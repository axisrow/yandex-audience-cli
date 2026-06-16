"""Тесты транспорта: авторизация, сборка URL, pretty, обработка ошибок и 429."""

from __future__ import annotations

import httpx
import pytest
import respx

from yac.config import Config
from yac.client import APIError, Client, RateLimitError

BASE = "https://api-audience.yandex.ru/v1/management"


def make_client() -> Client:
    return Client(Config(token="TESTTOKEN"))


@respx.mock
def test_oauth_header_and_url():
    route = respx.get(f"{BASE}/segments").mock(
        return_value=httpx.Response(200, json={"segments": []})
    )
    with make_client() as c:
        result = c.request("GET", "segments")

    assert result == {"segments": []}
    sent = route.calls.last.request
    assert sent.headers["Authorization"] == "OAuth TESTTOKEN"
    assert str(sent.url) == f"{BASE}/segments"


@respx.mock
def test_pretty_param_added():
    route = respx.get(f"{BASE}/accounts").mock(
        return_value=httpx.Response(200, json={"accounts": []})
    )
    with make_client() as c:
        c.request("GET", "accounts", pretty=True)
    assert route.calls.last.request.url.params["pretty"] == "1"


@respx.mock
def test_query_params_passed():
    route = respx.get(f"{BASE}/segments").mock(
        return_value=httpx.Response(200, json={"segments": []})
    )
    with make_client() as c:
        c.request("GET", "segments", params={"pixel": 42})
    assert route.calls.last.request.url.params["pixel"] == "42"


@respx.mock
def test_empty_body_returns_none():
    respx.delete(f"{BASE}/segment/5").mock(return_value=httpx.Response(204))
    with make_client() as c:
        assert c.request("DELETE", "segment/5") is None


@respx.mock
def test_rate_limit_raises():
    respx.get(f"{BASE}/segments").mock(
        return_value=httpx.Response(429, json={"errors": [{"text": "quota"}]})
    )
    with make_client() as c:
        with pytest.raises(RateLimitError) as exc:
            c.request("GET", "segments")
    assert exc.value.status_code == 429


@respx.mock
def test_api_error_message_extracted():
    respx.get(f"{BASE}/segment/1").mock(
        return_value=httpx.Response(404, json={"errors": [{"text": "not found"}]})
    )
    with make_client() as c:
        with pytest.raises(APIError) as exc:
            c.request("GET", "segment/1")
    assert "not found" in str(exc.value)
    assert exc.value.status_code == 404
