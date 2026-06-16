"""Удалить разрешение на сегмент (?user_login=...)

DELETE /v1/management/segment/{id}/grant
"""

from .._core import Endpoint, GROUP_GRANTS

ENDPOINT = Endpoint(
    GROUP_GRANTS,
    "remove",
    "DELETE",
    "segment/{id}/grant",
    "Удалить разрешение на сегмент (?user_login=...)",
    path_params=("id",),
)
