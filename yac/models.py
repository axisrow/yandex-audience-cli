"""Модели объектов Yandex Audience API (dataclass).

Поля повторяют JSON-структуры ответов API (имена — как в API).
Модели опциональны для самого CLI (он передаёт JSON напрямую),
но служат документацией формы данных и удобны при программном доступе.

Иерархия типов сегментов отражает API: общий :class:`BaseSegment`
и специализированные подтипы по способу создания.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Any, List, Optional

# --- константы значений API ------------------------------------------------

#: Типы загружаемых данных (content_type у uploading-сегмента).
CONTENT_IDFA_GAID = "idfa_gaid"
CONTENT_CLIENT_ID = "client_id"
CONTENT_MAC = "mac"
CONTENT_CRM = "crm"

#: Права представителя/аккаунта.
PERM_VIEW = "view"
PERM_EDIT = "edit"


def _from_dict(cls, data: dict) -> Any:
    """Создать dataclass из dict, игнорируя неизвестные ключи."""
    known = {f.name for f in fields(cls)}
    return cls(**{k: v for k, v in data.items() if k in known})


# --- сегменты --------------------------------------------------------------


@dataclass
class BaseSegment:
    """Поля, общие для всех типов сегментов."""

    id: Optional[int] = None
    name: Optional[str] = None
    status: Optional[str] = None
    create_time: Optional[str] = None
    owner: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "BaseSegment":
        return _from_dict(cls, data)


@dataclass
class PixelSegment(BaseSegment):
    pixel_id: Optional[int] = None
    period_length: Optional[int] = None
    times_quantity: Optional[int] = None
    times_quantity_operation: Optional[str] = None
    utm_source: Optional[str] = None
    utm_content: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_term: Optional[str] = None
    utm_medium: Optional[str] = None


@dataclass
class LookalikeSegment(BaseSegment):
    lookalike_link: Optional[int] = None
    lookalike_value: Optional[int] = None
    maintain_device_distribution: Optional[bool] = None
    maintain_geo_distribution: Optional[bool] = None


@dataclass
class MetrikaSegment(BaseSegment):
    metrika_segment_type: Optional[str] = None
    metrika_segment_id: Optional[int] = None


@dataclass
class AppMetricaSegment(BaseSegment):
    app_metrica_segment_type: Optional[str] = None
    app_metrica_segment_id: Optional[int] = None


@dataclass
class GeoPoint:
    latitude: float
    longitude: float
    description: Optional[str] = None


@dataclass
class CircleGeoSegment(BaseSegment):
    geo_segment_type: Optional[str] = None
    times_quantity: Optional[int] = None
    period_length: Optional[int] = None
    radius: Optional[int] = None
    points: List[GeoPoint] = field(default_factory=list)


@dataclass
class PolygonGeoSegment(BaseSegment):
    geo_segment_type: Optional[str] = None
    times_quantity: Optional[int] = None
    period_length: Optional[int] = None
    polygons: List[List[GeoPoint]] = field(default_factory=list)


@dataclass
class UploadingSegment(BaseSegment):
    hashed: Optional[bool] = None
    content_type: Optional[str] = None


# --- прочие ресурсы --------------------------------------------------------


@dataclass
class Grant:
    user_login: Optional[str] = None
    created_at: Optional[str] = None
    comment: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "Grant":
        return _from_dict(cls, data)


@dataclass
class Pixel:
    id: Optional[int] = None
    name: Optional[str] = None
    user_quantity_7: Optional[int] = None
    user_quantity_30: Optional[int] = None
    user_quantity_90: Optional[int] = None
    create_time: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "Pixel":
        return _from_dict(cls, data)


@dataclass
class Account:
    user_login: Optional[str] = None
    perm: Optional[str] = None
    created_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "Account":
        return _from_dict(cls, data)


@dataclass
class Delegate:
    user_login: Optional[str] = None
    perm: Optional[str] = None
    created_at: Optional[str] = None
    comment: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "Delegate":
        return _from_dict(cls, data)
