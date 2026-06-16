"""Разбор JSON-тела для команд создания/изменения.

Принимает строку JSON напрямую или ``@путь`` для чтения из файла,
а также ``-`` для чтения из stdin.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import typer


def parse_data(value: str) -> Any:
    """Разобрать JSON из строки, ``@файла`` или ``-`` (stdin)."""
    raw: str
    if value == "-":
        raw = sys.stdin.read()
    elif value.startswith("@"):
        try:
            raw = Path(value[1:]).read_text(encoding="utf-8")
        except OSError as exc:
            raise typer.BadParameter(f"Не удалось прочитать файл: {exc}")
    else:
        raw = value

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise typer.BadParameter(f"Некорректный JSON: {exc}")
