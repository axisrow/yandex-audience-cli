"""Команды группы ``pixels``."""

from __future__ import annotations

import typer

from ..api.pixels import Pixels
from ..render import render
from ..context import get_state, handle_errors

app = typer.Typer(help="Управление пикселями (5 эндпоинтов).", no_args_is_help=True)


def _pixels(ctx: typer.Context) -> Pixels:
    return Pixels(get_state(ctx).client())


@app.command("list")
@handle_errors
def list_(ctx: typer.Context) -> None:
    """Список пикселей."""
    render(ctx, _pixels(ctx).list(pretty=get_state(ctx).pretty))


@app.command("create")
@handle_errors
def create(ctx: typer.Context, name: str = typer.Option(..., "--name")) -> None:
    """Создать пиксель."""
    render(ctx, _pixels(ctx).create(name, pretty=get_state(ctx).pretty))


@app.command("update")
@handle_errors
def update(
    ctx: typer.Context,
    pixel_id: int = typer.Argument(...),
    name: str = typer.Option(..., "--name"),
) -> None:
    """Изменить пиксель."""
    render(ctx, _pixels(ctx).update(pixel_id, name, pretty=get_state(ctx).pretty))


@app.command("delete")
@handle_errors
def delete(ctx: typer.Context, pixel_id: int = typer.Argument(...)) -> None:
    """Удалить пиксель."""
    render(ctx, _pixels(ctx).delete(pixel_id, pretty=get_state(ctx).pretty))


@app.command("undelete")
@handle_errors
def undelete(ctx: typer.Context, pixel_id: int = typer.Argument(...)) -> None:
    """Восстановить удалённый пиксель."""
    render(ctx, _pixels(ctx).undelete(pixel_id, pretty=get_state(ctx).pretty))
