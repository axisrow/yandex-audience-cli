"""HTTP-клиент к Yandex Audience API поверх httpx.

Отвечает за единые правила транспорта:
- заголовок ``Authorization: OAuth <token>`` (именно OAuth, не Bearer);
- сборку URL относительно ``.../v1/management``;
- параметр ``pretty`` для форматированного ответа;
- загрузку файлов через ``multipart/form-data``;
- разбор ошибок API и отдельную обработку HTTP 429 (превышение квот).

Слой ресурсов (<group>_api.py) пользуется только методами этого класса
и не знает деталей транспорта.
"""

from __future__ import annotations

import sys
import time
from typing import Any, Mapping, Optional

import httpx

from .config import Config

DEFAULT_TIMEOUT = 30.0

#: Повторных попыток после HTTP 429 (итого попыток: RETRY_429_ATTEMPTS + 1).
RETRY_429_ATTEMPTS = 1
#: Пауза перед повтором, если API не отдал заголовок Retry-After.
RETRY_429_DEFAULT_WAIT = 60.0


def _sleep(seconds: float) -> None:
    """Точка подмены в тестах (реальный сон — time.sleep)."""
    time.sleep(seconds)


def _retry_wait(response: httpx.Response) -> float:
    """Пауза до повтора: Retry-After от API, иначе дефолт. Мусорный заголовок не роняет."""
    raw = response.headers.get("Retry-After")
    if raw:
        try:
            return max(float(raw), 0.0)
        except ValueError:
            pass
    return RETRY_429_DEFAULT_WAIT
    return RETRY_429_DEFAULT_WAIT


class APIError(RuntimeError):
    """Ошибка, вернувшаяся от API (или транспортная)."""

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        payload: Any = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


class RateLimitError(APIError):
    """HTTP 429 — превышены квоты запросов."""


class Client:
    """Тонкий клиент над httpx.Client с авторизацией Audience API."""

    def __init__(
        self,
        config: Config,
        *,
        timeout: float = DEFAULT_TIMEOUT,
        transport: Optional[httpx.BaseTransport] = None,
    ) -> None:
        self.config = config
        self._http = httpx.Client(
            base_url=config.management_url,
            headers={"Authorization": f"OAuth {config.token}"},
            timeout=timeout,
            transport=transport,
        )

    # -- контекстный менеджер ------------------------------------------------
    def __enter__(self) -> "Client":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def close(self) -> None:
        self._http.close()

    # -- основной примитив ---------------------------------------------------
    def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        json: Any = None,
        files: Optional[Mapping[str, Any]] = None,
        pretty: bool = False,
    ) -> Any:
        """Выполнить запрос и вернуть разобранный JSON (или None).

        ``path`` задаётся относительно пространства management,
        например ``"segments"`` или ``"segment/123/grants"``.
        """
        query = dict(params or {})
        if pretty:
            query["pretty"] = 1

        # HTTP 429 — не доменный отказ, а квотный голод: повтор безопасен (запрос
        # отклонён до обработки), поэтому ретраим с паузой Retry-After/60с —
        # иначе любой скрипт >10 записей/мин падает на 11-й. Пауза печатается в
        # stderr, чтобы ожидание не было молчаливым.
        response = self._send(method, path, query, json, files)
        for attempt in range(RETRY_429_ATTEMPTS):
            if response.status_code != 429:
                break
            wait = _retry_wait(response)
            print(
                f"HTTP 429: пауза {wait:g}с и повтор (осталось попыток: "
                f"{RETRY_429_ATTEMPTS - attempt})…",
                file=sys.stderr,
            )
            _sleep(wait)
            response = self._send(method, path, query, json, files)

        return self._handle(response)

    def _send(
        self,
        method: str,
        path: str,
        query: Mapping[str, Any],
        json: Any,
        files: Optional[Mapping[str, Any]],
    ) -> httpx.Response:
        try:
            return self._http.request(
                method.upper(),
                path.lstrip("/"),
                params=query or None,
                json=json,
                files=files,
            )
        except httpx.HTTPError as exc:  # сетевые/таймаут-ошибки
            raise APIError(f"Сетевая ошибка: {exc}") from exc

    # -- разбор ответа -------------------------------------------------------
    @staticmethod
    def _handle(response: httpx.Response) -> Any:
        if response.status_code == 429:
            raise RateLimitError(
                "Превышена квота запросов (HTTP 429). "
                "Лимиты: 30 req/s по IP, 5000 req/day по логину, "
                "запись 10/мин · 100/час · 500/день.",
                status_code=429,
                payload=_safe_json(response),
            )

        if response.is_success:
            if not response.content:
                return None
            return _safe_json(response)

        payload = _safe_json(response)
        message = _extract_error_message(payload) or response.text or "Ошибка API"
        raise APIError(
            f"HTTP {response.status_code}: {message}",
            status_code=response.status_code,
            payload=payload,
        )


def _safe_json(response: httpx.Response) -> Any:
    try:
        return response.json()
    except ValueError:
        return None


def _extract_error_message(payload: Any) -> Optional[str]:
    """Достать человекочитаемое сообщение из тела ошибки Audience API."""
    if not isinstance(payload, Mapping):
        return None
    # Возможные формы: {"errors": [{"text": ...}]} или {"message": ...}
    errors = payload.get("errors")
    if isinstance(errors, list) and errors:
        texts = [
            str(e.get("text") or e.get("message") or e)
            for e in errors
            if isinstance(e, Mapping)
        ]
        if texts:
            return "; ".join(texts)
    for key in ("message", "error", "text"):
        if payload.get(key):
            return str(payload[key])
    return None
