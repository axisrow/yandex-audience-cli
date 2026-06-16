"""Загрузить CSV-файл данных

POST /v1/management/segments/upload_csv_file
"""

from .._core import Endpoint, GROUP_SEGMENTS

ENDPOINT = Endpoint(
    GROUP_SEGMENTS,
    "upload_csv_file",
    "POST",
    "segments/upload_csv_file",
    "Загрузить CSV-файл данных",
    multipart=True,
)
