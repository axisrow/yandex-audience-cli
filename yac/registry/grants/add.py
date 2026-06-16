"""Создать разрешение на сегмент

PUT /v1/management/segment/{id}/grant
"""

from .._core import Endpoint, GROUP_GRANTS

ENDPOINT = Endpoint(
    GROUP_GRANTS,
    "add",
    "PUT",
    "segment/{id}/grant",
    "Создать разрешение на сегмент",
    path_params=("id",),
)
