"""Создать пиксель

POST /v1/management/pixels
"""

from .._core import Endpoint, GROUP_PIXELS

ENDPOINT = Endpoint(GROUP_PIXELS, "create", "POST", "pixels", "Создать пиксель")
