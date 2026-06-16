"""Базовый класс ресурса.

Связывает группу ресурса с реестром эндпоинтов и предоставляет хелпер
:meth:`Resource._call`, который берёт описание эндпоинта из registry.py
(HTTP-метод и путь) — так слой ресурсов не дублирует строки путей.
"""

from __future__ import annotations

from typing import Any, Mapping, Optional

from . import registry
from .client import Client


class Resource:
    """Базовый ресурс. Подклассы задают ``group``."""

    group: str = ""

    def __init__(self, client: Client) -> None:
        self._client = client

    def _call(
        self,
        op: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        json: Any = None,
        files: Optional[Mapping[str, Any]] = None,
        pretty: bool = False,
        **path_params: object,
    ) -> Any:
        """Выполнить вызов эндпоинта ``self.group``/``op`` из реестра."""
        ep = registry.get(self.group, op)
        path = registry.render_path(ep, **path_params)
        return self._client.request(
            ep.method,
            path,
            params=params,
            json=json,
            files=files,
            pretty=pretty,
        )
