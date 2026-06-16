"""Интеграция CLI ↔ API: команда проходит весь стек до (мокнутого) HTTP.

В отличие от смоук-тестов (структура CLI, без сети), здесь команда реально
доходит до запроса — respx подменяет сокет и проверяет, что вызов состоялся.
Это связка cli → context → resource → client → HTTP, а не один слой.
"""

from __future__ import annotations

import httpx
import pytest
import respx
from typer.testing import CliRunner

from yac import app

pytestmark = pytest.mark.integration

runner = CliRunner()
BASE = "https://api-audience.yandex.ru/v1/management"


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
