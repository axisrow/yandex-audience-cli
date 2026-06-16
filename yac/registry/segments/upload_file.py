"""Загрузить файл данных (CRM/idfa_gaid/mac/client_id)

POST /v1/management/segments/upload_file
"""

from .._core import Endpoint, GROUP_SEGMENTS

ENDPOINT = Endpoint(
    GROUP_SEGMENTS,
    "upload_file",
    "POST",
    "segments/upload_file",
    "Загрузить файл данных (CRM/idfa_gaid/mac/client_id)",
    multipart=True,
)
