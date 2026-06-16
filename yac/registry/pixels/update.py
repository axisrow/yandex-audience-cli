"""Изменить пиксель

PUT /v1/management/pixel/{id}
"""

from .._core import Endpoint, GROUP_PIXELS

ENDPOINT = Endpoint(
    GROUP_PIXELS, "update", "PUT", "pixel/{id}", "Изменить пиксель", path_params=("id",)
)
