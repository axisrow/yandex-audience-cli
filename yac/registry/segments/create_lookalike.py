"""Создать lookalike-сегмент (похожая аудитория)

POST /v1/management/segments/create_lookalike
"""

from .._core import Endpoint, GROUP_SEGMENTS

ENDPOINT = Endpoint(
    GROUP_SEGMENTS,
    "create_lookalike",
    "POST",
    "segments/create_lookalike",
    "Создать lookalike-сегмент (похожая аудитория)",
)
