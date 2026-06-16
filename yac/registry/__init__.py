"""Реестр всех эндпоинтов Yandex Audience API — дерево «файл на эндпоинт».

ИСТОЧНИК ПРАВДЫ — само дерево: ``registry/<group>/<op>.py``, по файлу на каждый
эндпоинт (имя файла = ``op``, каталог = ``group``). ``ls registry/segments/``
показывает все эндпоинты группы. Список :data:`ENDPOINTS` собирается из дерева
автозагрузкой (см. :func:`yac.registry._core._load`), а инвариант «имя файла =
op, каталог = group» защищён тестом ``tests/test_registry_tree.py``.

Структура API (3 уровня): версия (v1) → пространство (management) → ресурс (5 групп).
Пути даны относительно ``.../v1/management``; плейсхолдеры — ``{id}``.

Этот модуль — фасад: он реэкспортирует публичный контракт реестра
(``Endpoint``, ``ENDPOINTS``, ``GROUPS``, ``GROUP_*``, ``get``, ``by_group``,
``render_path``), поэтому ``from . import registry`` / ``from ..registry import
GROUP_SEGMENTS`` в остальном коде работают без изменений.
"""

from __future__ import annotations

from typing import Dict, List

from . import _core
from ._core import (
    GROUP_ACCOUNTS,
    GROUP_DELEGATES,
    GROUP_GRANTS,
    GROUP_PIXELS,
    GROUP_SEGMENTS,
    GROUPS,
    Endpoint,
    render_path,
)

#: Полный реестр: 5 групп, 28 эндпоинтов. Собирается из дерева при импорте.
ENDPOINTS: List[Endpoint] = _core._load(__name__)


def get(group: str, op: str) -> Endpoint:
    """Найти эндпоинт по группе и имени операции."""
    return _core.get(ENDPOINTS, group, op)


def by_group() -> Dict[str, List[Endpoint]]:
    """Сгруппировать эндпоинты по ресурсам, сохраняя порядок :data:`GROUPS`."""
    return _core.by_group(ENDPOINTS, GROUPS)


__all__ = [
    "Endpoint",
    "ENDPOINTS",
    "GROUPS",
    "GROUP_SEGMENTS",
    "GROUP_GRANTS",
    "GROUP_PIXELS",
    "GROUP_ACCOUNTS",
    "GROUP_DELEGATES",
    "get",
    "by_group",
    "render_path",
]
