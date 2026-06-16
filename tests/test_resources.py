"""Поведенческие тесты ресурсов: верный HTTP-метод и путь для каждого вызова.

Дополняет структурный test_registry_coverage реальной проверкой того,
что метод ресурса обращается ровно к ожидаемому эндпоинту.
"""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from yac.config import Config
from yac.client import Client
from yac.api.accounts import Accounts
from yac.api.delegates import Delegates
from yac.api.grants import Grants
from yac.api.pixels import Pixels
from yac.api.segments import Segments

BASE = "https://api-audience.yandex.ru/v1/management"


@pytest.fixture
def client():
    c = Client(Config(token="T"))
    yield c
    c.close()


def _route(method: str, path: str):
    return respx.route(method=method, url=f"{BASE}/{path}").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )


# (описание, callable(ресурс) -> вызов, ожидаемый HTTP-метод, ожидаемый путь)
CASES = [
    # segments
    ("segments.list", lambda r: r.list(), "GET", "segments"),
    ("segments.create_pixel", lambda r: r.create_pixel({"name": "s"}), "POST", "segments/create_pixel"),
    ("segments.create_lookalike", lambda r: r.create_lookalike({}), "POST", "segments/create_lookalike"),
    ("segments.create_metrika", lambda r: r.create_metrika({}), "POST", "segments/create_metrika"),
    ("segments.create_appmetrica", lambda r: r.create_appmetrica({}), "POST", "segments/create_appmetrica"),
    ("segments.create_geo", lambda r: r.create_geo({}), "POST", "segments/create_geo"),
    ("segments.create_geo_polygon", lambda r: r.create_geo_polygon({}), "POST", "segments/create_geo_polygon"),
    ("segments.update_geo_points", lambda r: r.update_geo_points(7, [{"latitude": 1, "longitude": 2}]),
     "POST", "segment/7/update_geo_points"),
    ("segments.confirm", lambda r: r.confirm(7, {"name": "x"}), "POST", "segment/7/confirm"),
    ("segments.confirm_client_id", lambda r: r.confirm_client_id(7, {}), "POST",
     "segment/client_id/7/confirm"),
    ("segments.update", lambda r: r.update(7, {"name": "x"}), "PUT", "segment/7"),
    ("segments.delete", lambda r: r.delete(7), "DELETE", "segment/7"),
    ("segments.reprocess", lambda r: r.reprocess(7), "PUT", "segment/7/reprocess"),
    # grants
    ("grants.list", lambda r: r.list(7), "GET", "segment/7/grants"),
    ("grants.add", lambda r: r.add(7, "user@ya.ru"), "PUT", "segment/7/grant"),
    ("grants.remove", lambda r: r.remove(7, "user@ya.ru"), "DELETE", "segment/7/grant"),
    # pixels
    ("pixels.list", lambda r: r.list(), "GET", "pixels"),
    ("pixels.create", lambda r: r.create("p"), "POST", "pixels"),
    ("pixels.update", lambda r: r.update(3, "p"), "PUT", "pixel/3"),
    ("pixels.delete", lambda r: r.delete(3), "DELETE", "pixel/3"),
    ("pixels.undelete", lambda r: r.undelete(3), "POST", "pixel/3/undelete"),
    # accounts
    ("accounts.list", lambda r: r.list(), "GET", "accounts"),
    # delegates
    ("delegates.list", lambda r: r.list(), "GET", "delegates"),
    ("delegates.add", lambda r: r.add("user@ya.ru"), "PUT", "delegate"),
    ("delegates.remove", lambda r: r.remove("user@ya.ru"), "DELETE", "delegate"),
]

RESOURCE_BY_GROUP = {
    "segments": Segments,
    "grants": Grants,
    "pixels": Pixels,
    "accounts": Accounts,
    "delegates": Delegates,
}


@pytest.mark.parametrize("name,call,method,path", CASES, ids=[c[0] for c in CASES])
@respx.mock
def test_resource_hits_expected_endpoint(client, name, call, method, path):
    route = _route(method, path)
    group = name.split(".")[0]
    resource = RESOURCE_BY_GROUP[group](client)
    call(resource)
    assert route.called, f"{name}: ожидался {method} {path}"
    assert route.calls.last.request.method == method


@respx.mock
def test_grant_add_optional_permission(client):
    route = respx.put(f"{BASE}/segment/7/grant").mock(return_value=httpx.Response(200, json={}))
    Grants(client).add(7, "u@ya.ru", permission="edit", comment="c")
    body = json.loads(route.calls.last.request.content)
    assert body["grant"] == {"user_login": "u@ya.ru", "permission": "edit", "comment": "c"}


@respx.mock
def test_grant_add_without_optional(client):
    route = respx.put(f"{BASE}/segment/7/grant").mock(return_value=httpx.Response(200, json={}))
    Grants(client).add(7, "u@ya.ru")
    body = json.loads(route.calls.last.request.content)
    assert body["grant"] == {"user_login": "u@ya.ru"}  # без permission/comment


@respx.mock
def test_delegate_add_optional_perm(client):
    route = respx.put(f"{BASE}/delegate").mock(return_value=httpx.Response(200, json={}))
    Delegates(client).add("u@ya.ru", perm="view")
    body = json.loads(route.calls.last.request.content)
    assert body["delegate"] == {"user_login": "u@ya.ru", "perm": "view"}


@respx.mock
def test_segments_list_limit_offset(client):
    route = respx.get(f"{BASE}/segments").mock(return_value=httpx.Response(200, json={"segments": []}))
    Segments(client).list(limit=50, offset=10)
    params = route.calls.last.request.url.params
    assert params["limit"] == "50" and params["offset"] == "10"


@respx.mock
def test_segments_confirm_check_size(client):
    route = respx.post(f"{BASE}/segment/9/confirm").mock(return_value=httpx.Response(200, json={}))
    Segments(client).confirm(9, {"name": "x", "content_type": "crm", "hashed": False}, check_size=False)
    assert route.calls.last.request.url.params["check_size"] == "false"


def test_cases_cover_all_non_upload_endpoints():
    """Все эндпоинты реестра, кроме multipart-загрузок, покрыты кейсами здесь."""
    from yac import registry

    covered = {name for name, *_ in CASES}
    # Multipart-эндпоинты (upload_file, upload_csv_file, modify_data) — в test_uploads.
    multipart_ops = {ep.op for ep in registry.ENDPOINTS if ep.multipart}
    for op in multipart_ops:
        assert f"segments.{op}" not in covered

    expected = {
        f"{ep.group}.{ep.op}"
        for ep in registry.ENDPOINTS
        if not ep.multipart
    }
    assert covered == expected, f"Не покрыты: {expected - covered}"
