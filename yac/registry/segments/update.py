"""Изменить сегмент

PUT /v1/management/segment/{id}
"""

from .._core import Endpoint, GROUP_SEGMENTS

ENDPOINT = Endpoint(
    GROUP_SEGMENTS,
    "update",
    "PUT",
    "segment/{id}",
    "Изменить сегмент",
    path_params=("id",),
)
