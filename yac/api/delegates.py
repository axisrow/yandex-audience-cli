"""Ресурс «Представители» (delegates) — 3 эндпоинта."""

from __future__ import annotations

from typing import Any, Optional

from ..registry import GROUP_DELEGATES
from ..base import Resource


class Delegates(Resource):
    group = GROUP_DELEGATES

    def list(self, *, pretty: bool = False) -> Any:
        return self._call("list", pretty=pretty)

    def add(
        self,
        user_login: str,
        *,
        perm: Optional[str] = None,
        comment: Optional[str] = None,
        pretty: bool = False,
    ) -> Any:
        delegate: dict = {"user_login": user_login}
        if perm is not None:
            delegate["perm"] = perm
        if comment is not None:
            delegate["comment"] = comment
        return self._call("add", json={"delegate": delegate}, pretty=pretty)

    def remove(self, user_login: str, *, pretty: bool = False) -> Any:
        return self._call("remove", params={"user_login": user_login}, pretty=pretty)
