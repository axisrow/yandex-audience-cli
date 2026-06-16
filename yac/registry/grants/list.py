"""Список разрешений сегмента

GET /v1/management/segment/{id}/grants
"""

from .._core import Endpoint, GROUP_GRANTS

ENDPOINT = Endpoint(
    GROUP_GRANTS,
    "list",
    "GET",
    "segment/{id}/grants",
    "Список разрешений сегмента",
    path_params=("id",),
)
