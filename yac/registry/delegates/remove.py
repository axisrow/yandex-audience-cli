"""Удалить представителя (?user_login=...)

DELETE /v1/management/delegate
"""

from .._core import Endpoint, GROUP_DELEGATES

ENDPOINT = Endpoint(
    GROUP_DELEGATES,
    "remove",
    "DELETE",
    "delegate",
    "Удалить представителя (?user_login=...)",
)
