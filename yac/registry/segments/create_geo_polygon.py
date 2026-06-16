"""Создать гео-сегмент (полигон)

POST /v1/management/segments/create_geo_polygon
"""

from .._core import Endpoint, GROUP_SEGMENTS

ENDPOINT = Endpoint(
    GROUP_SEGMENTS,
    "create_geo_polygon",
    "POST",
    "segments/create_geo_polygon",
    "Создать гео-сегмент (полигон)",
)
