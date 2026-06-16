"""Список сегментов (опц. фильтр ?pixel=ID)

GET /v1/management/segments
"""

from .._core import Endpoint, GROUP_SEGMENTS

ENDPOINT = Endpoint(
    GROUP_SEGMENTS,
    "list",
    "GET",
    "segments",
    "Список сегментов (опц. фильтр ?pixel=ID)",
)
