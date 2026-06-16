"""Сверка реестра эндпоинтов с снимком спеки Yandex Audience API.

Чистые функции без сети и I/O: нормализация путей, приведение спеки и реестра к
сравнимым операциям, вычисление покрытия (missing/extra/changed). Снимок спеки
добывает ``scripts/fetch_spec.py`` (там вся сеть); тест читает закоммиченный JSON.

Ключ сравнения — ``(method, normalized_path)``; ``multipart`` сравнивается как
атрибут (его расхождение → ``changed``, а не missing+extra). Все 28 эндпоинтов
реестра уникальны по этому ключу.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List, Tuple

# Любой плейсхолдер {...} (в спеке {segmentId}/{pixelId}, в реестре {id}) → {}.
_BRACE_RE = re.compile(r"\{[^}]*\}")


def normalize_path(path: str) -> str:
    """Привести путь к сравнимой форме (одинаково для спеки и реестра).

    1. Отбросить query-строку (``?modification_type=...``).
    2. Любой ``{...}`` → ``{}`` (стереть имя параметра).
    3. Числовой сегмент пути (живой пример ``/111/``) → ``{}``.
    4. Снять ведущий/замыкающий ``/``.
    """
    path = path.split("?", 1)[0]
    path = _BRACE_RE.sub("{}", path)
    segments = ["{}" if seg.isdigit() else seg for seg in path.split("/")]
    return "/".join(segments).strip("/")


# Сравнимая операция: ключ (method, path) + атрибуты.
@dataclass(frozen=True)
class Operation:
    method: str
    path: str
    multipart: bool
    label: str  # для диагностики: "group.op" или "group/slug"

    @property
    def key(self) -> Tuple[str, str]:
        return (self.method, self.path)


@dataclass
class CoverageResult:
    missing: List[Operation]  # в спеке есть, в реестре нет
    extra: List[Operation]  # в реестре есть, в спеке нет
    changed: List[str]  # совпал ключ, но разошёлся multipart
    unverified: List[str]  # эндпоинты реестра с unverified=True (мягкий skip)

    @property
    def ok(self) -> bool:
        return not (self.missing or self.extra or self.changed)


def spec_operations(snapshot: dict) -> List[Operation]:
    """Операции из снапшота спеки (путь уже нормализован при сборке)."""
    ops = []
    for o in snapshot["operations"]:
        ops.append(
            Operation(
                method=o["method"].upper(),
                path=normalize_path(o["path"]),
                multipart=bool(o["multipart"]),
                label=f"{o['group']}.{o['op']}",
            )
        )
    return ops


def registry_operations(endpoints: Iterable) -> Tuple[List[Operation], List[str]]:
    """Операции реестра + список unverified-эндпоинтов (исключены из строгой сверки)."""
    ops: List[Operation] = []
    unverified: List[str] = []
    for ep in endpoints:
        label = f"{ep.group}.{ep.op}"
        if getattr(ep, "unverified", False):
            unverified.append(label)
            continue
        ops.append(
            Operation(
                method=ep.method.upper(),
                path=normalize_path(ep.path),
                multipart=bool(ep.multipart),
                label=label,
            )
        )
    return ops, unverified


def compute_coverage(snapshot: dict, endpoints: Iterable) -> CoverageResult:
    """Сверить снапшот спеки с реестром по (method, path); multipart — атрибут."""
    spec = {op.key: op for op in spec_operations(snapshot)}
    reg_ops, unverified = registry_operations(endpoints)
    reg = {op.key: op for op in reg_ops}

    missing = [op for key, op in spec.items() if key not in reg]
    extra = [op for key, op in reg.items() if key not in spec]
    changed = [
        f"{reg[key].label}: multipart spec={spec[key].multipart} "
        f"registry={reg[key].multipart}"
        for key in spec.keys() & reg.keys()
        if spec[key].multipart != reg[key].multipart
    ]
    return CoverageResult(
        missing=sorted(missing, key=lambda o: o.key),
        extra=sorted(extra, key=lambda o: o.key),
        changed=sorted(changed),
        unverified=sorted(unverified),
    )
