"""Смоук: CLI собирается и раскрывается без сети.

Дымовой уровень пирамиды — проверяем, что приложение импортируется, все группы
на месте, справка/версия работают и отсутствие токена даёт чистую ошибку (без
traceback). Сети здесь нет: ни один тест не делает HTTP-запрос (негативный тест
падает на резолве токена ещё до клиента).
"""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

import yac
from yac import app, registry

pytestmark = pytest.mark.smoke

runner = CliRunner()


def test_help_lists_all_groups():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for group in registry.GROUPS:
        assert group in result.stdout


def test_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "yandex-audience-cli" in result.stdout


def test_version_string_matches_package():
    # Смоук версии: напечатанное совпадает с yac.__version__.
    result = runner.invoke(app, ["--version"])
    assert yac.__version__ in result.stdout


def test_missing_token_is_clean_error():
    # Без токена и без env — аккуратная ошибка, без трейсбека.
    result = runner.invoke(app, ["accounts", "list"], env={"YANDEX_AUDIENCE_TOKEN": ""})
    assert result.exit_code == 1
    assert "Traceback" not in result.stdout
    assert "токен" in result.stdout.lower() or "токен" in (result.stderr or "").lower()


def test_segments_help_lists_all_commands():
    result = runner.invoke(app, ["segments", "--help"])
    assert result.exit_code == 0
    for cmd in (
        "list",
        "create-pixel",
        "create-lookalike",
        "create-metrika",
        "create-appmetrica",
        "create-geo",
        "create-geo-polygon",
        "upload-file",
        "upload-csv-file",
        "update-geo-points",
        "modify-data",
        "confirm",
        "confirm-client-id",
        "update",
        "delete",
        "reprocess",
    ):
        assert cmd in result.stdout
    # get удалён: getSegment в Audience API не существует.
    assert " get " not in result.stdout


@pytest.mark.parametrize("group", registry.GROUPS)
def test_each_group_help_smoke(group):
    # Каждое под-приложение собралось и раскрывает справку без сети.
    result = runner.invoke(app, [group, "--help"])
    assert result.exit_code == 0, f"{group} --help упал: {result.stdout}"
