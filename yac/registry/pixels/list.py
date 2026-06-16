"""Список пикселей

GET /v1/management/pixels
"""

from .._core import Endpoint, GROUP_PIXELS

ENDPOINT = Endpoint(GROUP_PIXELS, "list", "GET", "pixels", "Список пикселей")
