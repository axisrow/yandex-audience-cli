"""Список представителей (делегатов)

GET /v1/management/delegates
"""

from .._core import Endpoint, GROUP_DELEGATES

ENDPOINT = Endpoint(
    GROUP_DELEGATES, "list", "GET", "delegates", "Список представителей (делегатов)"
)
