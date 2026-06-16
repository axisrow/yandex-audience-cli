"""Общий контекст для команд CLI: глобальные опции и фабрика ресурсов.

Хранит токен/base-url/pretty в ``ctx.obj`` (Typer/Click) и по требованию
создаёт :class:`Client` и нужный ресурс. Здесь же — единый декоратор
обработки ошибок API, чтобы команды оставались тонкими.
"""

from __future__ import annotations

import functools
from dataclasses import dataclass
from typing import Any, Callable, Optional

import typer

from .config import ConfigError, load_config
from .client import APIError, Client
from .output import print_error

from .api.accounts import Accounts
from .api.delegates import Delegates
from .api.grants import Grants
from .api.pixels import Pixels
from .api.segments import Segments


@dataclass
class AppState:
    """Глобальные опции, заполняются в главном callback."""

    token: Optional[str] = None
    base_url: Optional[str] = None
    pretty: bool = False
    output: str = "json"  # json | table

    def client(self) -> Client:
        config = load_config(token=self.token, base_url=self.base_url)
        return Client(config)


def get_state(ctx: typer.Context) -> AppState:
    if ctx.obj is None:
        ctx.obj = AppState()
    return ctx.obj


def handle_errors(func: Callable) -> Callable:
    """Превратить ConfigError/APIError в аккуратный exit(1) вместо трейсбека."""

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except (APIError, ConfigError) as exc:
            print_error(str(exc))
            raise typer.Exit(code=1)

    return wrapper


# Карта группа -> класс ресурса (используется командами).
RESOURCE_CLASSES = {
    "segments": Segments,
    "grants": Grants,
    "pixels": Pixels,
    "accounts": Accounts,
    "delegates": Delegates,
}
