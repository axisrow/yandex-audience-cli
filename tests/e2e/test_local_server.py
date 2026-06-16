"""E2E против НАСТОЯЩЕГО локального сервера — без единого мока.

Самый честный детерминированный e2e: реальный ``yac`` через ``CliRunner`` с
``--base-url`` на поднятый stdlib-сервер (фикстура ``stub_server``). Запрос идёт
весь стек насквозь — cli → context.load_config → Client → httpx → реальный сокет
→ stub. Проверяем, что собранный URL/заголовки верны и ответ доходит до вывода.
"""

from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from yac import app

pytestmark = pytest.mark.e2e

runner = CliRunner()


def test_segments_list_e2e(stub_server):
    stub_server.respond(
        "GET", "segments", json_body={"segments": [{"id": 1, "name": "A"}]}
    )

    result = runner.invoke(
        app,
        [
            "--base-url",
            stub_server.url,
            "--token",
            "T",
            "--output",
            "json",
            "segments",
            "list",
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert "A" in result.stdout
    # Сервер реально получил запрос с верным путём и OAuth-заголовком.
    assert len(stub_server.requests) == 1
    req = stub_server.requests[0]
    assert req.method == "GET"
    assert req.path == "/v1/management/segments"
    assert req.authorization == "OAuth T"


def test_pretty_flag_e2e(stub_server):
    stub_server.respond("GET", "accounts", json_body={"accounts": []})

    result = runner.invoke(
        app,
        ["--base-url", stub_server.url, "--token", "T", "--pretty", "accounts", "list"],
    )

    assert result.exit_code == 0, result.stdout
    # --pretty доходит до query настоящего запроса.
    assert "pretty=1" in stub_server.requests[0].query


def test_api_error_is_clean_e2e(stub_server):
    # Неизвестный путь → стаб отвечает 404 в формате ошибки Audience API.
    # Здесь намеренно НЕ регистрируем маршрут.
    result = runner.invoke(
        app,
        ["--base-url", stub_server.url, "--token", "T", "segments", "delete", "999"],
    )

    assert result.exit_code == 1
    output = result.stdout + (result.stderr or "")
    assert "Traceback" not in output
    # Сообщение из тела ошибки дошло до пользователя (сквозь _extract_error_message).
    assert "unknown path" in output or "404" in output


def test_post_command_reaches_server_e2e(stub_server):
    # POST-команда с телом тоже проходит весь стек до сервера.
    stub_server.respond("POST", "pixels", json_body={"pixel": {"id": 9, "name": "p"}})

    result = runner.invoke(
        app,
        [
            "--base-url",
            stub_server.url,
            "--token",
            "T",
            "pixels",
            "create",
            "--name",
            "p",
        ],
    )

    assert result.exit_code == 0, result.stdout
    req = stub_server.requests[0]
    assert req.method == "POST"
    assert req.path == "/v1/management/pixels"
    # Ответ сервера долетел до вывода (валидный JSON с pixel).
    assert json.loads(result.stdout)["pixel"]["id"] == 9
