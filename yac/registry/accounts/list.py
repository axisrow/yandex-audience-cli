"""Список аккаунтов, где текущий пользователь — представитель

GET /v1/management/accounts
"""

from .._core import Endpoint, GROUP_ACCOUNTS

ENDPOINT = Endpoint(
    GROUP_ACCOUNTS,
    "list",
    "GET",
    "accounts",
    "Список аккаунтов, где текущий пользователь — представитель",
)
