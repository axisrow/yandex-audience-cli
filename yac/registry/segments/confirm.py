"""Сохранить/подтвердить загруженный сегмент

POST /v1/management/segment/{id}/confirm
"""

from .._core import Endpoint, GROUP_SEGMENTS

ENDPOINT = Endpoint(
    GROUP_SEGMENTS,
    "confirm",
    "POST",
    "segment/{id}/confirm",
    "Сохранить/подтвердить загруженный сегмент",
    path_params=("id",),
)
