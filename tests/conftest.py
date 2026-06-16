"""Общие фикстуры для всех уровней тестовой пирамиды.

Здесь два рода фикстур:

* ``client`` — готовый :class:`yac.client.Client` для интеграционных тестов
  ресурсов (respx подменяет сокет; base-url по умолчанию — боевой).
* ``stub_server`` — НАСТОЯЩИЙ локальный HTTP-сервер на stdlib ``http.server``
  для e2e: тесты гоняют реальный ``yac`` через ``--base-url`` на него, без единого
  мока. Сервер программируется из теста (что отдать на какой путь) и фиксирует
  пришедшие запросы для проверок (заголовок ``Authorization``, путь, query).
"""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional, Tuple

import pytest

from yac.client import Client
from yac.config import Config

# --- opt-in на e2e: флаг --run-e2e (идиоматичный паттерн pytest) --------------
#
# e2e либо поднимает локальный сервер, либо бьёт в боевой API — в дефолтном
# прогоне не нужен. Вместо фильтра по маркеру в addopts (который ломал бы
# `pytest tests/e2e`) помечаем e2e как skip, пока не передан --run-e2e. Тогда
# и `pytest`, и `pytest tests/e2e` ведут себя ожидаемо: e2e идёт только по флагу.


def pytest_addoption(parser):
    parser.addoption(
        "--run-e2e",
        action="store_true",
        default=False,
        help="Запускать e2e-тесты (локальный stub-сервер и/или боевой API).",
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-e2e"):
        return
    skip_e2e = pytest.mark.skip(reason="e2e off: передайте --run-e2e")
    for item in items:
        if "e2e" in item.keywords:
            item.add_marker(skip_e2e)


@pytest.fixture
def client():
    """Клиент с боевым base-url по умолчанию; закрывается после теста.

    Сетевых обращений не делает сам по себе — интеграционные тесты подменяют
    транспорт через ``@respx.mock``. Вынесено из ``test_resources.py``, где
    фикстура с тем же именем дублировалась.
    """
    c = Client(Config(token="T"))
    yield c
    c.close()


# --- e2e: настоящий локальный stub-сервер Audience API -----------------------


@dataclass
class _RecordedRequest:
    """Снимок пришедшего на стаб запроса — для ассертов в тесте."""

    method: str
    path: str  # без query
    query: str  # сырая query-строка
    authorization: Optional[str]


@dataclass
class StubServer:
    """Управляемый локальный сервер: задаём ответы, читаем запросы.

    ``url`` подставляется в ``yac --base-url``. ``respond(method, path, ...)``
    регистрирует ответ для конкретного ``/v1/management/<path>``. Всё пришедшее
    копится в ``requests`` для проверок.
    """

    url: str
    _routes: Dict[Tuple[str, str], Tuple[int, Any]] = field(default_factory=dict)
    requests: List[_RecordedRequest] = field(default_factory=list)

    def respond(
        self, method: str, path: str, status: int = 200, json_body: Any = None
    ) -> None:
        """Зарегистрировать ответ на ``METHOD /v1/management/<path>``."""
        self._routes[(method.upper(), "/v1/management/" + path.lstrip("/"))] = (
            status,
            json_body,
        )

    def _lookup(self, method: str, path: str) -> Optional[Tuple[int, Any]]:
        return self._routes.get((method.upper(), path))


def _make_handler(stub: StubServer):
    class _Handler(BaseHTTPRequestHandler):
        # Глушим логи сервера в stderr на каждый запрос.
        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
            pass

        def _read_body(self) -> None:
            # Вычитать тело, чтобы клиент не подвис на незакрытом сокете.
            length = int(self.headers.get("Content-Length") or 0)
            if length:
                self.rfile.read(length)

        def _dispatch(self, method: str) -> None:
            path, _, query = self.path.partition("?")
            stub.requests.append(
                _RecordedRequest(
                    method=method,
                    path=path,
                    query=query,
                    authorization=self.headers.get("Authorization"),
                )
            )
            match = stub._lookup(method, path)
            if match is None:
                # Неизвестный путь — 404 в формате ошибки Audience API,
                # чтобы e2e проверял и ветку разбора ошибок.
                self._write(404, {"errors": [{"text": f"unknown path {path}"}]})
                return
            status, body = match
            self._write(status, body)

        def _write(self, status: int, body: Any) -> None:
            payload = b"" if body is None else json.dumps(body).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            if payload:
                self.wfile.write(payload)

        def do_GET(self) -> None:  # noqa: N802
            self._dispatch("GET")

        def do_POST(self) -> None:  # noqa: N802
            self._read_body()
            self._dispatch("POST")

        def do_PUT(self) -> None:  # noqa: N802
            self._read_body()
            self._dispatch("PUT")

        def do_DELETE(self) -> None:  # noqa: N802
            self._dispatch("DELETE")

    return _Handler


@pytest.fixture
def stub_server():
    """Поднять реальный HTTP-сервер на 127.0.0.1:<свободный порт> в фоне.

    Отдаёт :class:`StubServer`; тест задаёт ответы через ``respond`` и читает
    ``requests``. Останавливается в teardown.
    """
    # Биндим сокет (порт известен из server_address), собираем stub с готовым
    # url, затем подключаем обработчик — без временного пустого url.
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), BaseHTTPRequestHandler)
    host, port = httpd.server_address[0], httpd.server_address[1]
    stub = StubServer(url=f"http://{host}:{port}")
    httpd.RequestHandlerClass = _make_handler(stub)

    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield stub
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=5)
