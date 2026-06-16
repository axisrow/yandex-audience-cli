"""Структурная гарантия 100% покрытия API.

Реестр (registry.ENDPOINTS) — единый источник правды. Эти тесты падают,
если хоть один эндпоинт не имеет:
  * метода в соответствующем классе ресурса, ИЛИ
  * команды в соответствующем под-приложении CLI.

Так покрытие API проверяется машинно, а не на глаз.
"""

from __future__ import annotations

import pytest
import typer

from yac import registry
from yac import app as root_app
from yac.api.accounts import Accounts
from yac.api.delegates import Delegates
from yac.api.grants import Grants
from yac.api.pixels import Pixels
from yac.api.segments import Segments

pytestmark = pytest.mark.unit

EXPECTED_PER_GROUP = {
    "segments": 16,
    "grants": 3,
    "pixels": 5,
    "accounts": 1,
    "delegates": 3,
}
EXPECTED_TOTAL = sum(EXPECTED_PER_GROUP.values())  # 28

RESOURCE_BY_GROUP = {
    "segments": Segments,
    "grants": Grants,
    "pixels": Pixels,
    "accounts": Accounts,
    "delegates": Delegates,
}


def test_total_endpoint_count():
    assert len(registry.ENDPOINTS) == EXPECTED_TOTAL


def test_counts_per_group():
    grouped = registry.by_group()
    assert {g: len(eps) for g, eps in grouped.items()} == EXPECTED_PER_GROUP


def test_no_duplicate_endpoints():
    keys = [(ep.group, ep.op) for ep in registry.ENDPOINTS]
    assert len(keys) == len(set(keys)), "Дубликаты (group, op) в реестре"


def test_methods_and_paths_well_formed():
    for ep in registry.ENDPOINTS:
        assert ep.method in {"GET", "POST", "PUT", "DELETE"}, ep
        assert ep.path and not ep.path.startswith("/"), ep
        # Плейсхолдеры пути объявлены в path_params.
        for name in ep.path_params:
            assert "{" + name + "}" in ep.path, ep


@pytest.mark.parametrize("ep", registry.ENDPOINTS, ids=lambda e: f"{e.group}.{e.op}")
def test_every_endpoint_has_resource_method(ep):
    resource_cls = RESOURCE_BY_GROUP[ep.group]
    assert callable(
        getattr(resource_cls, ep.op, None)
    ), f"Нет метода ресурса {resource_cls.__name__}.{ep.op}"


def _group_command_names(group: str) -> set:
    """Имена команд группы так, как их видит пользователь в корневом app."""
    root = typer.main.get_command(root_app)
    sub = root.commands[group]
    return set(sub.commands.keys())


def _op_to_command(op: str) -> str:
    """op в реестре использует _, команды CLI — дефисы; list -> list."""
    return op.replace("_", "-")


@pytest.mark.parametrize("ep", registry.ENDPOINTS, ids=lambda e: f"{e.group}.{e.op}")
def test_every_endpoint_has_cli_command(ep):
    commands = _group_command_names(ep.group)
    expected = _op_to_command(ep.op)
    assert expected in commands, (
        f"Нет команды CLI '{ep.group} {expected}' для эндпоинта {ep.group}.{ep.op}. "
        f"Доступные: {sorted(commands)}"
    )


def test_all_groups_registered_in_main_app():
    root = typer.main.get_command(root_app)
    assert set(registry.GROUPS).issubset(set(root.commands.keys()))
