"""Изменить данные загруженного из файла сегмента

POST /v1/management/segment/{id}/modify_data
"""

from .._core import Endpoint, GROUP_SEGMENTS

ENDPOINT = Endpoint(
    GROUP_SEGMENTS,
    "modify_data",
    "POST",
    "segment/{id}/modify_data",
    "Изменить данные загруженного из файла сегмента",
    multipart=True,
    path_params=("id",),
)
