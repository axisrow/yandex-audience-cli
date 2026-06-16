"""Добавить представителя

PUT /v1/management/delegate
"""

from .._core import Endpoint, GROUP_DELEGATES

ENDPOINT = Endpoint(GROUP_DELEGATES, "add", "PUT", "delegate", "Добавить представителя")
