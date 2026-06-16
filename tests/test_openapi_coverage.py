"""Аудит покрытия: реестр ↔ снимок спеки Yandex Audience API (offline).

Читает закоммиченный снапшот ``tests/data/audience_spec.json`` (его обновляет
``scripts/fetch_spec.py``, там вся сеть) и строго сверяет с ``registry.ENDPOINTS``
по ``(method, normalized_path)``; ``multipart`` сравнивается как атрибут.

Падает на ЛЮБОМ расхождении (missing/extra/changed) — так дрейф API Яндекса
становится красным тестом, а не строкой в докстринге. Эндпоинт с ``unverified=True``
исключается из строгой сверки и репортится мягким skip (сейчас таких нет).
"""

import json
from pathlib import Path

import pytest

from yac import registry
from yac.openapi_coverage import compute_coverage, normalize_path

pytestmark = pytest.mark.unit

SNAPSHOT = Path(__file__).parent / "data" / "audience_spec.json"


@pytest.fixture(scope="module")
def snapshot() -> dict:
    with SNAPSHOT.open(encoding="utf-8") as fp:
        return json.load(fp)


def test_no_missing_endpoints(snapshot):
    """В спеке Яндекса нет эндпоинта, которого нет в реестре (новый метод API)."""
    result = compute_coverage(snapshot, registry.ENDPOINTS)
    assert (
        not result.missing
    ), "Эндпоинты есть в спеке Яндекса, но НЕТ в реестре: " + ", ".join(
        f"{o.method} {o.path}" for o in result.missing
    )


def test_no_extra_endpoints(snapshot):
    """В реестре нет эндпоинта, которого нет в спеке (удалён/переименован/неверный slug)."""
    result = compute_coverage(snapshot, registry.ENDPOINTS)
    assert (
        not result.extra
    ), "Эндпоинты есть в реестре, но НЕТ в спеке Яндекса: " + ", ".join(
        f"{o.label} ({o.method} {o.path})" for o in result.extra
    )


def test_no_multipart_drift(snapshot):
    """Совпал (method, path), но разошёлся признак multipart."""
    result = compute_coverage(snapshot, registry.ENDPOINTS)
    assert not result.changed, "Расхождение multipart: " + "; ".join(result.changed)


def test_unverified_are_soft_skipped(snapshot):
    """unverified-эндпоинты не валят сверку, а отмечаются skip (механизм на будущее)."""
    result = compute_coverage(snapshot, registry.ENDPOINTS)
    if result.unverified:
        pytest.skip("unverified (вне строгой сверки): " + ", ".join(result.unverified))


def test_counts_match(snapshot):
    """Число операций в снапшоте = числу эндпоинтов реестра."""
    assert len(snapshot["operations"]) == len(registry.ENDPOINTS)


# --- table-driven юнит на normalize_path (пинит контракт независимо от снапшота) ---


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("segment/{segmentId}/grant", "segment/{}/grant"),
        ("segment/{id}/grant", "segment/{}/grant"),
        ("segment/{pixelId}/grants", "segment/{}/grants"),
        (
            "segment/111/modify_data?modification_type=addition",
            "segment/{}/modify_data",
        ),
        ("segment/{id}/modify_data", "segment/{}/modify_data"),
        ("segments/upload_file", "segments/upload_file"),
        ("segment/client_id/{id}/confirm", "segment/client_id/{}/confirm"),
        ("/segments/", "segments"),
        ("pixels", "pixels"),
    ],
)
def test_normalize_path(raw, expected):
    assert normalize_path(raw) == expected
