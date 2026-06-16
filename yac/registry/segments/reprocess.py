"""Переобработать (пересчитать) сегмент

PUT /v1/management/segment/{id}/reprocess
"""

from .._core import Endpoint, GROUP_SEGMENTS

ENDPOINT = Endpoint(
    GROUP_SEGMENTS,
    "reprocess",
    "PUT",
    "segment/{id}/reprocess",
    "Переобработать (пересчитать) сегмент",
    path_params=("id",),
)
