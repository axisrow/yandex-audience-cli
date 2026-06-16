"""Удалить сегмент

DELETE /v1/management/segment/{id}
"""

from .._core import Endpoint, GROUP_SEGMENTS

ENDPOINT = Endpoint(
    GROUP_SEGMENTS,
    "delete",
    "DELETE",
    "segment/{id}",
    "Удалить сегмент",
    path_params=("id",),
)
