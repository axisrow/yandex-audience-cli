"""Команды группы ``grants`` (разрешения на сегмент)."""

from __future__ import annotations

from typing import Optional

import typer

from ..api.grants import Grants
from ..render import render
from ..context import get_state, handle_errors

app = typer.Typer(
    help="Управление доступом к сегментам (3 эндпоинта).", no_args_is_help=True
)


def _grants(ctx: typer.Context) -> Grants:
    return Grants(get_state(ctx).client())


@app.command("list")
@handle_errors
def list_(ctx: typer.Context, segment_id: int = typer.Argument(...)) -> None:
    """Список разрешений сегмента."""
    render(ctx, _grants(ctx).list(segment_id, pretty=get_state(ctx).pretty))


@app.command("add")
@handle_errors
def add(
    ctx: typer.Context,
    segment_id: int = typer.Argument(...),
    user_login: str = typer.Option(
        ..., "--user-login", help="Логин получателя доступа."
    ),
    permission: Optional[str] = typer.Option(
        None, "--permission", help="edit | view (опц.)."
    ),
    comment: Optional[str] = typer.Option(None, "--comment"),
) -> None:
    """Создать разрешение на сегмент."""
    render(
        ctx,
        _grants(ctx).add(
            segment_id,
            user_login,
            permission=permission,
            comment=comment,
            pretty=get_state(ctx).pretty,
        ),
    )


@app.command("remove")
@handle_errors
def remove(
    ctx: typer.Context,
    segment_id: int = typer.Argument(...),
    user_login: str = typer.Option(..., "--user-login"),
) -> None:
    """Удалить разрешение на сегмент."""
    render(
        ctx, _grants(ctx).remove(segment_id, user_login, pretty=get_state(ctx).pretty)
    )
