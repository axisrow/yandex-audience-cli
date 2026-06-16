"""Команды группы ``accounts``."""

from __future__ import annotations

import typer

from ..api.accounts import Accounts
from ..render import render
from ..context import get_state, handle_errors

app = typer.Typer(
    help="Аккаунты, где вы — представитель (1 эндпоинт).", no_args_is_help=True
)


@app.command("list")
@handle_errors
def list_(ctx: typer.Context) -> None:
    """Список аккаунтов."""
    render(ctx, Accounts(get_state(ctx).client()).list(pretty=get_state(ctx).pretty))
