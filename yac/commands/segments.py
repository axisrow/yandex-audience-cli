"""Команды группы ``segments`` (resource verb)."""

from __future__ import annotations

from typing import Optional

import typer

from ..api.segments import Segments
from ..inputs import parse_data
from ..render import render
from ..context import get_state, handle_errors

app = typer.Typer(help="Управление сегментами (16 эндпоинтов).", no_args_is_help=True)

DATA_HELP = "JSON-тело сегмента: строка, @файл или - (stdin)."


def _segments(ctx: typer.Context) -> Segments:
    state = get_state(ctx)
    return Segments(state.client())


@app.command("list")
@handle_errors
def list_(
    ctx: typer.Context,
    pixel: Optional[int] = typer.Option(None, help="Фильтр по id пикселя."),
    limit: Optional[int] = typer.Option(
        None, help="Сколько сегментов вернуть (по умолчанию 10000)."
    ),
    offset: Optional[int] = typer.Option(None, help="Смещение пагинации."),
) -> None:
    """Список сегментов."""
    render(
        ctx,
        _segments(ctx).list(
            pixel=pixel, limit=limit, offset=offset, pretty=get_state(ctx).pretty
        ),
    )


@app.command("create-pixel")
@handle_errors
def create_pixel(
    ctx: typer.Context, data: str = typer.Option(..., "--data", help=DATA_HELP)
) -> None:
    """Создать сегмент на основе пикселя."""
    render(
        ctx, _segments(ctx).create_pixel(parse_data(data), pretty=get_state(ctx).pretty)
    )


@app.command("create-lookalike")
@handle_errors
def create_lookalike(
    ctx: typer.Context, data: str = typer.Option(..., "--data", help=DATA_HELP)
) -> None:
    """Создать lookalike-сегмент."""
    render(
        ctx,
        _segments(ctx).create_lookalike(parse_data(data), pretty=get_state(ctx).pretty),
    )


@app.command("create-metrika")
@handle_errors
def create_metrika(
    ctx: typer.Context, data: str = typer.Option(..., "--data", help=DATA_HELP)
) -> None:
    """Создать сегмент из Яндекс.Метрики."""
    render(
        ctx,
        _segments(ctx).create_metrika(parse_data(data), pretty=get_state(ctx).pretty),
    )


@app.command("create-appmetrica")
@handle_errors
def create_appmetrica(
    ctx: typer.Context, data: str = typer.Option(..., "--data", help=DATA_HELP)
) -> None:
    """Создать сегмент из AppMetrica."""
    render(
        ctx,
        _segments(ctx).create_appmetrica(
            parse_data(data), pretty=get_state(ctx).pretty
        ),
    )


@app.command("create-geo")
@handle_errors
def create_geo(
    ctx: typer.Context, data: str = typer.Option(..., "--data", help=DATA_HELP)
) -> None:
    """Создать гео-сегмент (окружность)."""
    render(
        ctx, _segments(ctx).create_geo(parse_data(data), pretty=get_state(ctx).pretty)
    )


@app.command("create-geo-polygon")
@handle_errors
def create_geo_polygon(
    ctx: typer.Context, data: str = typer.Option(..., "--data", help=DATA_HELP)
) -> None:
    """Создать гео-сегмент (полигон)."""
    render(
        ctx,
        _segments(ctx).create_geo_polygon(
            parse_data(data), pretty=get_state(ctx).pretty
        ),
    )


@app.command("upload-file")
@handle_errors
def upload_file(
    ctx: typer.Context, file: str = typer.Argument(..., help="Путь к файлу данных.")
) -> None:
    """Загрузить файл данных (CRM/idfa_gaid/mac/client_id)."""
    render(ctx, _segments(ctx).upload_file(file, pretty=get_state(ctx).pretty))


@app.command("upload-csv-file")
@handle_errors
def upload_csv_file(
    ctx: typer.Context, file: str = typer.Argument(..., help="Путь к CSV-файлу.")
) -> None:
    """Загрузить CSV-файл данных."""
    render(ctx, _segments(ctx).upload_csv_file(file, pretty=get_state(ctx).pretty))


@app.command("update-geo-points")
@handle_errors
def update_geo_points(
    ctx: typer.Context,
    segment_id: int = typer.Argument(...),
    data: str = typer.Option(
        ..., "--data", help="JSON-массив точек: строка, @файл или - (stdin)."
    ),
) -> None:
    """Изменить координаты гео-сегмента (окружность)."""
    points = parse_data(data)
    render(
        ctx,
        _segments(ctx).update_geo_points(
            segment_id, points, pretty=get_state(ctx).pretty
        ),
    )


@app.command("modify-data")
@handle_errors
def modify_data(
    ctx: typer.Context,
    segment_id: int = typer.Argument(...),
    file: str = typer.Argument(..., help="Путь к файлу с обновлёнными данными."),
    modification_type: str = typer.Option(
        ..., "--modification-type", help="addition | subtraction | replace."
    ),
    check_size: Optional[bool] = typer.Option(
        None, "--check-size/--no-check-size", help="Проверять минимум 100 записей."
    ),
) -> None:
    """Изменить данные загруженного из файла сегмента."""
    render(
        ctx,
        _segments(ctx).modify_data(
            segment_id,
            file,
            modification_type,
            check_size=check_size,
            pretty=get_state(ctx).pretty,
        ),
    )


@app.command("confirm")
@handle_errors
def confirm(
    ctx: typer.Context,
    segment_id: int = typer.Argument(...),
    data: str = typer.Option(..., "--data", help=DATA_HELP),
    check_size: Optional[bool] = typer.Option(
        None,
        "--check-size/--no-check-size",
        help="Проверять минимум 100 записей (опц.).",
    ),
) -> None:
    """Сохранить/подтвердить загруженный сегмент."""
    render(
        ctx,
        _segments(ctx).confirm(
            segment_id,
            parse_data(data),
            check_size=check_size,
            pretty=get_state(ctx).pretty,
        ),
    )


@app.command("confirm-client-id")
@handle_errors
def confirm_client_id(
    ctx: typer.Context,
    segment_id: int = typer.Argument(...),
    data: str = typer.Option(..., "--data", help=DATA_HELP),
) -> None:
    """Сохранить сегмент из ClientId Метрики."""
    render(
        ctx,
        _segments(ctx).confirm_client_id(
            segment_id, parse_data(data), pretty=get_state(ctx).pretty
        ),
    )


@app.command("update")
@handle_errors
def update(
    ctx: typer.Context,
    segment_id: int = typer.Argument(...),
    data: str = typer.Option(..., "--data", help=DATA_HELP),
) -> None:
    """Изменить сегмент."""
    render(
        ctx,
        _segments(ctx).update(
            segment_id, parse_data(data), pretty=get_state(ctx).pretty
        ),
    )


@app.command("delete")
@handle_errors
def delete(ctx: typer.Context, segment_id: int = typer.Argument(...)) -> None:
    """Удалить сегмент."""
    render(ctx, _segments(ctx).delete(segment_id, pretty=get_state(ctx).pretty))


@app.command("reprocess")
@handle_errors
def reprocess(ctx: typer.Context, segment_id: int = typer.Argument(...)) -> None:
    """Переобработать (пересчитать) сегмент."""
    render(ctx, _segments(ctx).reprocess(segment_id, pretty=get_state(ctx).pretty))
