"""yac — CLI для Yandex Audience API.

Точка входа и сборка корневого Typer-приложения. Зеркалит структуру
HTTP API Яндекс.Аудиторий «1 в 1»:
версия (v1) → пространство (management) → 5 ресурсных групп
(segments, grants, pixels, accounts, delegates).

Единый источник правды по эндпоинтам — registry.py.
Запуск: ``yac ...`` (консольный скрипт) или ``python -m yac ...``.
"""

from __future__ import annotations

from typing import Optional

import typer

from .config import ENV_BASE_URL, ENV_TOKEN
from .context import AppState, get_state

from .commands import segments as segments_cli
from .commands import grants as grants_cli
from .commands import pixels as pixels_cli
from .commands import accounts as accounts_cli
from .commands import delegates as delegates_cli

__version__ = "0.1.0"

app = typer.Typer(
    name="yac",
    help="CLI для Yandex Audience API — структура API 1:1 (5 групп, 28 эндпоинтов).",
    no_args_is_help=True,
    add_completion=True,
)

# Под-приложения = ресурсные группы API.
app.add_typer(segments_cli.app, name="segments")
app.add_typer(grants_cli.app, name="grants")
app.add_typer(pixels_cli.app, name="pixels")
app.add_typer(accounts_cli.app, name="accounts")
app.add_typer(delegates_cli.app, name="delegates")


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"yandex-audience-cli {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    ctx: typer.Context,
    token: Optional[str] = typer.Option(
        None, "--token", envvar=ENV_TOKEN, help="OAuth-токен Яндекса."
    ),
    base_url: Optional[str] = typer.Option(
        None,
        "--base-url",
        envvar=ENV_BASE_URL,
        help="Базовый URL API (для тестов/прокси).",
    ),
    output: str = typer.Option(
        "json", "--output", "-o", help="Формат вывода: json | table."
    ),
    pretty: bool = typer.Option(
        False, "--pretty", help="Запрашивать pretty-ответ у API."
    ),
    _version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Версия CLI.",
    ),
) -> None:
    """Общие опции применяются ко всем командам."""
    state = get_state(ctx)
    state.token = token
    state.base_url = base_url
    state.output = output
    state.pretty = pretty


__all__ = ["app", "AppState", "__version__"]


if __name__ == "__main__":
    app()
