"""Команды группы ``delegates`` (представители)."""

from __future__ import annotations

from typing import Optional

import typer

from ..api.delegates import Delegates
from ..render import render
from ..context import get_state, handle_errors

app = typer.Typer(help="Управление представителями (3 эндпоинта).", no_args_is_help=True)


def _delegates(ctx: typer.Context) -> Delegates:
    return Delegates(get_state(ctx).client())


@app.command("list")
@handle_errors
def list_(ctx: typer.Context) -> None:
    """Список представителей."""
    render(ctx, _delegates(ctx).list(pretty=get_state(ctx).pretty))


@app.command("add")
@handle_errors
def add(
    ctx: typer.Context,
    user_login: str = typer.Option(..., "--user-login"),
    perm: Optional[str] = typer.Option(None, "--perm", help="view | edit (опц.)."),
    comment: Optional[str] = typer.Option(None, "--comment"),
) -> None:
    """Добавить представителя."""
    render(ctx, _delegates(ctx).add(user_login, perm=perm, comment=comment, pretty=get_state(ctx).pretty))


@app.command("remove")
@handle_errors
def remove(ctx: typer.Context, user_login: str = typer.Option(..., "--user-login")) -> None:
    """Удалить представителя."""
    render(ctx, _delegates(ctx).remove(user_login, pretty=get_state(ctx).pretty))
