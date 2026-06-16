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

from typing import Any, Mapping, Optional

import httpx

from .config import Config

DEFAULT_TIMEOUT = 30.0


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

        try:
            response = self._http.request(
                method.upper(),
                path.lstrip("/"),
                params=query or None,
                json=json,
                files=files,
            )
        except httpx.HTTPError as exc:  # сетевые/таймаут-ошибки
            raise APIError(f"Сетевая ошибка: {exc}") from exc

        return self._handle(response)

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
