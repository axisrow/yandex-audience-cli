"""Ресурс «Аккаунты» — 1 эндпоинт."""

from __future__ import annotations

from typing import Any

from ..registry import GROUP_ACCOUNTS
from ..base import Resource


class Accounts(Resource):
    group = GROUP_ACCOUNTS

    def list(self, *, pretty: bool = False) -> Any:
        return self._call("list", pretty=pretty)
