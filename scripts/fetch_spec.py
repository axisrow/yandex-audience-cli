#!/usr/bin/env python3
"""Снимок спеки Yandex Audience API для аудита покрытия реестра.

Тянет страницы справочника (Diplodoc `.md`, локаль `ru`), парсит из каждой
HTTP-метод + полный URL ресурса + признак multipart, нормализует путь и пишет
снапшот ``tests/data/audience_spec.json``. Этот снапшот — offline-источник правды
для ``tests/test_openapi_coverage.py`` (тест сети НЕ трогает).

Сеть живёт ТОЛЬКО здесь. Обновление снапшота — ручное:

    python scripts/fetch_spec.py            # перезаписать снапшот
    git diff tests/data/audience_spec.json  # пусто → API не дрейфовал

Перед доверием карте слагов — выверить её эмпирически:

    python scripts/fetch_spec.py --probe    # по каждому слагу: 200|404 + (method, path)

Слаги справочника НЕ выводятся из ``op`` (напр. список сегментов = слаг ``segments``,
не ``list``) и машинного TOC у Diplodoc нет — поэтому карта ``SLUGS`` задаётся явно.
Только stdlib (urllib) — без новых зависимостей.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, List, Tuple

# Путь к пакету в sys.path, чтобы импортировать реестр при запуске из корня репо.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from yac import registry  # noqa: E402  (после правки sys.path)
from yac.openapi_coverage import normalize_path  # noqa: E402

DOCS_BASE = "https://yandex.ru/dev/audience/ru/ref/openapi"
API_BASE = "https://api-audience.yandex.ru/v1/management"
SNAPSHOT = _REPO_ROOT / "tests" / "data" / "audience_spec.json"

# Карта (group, op) -> slug страницы справочника. Слаги НЕ выводимы из op и без
# машинного TOC — заданы явно и выверены `--probe`. Ключи обязаны точно совпадать
# с множеством (ep.group, ep.op) реестра (проверяется _check_map_covers_registry).
SLUGS: Dict[Tuple[str, str], str] = {
    ("segments", "list"): "segments",
    ("segments", "create_pixel"): "createPixel",
    ("segments", "create_metrika"): "createMetrika",
    ("segments", "create_lookalike"): "createLookalike",
    ("segments", "create_geo"): "createGeo",
    ("segments", "create_geo_polygon"): "createGeoPolygon",
    ("segments", "create_appmetrica"): "createAppMetrica",
    ("segments", "upload_file"): "uploadFile",
    ("segments", "upload_csv_file"): "uploadCsvFile",
    ("segments", "update_geo_points"): "updateGeoPoints",
    ("segments", "modify_data"): "modifyUploadingData",
    ("segments", "confirm"): "confirm",
    ("segments", "confirm_client_id"): "confirmClientId",
    ("segments", "update"): "edit",
    ("segments", "delete"): "delete",
    ("segments", "reprocess"): "reprocessSegment",
    ("grants", "list"): "grants",
    ("grants", "add"): "addGrant",
    ("grants", "remove"): "deleteGrant",
    ("pixels", "list"): "pixels",
    ("pixels", "create"): "create",
    ("pixels", "update"): "editPixel",
    ("pixels", "delete"): "deletePixel",
    ("pixels", "undelete"): "undelete",
    ("accounts", "list"): "accounts",
    ("delegates", "list"): "delegates",
    ("delegates", "add"): "addDelegate",
    ("delegates", "remove"): "deleteDelegate",
}

# Блок метода в .md: строка `<METHOD> {.openapi__method}`.
_METHOD_RE = re.compile(
    r"^\s*(GET|POST|PUT|DELETE)\s+\{\.openapi__method\}", re.MULTILINE
)
# Полный URL ресурса.
_URL_RE = re.compile(re.escape(API_BASE) + r"/(\S+)")


def _check_map_covers_registry() -> None:
    """Карта слагов обязана покрывать ровно множество эндпоинтов реестра."""
    reg = {(ep.group, ep.op) for ep in registry.ENDPOINTS}
    mapped = set(SLUGS)
    missing = reg - mapped
    extra = mapped - reg
    if missing or extra:
        raise SystemExit(
            f"Карта SLUGS рассинхронизирована с реестром: "
            f"нет в карте={sorted(missing)}, лишние в карте={sorted(extra)}"
        )


def _fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "yac-spec-audit/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", "replace")


def parse_page(text: str) -> List[Tuple[str, str, bool]]:
    """Извлечь ВСЕ операции страницы: список (method, normalized_path, multipart).

    Страница может нести несколько `<METHOD> {.openapi__method}`-блоков; URL
    привязывается к своему блоку (первый URL ПОСЛЕ метода). multipart — признак
    всей страницы (подстрока ``multipart/form-data``).
    """
    multipart = "multipart/form-data" in text
    ops: List[Tuple[str, str, bool]] = []
    for m in _METHOD_RE.finditer(text):
        method = m.group(1)
        url_match = _URL_RE.search(text, m.end())
        if not url_match:
            raise ValueError(f"После метода {method} не найден URL ресурса")
        raw_path = url_match.group(1).rstrip("`\"' \t\r\n")
        ops.append((method, normalize_path(raw_path), multipart))
    if not ops:
        raise ValueError("На странице не найдено ни одного блока метода")
    return ops


def _iter_pages():
    """Уникальные страницы (slug может быть общим — напр. pixels create/list)."""
    seen_slugs = set()
    for (group, _op), slug in SLUGS.items():
        key = (group, slug)
        if key in seen_slugs:
            continue
        seen_slugs.add(key)
        yield group, slug


def probe() -> int:
    """Печать по каждому слагу: HTTP-код + распарсенные (method, path)."""
    _check_map_covers_registry()
    bad = 0
    print(f"{'group/slug':40} code  operations")
    for group, slug in _iter_pages():
        url = f"{DOCS_BASE}/{group}/{slug}.md"
        try:
            text = _fetch(url)
            code = 200
        except urllib.error.HTTPError as e:
            code = e.code
            text = ""
        except (
            Exception
        ) as e:  # noqa: BLE001 — сетевые/прочие, печатаем и считаем плохим
            print(f"{group + '/' + slug:40} ERR   {e}")
            bad += 1
            continue
        if code != 200:
            print(f"{group + '/' + slug:40} {code}")
            bad += 1
            continue
        try:
            ops = parse_page(text)
            ops_str = ", ".join(f"{m} {p} mp={mp}" for m, p, mp in ops)
        except ValueError as e:
            ops_str = f"ПАРС-ОШИБКА: {e}"
            bad += 1
        print(f"{group + '/' + slug:40} 200   {ops_str}")
        time.sleep(0.3)
    print(f"\nПлохих страниц: {bad}/{sum(1 for _ in _iter_pages())}")
    return bad


def build_snapshot() -> dict:
    """Собрать снапшот: по операции на каждый (group, op) реестра."""
    _check_map_covers_registry()
    # Кэш распарсенных страниц, чтобы общий слаг (pixels) тянуть один раз.
    page_cache: Dict[Tuple[str, str], List[Tuple[str, str, bool]]] = {}
    operations: List[dict] = []
    for ep in registry.ENDPOINTS:
        slug = SLUGS[(ep.group, ep.op)]
        cache_key = (ep.group, slug)
        if cache_key not in page_cache:
            url = f"{DOCS_BASE}/{ep.group}/{slug}.md"
            page_cache[cache_key] = parse_page(_fetch(url))
            time.sleep(0.3)
        page_ops = page_cache[cache_key]
        # На странице может быть несколько методов — берём совпадающий с реестром.
        want_method = ep.method.upper()
        match = next((o for o in page_ops if o[0] == want_method), None)
        if match is None:
            raise SystemExit(
                f"На странице {ep.group}/{slug} нет метода {want_method} "
                f"для {ep.group}.{ep.op} (есть: {[o[0] for o in page_ops]})"
            )
        method, path, multipart = match
        operations.append(
            {
                "group": ep.group,
                "op": ep.op,
                "slug": slug,
                "method": method,
                "path": path,
                "multipart": multipart,
            }
        )
    operations.sort(key=lambda o: (o["group"], o["op"]))
    return {
        "source": DOCS_BASE,
        "locale": "ru",
        "base_path": "/v1/management",
        "generated_by": "scripts/fetch_spec.py",
        "operations": operations,
    }


def write_snapshot() -> None:
    data = build_snapshot()
    SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
    with SNAPSHOT.open("w", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=2, sort_keys=True)
        fp.write("\n")
    print(f"Снапшот записан: {SNAPSHOT} ({len(data['operations'])} операций)")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--probe",
        action="store_true",
        help="Только проверить слаги (200/404) и распарсенные операции, не писать снапшот.",
    )
    args = ap.parse_args()
    if args.probe:
        return 1 if probe() else 0
    write_snapshot()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
