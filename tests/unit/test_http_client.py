"""Тесты транспорта: авторизация, сборка URL, pretty, обработка ошибок и 429."""

from __future__ import annotations

import httpx
import pytest
import respx

from yac.config import Config
from yac.client import APIError, Client, RateLimitError

pytestmark = pytest.mark.unit

BASE = "https://api-audience.yandex.ru/v1/management"


@pytest.fixture(autouse=True)
def no_real_sleep(monkeypatch):
    """Перехват сна клиента: тесты не должны реально ждать 60с, а ассерты по
    паузам идут через этот шпион (yac.client._sleep)."""
    calls: list[float] = []
    monkeypatch.setattr("yac.client._sleep", calls.append, raising=False)
    return calls


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
def test_rate_limit_raises_after_retry():
    """Упорный 429: RateLimitError после исчерпания ретраев, ровно 2 попытки, пауза 60с."""
    route = respx.get(f"{BASE}/segments").mock(
        side_effect=[
            httpx.Response(429, json={"errors": [{"text": "quota"}]}),
            httpx.Response(429, json={"errors": [{"text": "quota"}]}),
        ]
    )
    with make_client() as c:
        with pytest.raises(RateLimitError) as exc:
            c.request("GET", "segments")
    assert exc.value.status_code == 429
    assert route.call_count == 2, "после 429 должна быть ровно одна повторная попытка"


@respx.mock
def test_429_retried_then_success(no_real_sleep):
    """429 → пауза (дефолт 60с) → повтор → успех: потребителю не видно квотного голода."""
    route = respx.get(f"{BASE}/segments").mock(
        side_effect=[
            httpx.Response(429, json={"errors": [{"text": "quota"}]}),
            httpx.Response(200, json={"segments": []}),
        ]
    )
    with make_client() as c:
        result = c.request("GET", "segments")
    assert result == {"segments": []}
    assert route.call_count == 2
    assert no_real_sleep == [60.0], "пауза по умолчанию — 60с (Retry-After отсутствует)"


@respx.mock
def test_retry_after_header_honored(no_real_sleep):
    """Retry-After от API уважается: спим указанное число секунд, не дефолтные 60."""
    respx.get(f"{BASE}/segments").mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "30"}, json={}),
            httpx.Response(200, json={"segments": []}),
        ]
    )
    with make_client() as c:
        assert c.request("GET", "segments") == {"segments": []}
    assert no_real_sleep == [30.0]


@respx.mock
def test_retry_after_garbage_falls_back_to_default(no_real_sleep):
    """Мусорный Retry-After не роняет клиента — дефолтные 60с."""
    respx.get(f"{BASE}/segments").mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "soon"}, json={}),
            httpx.Response(200, json={"segments": []}),
        ]
    )
    with make_client() as c:
        assert c.request("GET", "segments") == {"segments": []}
    assert no_real_sleep == [60.0]


@respx.mock
def test_retry_after_negative_clamped(no_real_sleep):
    """Отрицательный Retry-After зажимается в 0 (иначе time.sleep(-5) бросил бы ValueError)."""
    respx.get(f"{BASE}/segments").mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "-5"}, json={}),
            httpx.Response(200, json={"segments": []}),
        ]
    )
    with make_client() as c:
        assert c.request("GET", "segments") == {"segments": []}
    assert no_real_sleep == [0.0]


@respx.mock
def test_non_429_errors_not_retried(no_real_sleep):
    """Доменные ошибки (не 429) ретраям не подлежат — ровно один запрос."""
    route = respx.get(f"{BASE}/segment/1").mock(
        return_value=httpx.Response(404, json={"errors": [{"text": "not found"}]})
    )
    with make_client() as c:
        with pytest.raises(APIError):
            c.request("GET", "segment/1")
    assert route.call_count == 1
    assert no_real_sleep == []


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
