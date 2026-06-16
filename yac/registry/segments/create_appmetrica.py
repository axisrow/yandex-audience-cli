"""Создать сегмент из AppMetrica

POST /v1/management/segments/create_appmetrica
"""

from .._core import Endpoint, GROUP_SEGMENTS

ENDPOINT = Endpoint(
    GROUP_SEGMENTS,
    "create_appmetrica",
    "POST",
    "segments/create_appmetrica",
    "Создать сегмент из AppMetrica",
)
