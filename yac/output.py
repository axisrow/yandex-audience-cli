"""Рендер результатов: JSON (по умолчанию) или таблица."""

from __future__ import annotations

import json
from typing import Any

from rich.console import Console
from rich.table import Table

_console = Console()
_err_console = Console(stderr=True)


def print_json(data: Any) -> None:
    """Вывести данные как отформатированный JSON (UTF-8, без эскейпа)."""
    _console.print_json(json.dumps(data, ensure_ascii=False, default=str))


def print_table(rows: list, *, title: str | None = None) -> None:
    """Вывести список словарей таблицей. При несовместимых данных — JSON."""
    if not isinstance(rows, list) or not rows or not all(isinstance(r, dict) for r in rows):
        print_json(rows)
        return

    columns: list = []
    for row in rows:
        for key in row:
            if key not in columns:
                columns.append(key)

    table = Table(title=title, show_lines=False)
    for col in columns:
        table.add_column(str(col))
    for row in rows:
        table.add_row(*[_fmt(row.get(col)) for col in columns])
    _console.print(table)


def print_error(message: str) -> None:
    _err_console.print(f"[bold red]Ошибка:[/] {message}")


def _fmt(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, default=str)
    return str(value)
