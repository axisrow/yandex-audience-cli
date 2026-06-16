"""Стражи дерева-реестра: «дерево не врёт».

Реестр — это дерево ``yac/registry/<group>/<op>.py`` (файл на эндпоинт), а
``registry.ENDPOINTS`` собирается из него автозагрузкой. Эти тесты машинно
гарантируют инвариант раскладки: имя файла = ``op``, каталог = ``group``, у
каждого модуля есть ровно один ``Endpoint``, и число файлов = число эндпоинтов.
Так дерево не сможет молча рассинхронизироваться с полями ``Endpoint``.
"""

from __future__ import annotations

import pytest

from yac import registry
from yac.registry._core import ENDPOINT_ATTR, iter_endpoint_modules

# Обход дерева берём из прода (iter_endpoint_modules) — так страж проверяет
# инвариант поверх той же машины, что грузит ENDPOINTS, и конвенция обхода
# («файлы на _ — не эндпоинты») живёт в одном месте.
_TREE_MODULES = list(iter_endpoint_modules(registry.__name__))
_IDS = [f"{g}/{name}" for g, name, _ in _TREE_MODULES]


@pytest.mark.parametrize("group,mod_name,module", _TREE_MODULES, ids=_IDS)
def test_every_module_declares_endpoint(group, mod_name, module):
    ep = getattr(module, ENDPOINT_ATTR, None)
    assert isinstance(
        ep, registry.Endpoint
    ), f"{module.__name__} должен объявлять {ENDPOINT_ATTR}: Endpoint"


@pytest.mark.parametrize("group,mod_name,module", _TREE_MODULES, ids=_IDS)
def test_each_module_filename_matches_op(group, mod_name, module):
    ep = getattr(module, ENDPOINT_ATTR)
    assert (
        mod_name == ep.op
    ), f"Имя файла '{mod_name}.py' != op '{ep.op}' в {module.__name__}"


@pytest.mark.parametrize("group,mod_name,module", _TREE_MODULES, ids=_IDS)
def test_each_module_dir_matches_group(group, mod_name, module):
    ep = getattr(module, ENDPOINT_ATTR)
    assert (
        group == ep.group
    ), f"Каталог '{group}/' != group '{ep.group}' в {module.__name__}"


def test_file_count_equals_endpoint_count():
    assert len(_TREE_MODULES) == len(
        registry.ENDPOINTS
    ), "Число файлов-эндпоинтов в дереве должно совпадать с len(ENDPOINTS)"
