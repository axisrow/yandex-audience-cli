"""Восстановить удалённый пиксель

POST /v1/management/pixel/{id}/undelete
"""

from .._core import Endpoint, GROUP_PIXELS

ENDPOINT = Endpoint(
    GROUP_PIXELS,
    "undelete",
    "POST",
    "pixel/{id}/undelete",
    "Восстановить удалённый пиксель",
    path_params=("id",),
)
