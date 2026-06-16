"""Рендер результата команды с учётом глобальной опции --output."""

from __future__ import annotations

from typing import Any

import typer

from .output import print_json, print_table
from .context import get_state


def render(ctx: typer.Context, data: Any) -> None:
    """Вывести результат в выбранном формате (json по умолчанию)."""
    if data is None:
        print_json({"ok": True})
        return

    state = get_state(ctx)
    if state.output == "table":
        rows = _as_rows(data)
        if rows is not None:
            print_table(rows)
            return
    print_json(data)


def _as_rows(data: Any):
    """Привести типичные ответы API к списку словарей для таблицы."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        # Частые формы: {"segments": [...]}, {"pixels": [...]}, {"grants": [...]}
        for value in data.values():
            if isinstance(value, list):
                return value
        return [data]
    return None
