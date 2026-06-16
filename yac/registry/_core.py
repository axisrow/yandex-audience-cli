"""Ядро реестра: модель эндпоинта, группы и чистые функции.

Это «лист» графа импортов — модуль НЕ импортирует ни ``__init__`` пакета, ни
файлы-эндпоинты. Поэтому файлы ``registry/<group>/<op>.py`` могут безопасно
импортировать отсюда ``Endpoint`` и ``GROUP_*`` без риска цикла: к моменту
автосборки (``_load`` вызывается из ``__init__``) этот модуль уже полностью
инициализирован.

Сами эндпоинты живут не здесь, а по файлу на каждый в дереве
``registry/<group>/<op>.py`` (имя файла = ``op``, каталог = ``group``).
``ENDPOINTS`` собирается из дерева автозагрузкой в ``registry/__init__.py``.
"""

from __future__ import annotations

import importlib
import pkgutil
from dataclasses import dataclass, field
from types import ModuleType
from typing import Dict, Iterator, List, Tuple

# Группы ресурсов (= под-приложения CLI = пространства имён API).
GROUP_SEGMENTS = "segments"
GROUP_GRANTS = "grants"
GROUP_PIXELS = "pixels"
GROUP_ACCOUNTS = "accounts"
GROUP_DELEGATES = "delegates"

#: Имя переменной, в которой каждый файл-эндпоинт объявляет свой ``Endpoint``.
ENDPOINT_ATTR = "ENDPOINT"


@dataclass(frozen=True)
class Endpoint:
    """Описание одного эндпоинта API.

    :param group: ресурсная группа (segments/grants/pixels/...).
    :param op: имя операции — совпадает с методом ресурса и командой CLI.
    :param method: HTTP-метод.
    :param path: путь относительно ``.../v1/management`` с плейсхолдерами.
    :param summary: краткое назначение (для --help и документации).
    :param multipart: эндпоинт принимает файл (multipart/form-data).
    :param unverified: путь требует сверки на живом API (см. план).
    """

    group: str
    op: str
    method: str
    path: str
    summary: str
    multipart: bool = False
    unverified: bool = False
    path_params: Tuple[str, ...] = field(default_factory=tuple)


#: Порядок групп для отображения/итерации (фиксирован ЯВНО, не из ФС).
GROUPS: Tuple[str, ...] = (
    GROUP_SEGMENTS,
    GROUP_GRANTS,
    GROUP_PIXELS,
    GROUP_ACCOUNTS,
    GROUP_DELEGATES,
)


def iter_endpoint_modules(pkg_name: str) -> Iterator[Tuple[str, str, ModuleType]]:
    """Обойти дерево ``registry/<group>/<op>.py``, отдавая (group, op, module).

    Единственное место, где закодирован обход дерева и конвенция «файлы на
    ``_`` — не эндпоинты». На этом строятся и :func:`_load` (прод), и
    тест-страж — чтобы правила обхода не разъехались по двум копиям.

    Группы перебираются в порядке :data:`GROUPS` (явный, не из файловой
    системы). Внутри группы модули сортируются по имени (``sorted``), т.к.
    порядок обхода файловой системы не гарантирован — это влияет только на
    косметику вывода (--help/листинги), логика от него не зависит.
    """
    for group in GROUPS:
        group_pkg = importlib.import_module(f"{pkg_name}.{group}")
        mod_names = sorted(
            info.name
            for info in pkgutil.iter_modules(group_pkg.__path__)
            if not info.name.startswith("_")
        )
        for mod_name in mod_names:
            module = importlib.import_module(f"{pkg_name}.{group}.{mod_name}")
            yield group, mod_name, module


def _load(pkg_name: str) -> List[Endpoint]:
    """Собрать ``ENDPOINTS`` обходом дерева (см. :func:`iter_endpoint_modules`).

    Падает ГРОМКО при импорте, если модуль не объявляет :data:`ENDPOINT_ATTR`,
    объявляет не ``Endpoint``, или возникает дубль ``(group, op)`` — потерять
    эндпоинт молча хуже, чем уронить импорт.
    """
    endpoints: List[Endpoint] = []
    seen: set[Tuple[str, str]] = set()

    for _group, _mod_name, module in iter_endpoint_modules(pkg_name):
        ep = getattr(module, ENDPOINT_ATTR, None)
        if ep is None:
            raise RuntimeError(f"Модуль {module.__name__} не объявляет {ENDPOINT_ATTR}")
        if not isinstance(ep, Endpoint):
            raise TypeError(
                f"{module.__name__}.{ENDPOINT_ATTR} не Endpoint: {type(ep)!r}"
            )
        key = (ep.group, ep.op)
        if key in seen:
            raise ValueError(f"Дубликат эндпоинта в дереве: {key}")
        seen.add(key)
        endpoints.append(ep)
    return endpoints


def by_group(
    endpoints: List[Endpoint], groups: Tuple[str, ...]
) -> Dict[str, List[Endpoint]]:
    """Сгруппировать эндпоинты по ресурсам, сохраняя порядок ``groups``."""
    result: Dict[str, List[Endpoint]] = {g: [] for g in groups}
    for ep in endpoints:
        result.setdefault(ep.group, []).append(ep)
    return result


def get(endpoints: List[Endpoint], group: str, op: str) -> Endpoint:
    """Найти эндпоинт по группе и имени операции."""
    for ep in endpoints:
        if ep.group == group and ep.op == op:
            return ep
    raise KeyError(f"Эндпоинт не найден: {group}.{op}")


def render_path(ep: Endpoint, **params: object) -> str:
    """Подставить значения плейсхолдеров пути (например id)."""
    path = ep.path
    for name in ep.path_params:
        if name not in params:
            raise KeyError(f"Не передан параметр пути '{name}' для {ep.group}.{ep.op}")
        path = path.replace("{" + name + "}", str(params[name]))
    return path
