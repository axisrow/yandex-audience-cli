"""Конфигурация клиента: токен, базовый URL, версия API.

Источники токена (по приоритету):
1. явно переданный аргумент ``token``;
2. переменная окружения ``YANDEX_AUDIENCE_TOKEN``;
3. файл ``~/.config/yandex-audience-cli/token`` (одна строка).

Базовый URL и версия зафиксированы по факту исследования API:
у Audience API существует только версия ``v1`` и единственное
пространство имён ``management`` (см. registry.py).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

#: Базовый адрес API (без версии). Подтверждено: api-audience.yandex.ru.
DEFAULT_BASE_URL = "https://api-audience.yandex.ru"

#: Единственная существующая версия API.
DEFAULT_API_VERSION = "v1"

ENV_TOKEN = "YANDEX_AUDIENCE_TOKEN"
ENV_BASE_URL = "YANDEX_AUDIENCE_BASE_URL"

#: Путь к файлу с токеном по умолчанию.
TOKEN_FILE = Path.home() / ".config" / "yandex-audience-cli" / "token"


class ConfigError(RuntimeError):
    """Ошибка конфигурации (например, отсутствует токен)."""


def _read_token_file() -> Optional[str]:
    try:
        text = TOKEN_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return text or None


@dataclass(frozen=True)
class Config:
    """Неизменяемая конфигурация клиента."""

    token: str
    base_url: str = DEFAULT_BASE_URL
    api_version: str = DEFAULT_API_VERSION

    @property
    def management_url(self) -> str:
        """Полный префикс пространства management: ``.../v1/management``."""
        return f"{self.base_url.rstrip('/')}/{self.api_version}/management"


def resolve_token(token: Optional[str] = None) -> str:
    """Найти OAuth-токен по приоритету источников или поднять ConfigError."""
    candidate = (
        token
        or os.environ.get(ENV_TOKEN)
        or _read_token_file()
    )
    if not candidate:
        raise ConfigError(
            "OAuth-токен не найден. Передайте --token, задайте переменную "
            f"{ENV_TOKEN} или запишите токен в {TOKEN_FILE}."
        )
    return candidate.strip()


def load_config(
    token: Optional[str] = None,
    base_url: Optional[str] = None,
    api_version: Optional[str] = None,
) -> Config:
    """Собрать :class:`Config` из аргументов и окружения."""
    return Config(
        token=resolve_token(token),
        base_url=base_url or os.environ.get(ENV_BASE_URL) or DEFAULT_BASE_URL,
        api_version=api_version or DEFAULT_API_VERSION,
    )
