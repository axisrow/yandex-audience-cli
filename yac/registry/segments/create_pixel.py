"""Создать сегмент на основе пикселя

POST /v1/management/segments/create_pixel
"""

from .._core import Endpoint, GROUP_SEGMENTS

ENDPOINT = Endpoint(
    GROUP_SEGMENTS,
    "create_pixel",
    "POST",
    "segments/create_pixel",
    "Создать сегмент на основе пикселя",
)
