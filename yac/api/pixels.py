"""Ресурс «Пиксели» — 5 эндпоинтов."""

from __future__ import annotations

from typing import Any

from ..registry import GROUP_PIXELS
from ..base import Resource


class Pixels(Resource):
    group = GROUP_PIXELS

    def list(self, *, pretty: bool = False) -> Any:
        return self._call("list", pretty=pretty)

    def create(self, name: str, *, pretty: bool = False) -> Any:
        return self._call("create", json={"pixel": {"name": name}}, pretty=pretty)

    def update(self, pixel_id: int, name: str, *, pretty: bool = False) -> Any:
        return self._call(
            "update", id=pixel_id, json={"pixel": {"name": name}}, pretty=pretty
        )

    def delete(self, pixel_id: int, *, pretty: bool = False) -> Any:
        return self._call("delete", id=pixel_id, pretty=pretty)

    def undelete(self, pixel_id: int, *, pretty: bool = False) -> Any:
        return self._call("undelete", id=pixel_id, pretty=pretty)
