"""Сохранить сегмент из ClientId Метрики

POST /v1/management/segment/client_id/{id}/confirm
"""

from .._core import Endpoint, GROUP_SEGMENTS

ENDPOINT = Endpoint(
    GROUP_SEGMENTS,
    "confirm_client_id",
    "POST",
    "segment/client_id/{id}/confirm",
    "Сохранить сегмент из ClientId Метрики",
    path_params=("id",),
)
