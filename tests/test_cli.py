"""Тесты CLI: справка, версия, прохождение команды через мок-API."""

from __future__ import annotations

import httpx
import respx
from typer.testing import CliRunner

from yac import app

runner = CliRunner()
BASE = "https://api-audience.yandex.ru/v1/management"


def test_help_lists_all_groups():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for group in ("segments", "grants", "pixels", "accounts", "delegates"):
        assert group in result.stdout


def test_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "yandex-audience-cli" in result.stdout


def test_missing_token_is_clean_error():
    # Без токена и без env — аккуратная ошибка, без трейсбека.
    result = runner.invoke(app, ["accounts", "list"], env={"YANDEX_AUDIENCE_TOKEN": ""})
    assert result.exit_code == 1
    assert "токен" in result.stdout.lower() or "токен" in (result.stderr or "").lower()


@respx.mock
def test_segments_list_command():
    respx.get(f"{BASE}/segments").mock(
        return_value=httpx.Response(200, json={"segments": [{"id": 1, "name": "A"}]})
    )
    result = runner.invoke(app, ["--token", "T", "segments", "list"])
    assert result.exit_code == 0
    assert "A" in result.stdout


@respx.mock
def test_pixels_create_command():
    route = respx.post(f"{BASE}/pixels").mock(
        return_value=httpx.Response(200, json={"pixel": {"id": 9, "name": "p"}})
    )
    result = runner.invoke(app, ["--token", "T", "pixels", "create", "--name", "p"])
    assert result.exit_code == 0
    assert route.called


def test_segments_help_lists_all_commands():
    result = runner.invoke(app, ["segments", "--help"])
    assert result.exit_code == 0
    for cmd in (
        "list", "create-pixel", "create-lookalike", "create-metrika",
        "create-appmetrica", "create-geo", "create-geo-polygon", "upload-file",
        "upload-csv-file", "update-geo-points", "modify-data", "confirm",
        "confirm-client-id", "update", "delete", "reprocess",
    ):
        assert cmd in result.stdout
    # get удалён: getSegment в Audience API не существует.
    assert " get " not in result.stdout
