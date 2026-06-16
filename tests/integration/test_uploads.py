"""Тесты загрузки файлов (multipart/form-data) для upload-эндпоинтов."""

from __future__ import annotations

import httpx
import pytest
import respx

from yac.config import Config
from yac.client import Client
from yac.api.segments import Segments

pytestmark = pytest.mark.integration

BASE = "https://api-audience.yandex.ru/v1/management"


@respx.mock
def test_upload_file_multipart(tmp_path):
    f = tmp_path / "data.txt"
    f.write_text("email\nuser@example.com\n", encoding="utf-8")
    route = respx.post(f"{BASE}/segments/upload_file").mock(
        return_value=httpx.Response(200, json={"segment": {"id": 1}})
    )
    with Client(Config(token="T")) as c:
        Segments(c).upload_file(str(f))

    req = route.calls.last.request
    assert req.method == "POST"
    assert b"multipart/form-data" in req.headers["content-type"].encode()
    assert b"data.txt" in req.content


@respx.mock
def test_upload_csv_file_multipart(tmp_path):
    f = tmp_path / "data.csv"
    f.write_text("email\nuser@example.com\n", encoding="utf-8")
    route = respx.post(f"{BASE}/segments/upload_csv_file").mock(
        return_value=httpx.Response(200, json={"segment": {"id": 2}})
    )
    with Client(Config(token="T")) as c:
        Segments(c).upload_csv_file(str(f))
    assert route.called


@respx.mock
def test_modify_data_multipart_with_query(tmp_path):
    f = tmp_path / "more.csv"
    f.write_text("email\nuser@example.com\n", encoding="utf-8")
    route = respx.post(f"{BASE}/segment/5/modify_data").mock(
        return_value=httpx.Response(200, json={"segment": {"id": 5}})
    )
    with Client(Config(token="T")) as c:
        Segments(c).modify_data(5, str(f), "addition", check_size=False)

    req = route.calls.last.request
    assert req.method == "POST"
    assert b"multipart/form-data" in req.headers["content-type"].encode()
    assert req.url.params["modification_type"] == "addition"
    assert req.url.params["check_size"] == "false"
