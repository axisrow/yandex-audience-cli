"""E2E против БОЕВОГО Yandex Audience API — opt-in, по реальному токену.

По умолчанию пропускается: бьёт в настоящий ``api-audience.yandex.ru`` и требует
действующий OAuth-токен в ``YAC_E2E_TOKEN``. Только read-only вызовы — никаких
мутаций боевого аккаунта. Запуск осознанный::

    YAC_E2E_TOKEN=*** pytest tests/e2e/test_live_api.py
"""

from __future__ import annotations

import json
import os

import pytest
from typer.testing import CliRunner

from yac import app

_TOKEN = os.getenv("YAC_E2E_TOKEN")

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(not _TOKEN, reason="нужен YAC_E2E_TOKEN для боевого e2e"),
]

runner = CliRunner()


def test_live_segments_list():
    assert _TOKEN  # гарантировано skipif; здесь сужаем тип до str
    # Read-only: список сегментов боевого аккаунта.
    result = runner.invoke(
        app, ["--token", _TOKEN, "--output", "json", "segments", "list"]
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    # Audience отдаёт {"segments": [...]}; проверяем форму, не содержимое.
    assert isinstance(payload, dict)
    assert "segments" in payload


def test_live_accounts_list():
    assert _TOKEN  # гарантировано skipif; здесь сужаем тип до str
    # Read-only: доступные представительские аккаунты.
    result = runner.invoke(
        app, ["--token", _TOKEN, "--output", "json", "accounts", "list"]
    )
    assert result.exit_code == 0, result.stdout
    json.loads(result.stdout)  # ответ — валидный JSON
