"""Создать сегмент из Яндекс.Метрики

POST /v1/management/segments/create_metrika
"""

from .._core import Endpoint, GROUP_SEGMENTS

ENDPOINT = Endpoint(
    GROUP_SEGMENTS,
    "create_metrika",
    "POST",
    "segments/create_metrika",
    "Создать сегмент из Яндекс.Метрики",
)
