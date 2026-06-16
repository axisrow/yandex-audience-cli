"""Удалить пиксель

DELETE /v1/management/pixel/{id}
"""

from .._core import Endpoint, GROUP_PIXELS

ENDPOINT = Endpoint(
    GROUP_PIXELS,
    "delete",
    "DELETE",
    "pixel/{id}",
    "Удалить пиксель",
    path_params=("id",),
)
