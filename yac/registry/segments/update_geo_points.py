"""Изменить координаты гео-сегмента (окружность)

POST /v1/management/segment/{id}/update_geo_points
"""

from .._core import Endpoint, GROUP_SEGMENTS

ENDPOINT = Endpoint(
    GROUP_SEGMENTS,
    "update_geo_points",
    "POST",
    "segment/{id}/update_geo_points",
    "Изменить координаты гео-сегмента (окружность)",
    path_params=("id",),
)
