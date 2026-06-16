"""Создать гео-сегмент (окружность)

POST /v1/management/segments/create_geo
"""

from .._core import Endpoint, GROUP_SEGMENTS

ENDPOINT = Endpoint(
    GROUP_SEGMENTS,
    "create_geo",
    "POST",
    "segments/create_geo",
    "Создать гео-сегмент (окружность)",
)
