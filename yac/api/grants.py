"""Ресурс «Разрешения» (grants) — 3 эндпоинта."""

from __future__ import annotations

from typing import Any, Optional

from ..registry import GROUP_GRANTS
from ..base import Resource


class Grants(Resource):
    group = GROUP_GRANTS

    def list(self, segment_id: int, *, pretty: bool = False) -> Any:
        return self._call("list", id=segment_id, pretty=pretty)

    def add(
        self,
        segment_id: int,
        user_login: str,
        *,
        permission: Optional[str] = None,
        comment: Optional[str] = None,
        pretty: bool = False,
    ) -> Any:
        grant: dict = {"user_login": user_login}
        if permission is not None:
            grant["permission"] = permission
        if comment is not None:
            grant["comment"] = comment
        return self._call("add", id=segment_id, json={"grant": grant}, pretty=pretty)

    def remove(self, segment_id: int, user_login: str, *, pretty: bool = False) -> Any:
        return self._call(
            "remove", id=segment_id, params={"user_login": user_login}, pretty=pretty
        )
