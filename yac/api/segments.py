"""Ресурс «Сегменты» — 16 эндпоинтов.

Имена методов совпадают с ``op`` соответствующих эндпоинтов в registry.py.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from ..registry import GROUP_SEGMENTS
from ..base import Resource


class Segments(Resource):
    group = GROUP_SEGMENTS

    # -- чтение -------------------------------------------------------------
    def list(
        self,
        *,
        pixel: Optional[int] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        pretty: bool = False,
    ) -> Any:
        params: dict = {}
        if pixel is not None:
            params["pixel"] = pixel
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        return self._call("list", params=params or None, pretty=pretty)

    # -- создание сегментов по типам ---------------------------------------
    def create_pixel(self, segment: dict, *, pretty: bool = False) -> Any:
        return self._call("create_pixel", json={"segment": segment}, pretty=pretty)

    def create_lookalike(self, segment: dict, *, pretty: bool = False) -> Any:
        return self._call("create_lookalike", json={"segment": segment}, pretty=pretty)

    def create_metrika(self, segment: dict, *, pretty: bool = False) -> Any:
        return self._call("create_metrika", json={"segment": segment}, pretty=pretty)

    def create_appmetrica(self, segment: dict, *, pretty: bool = False) -> Any:
        return self._call("create_appmetrica", json={"segment": segment}, pretty=pretty)

    def create_geo(self, segment: dict, *, pretty: bool = False) -> Any:
        return self._call("create_geo", json={"segment": segment}, pretty=pretty)

    def create_geo_polygon(self, segment: dict, *, pretty: bool = False) -> Any:
        return self._call("create_geo_polygon", json={"segment": segment}, pretty=pretty)

    # -- загрузка файлов ----------------------------------------------------
    def upload_file(self, file_path: str, *, pretty: bool = False) -> Any:
        return self._upload("upload_file", file_path, pretty=pretty)

    def upload_csv_file(self, file_path: str, *, pretty: bool = False) -> Any:
        return self._upload("upload_csv_file", file_path, pretty=pretty)

    def _upload(self, op: str, file_path: str, *, pretty: bool) -> Any:
        path = Path(file_path)
        with path.open("rb") as fh:
            files = {"file": (path.name, fh)}
            return self._call(op, files=files, pretty=pretty)

    # -- изменение координат гео-окружности --------------------------------
    def update_geo_points(self, segment_id: int, points: list, *, pretty: bool = False) -> Any:
        return self._call(
            "update_geo_points", id=segment_id, json={"points": points}, pretty=pretty
        )

    # -- изменение данных загруженного сегмента (multipart) ----------------
    def modify_data(
        self,
        segment_id: int,
        file_path: str,
        modification_type: str,
        *,
        check_size: Optional[bool] = None,
        pretty: bool = False,
    ) -> Any:
        params: dict = {"modification_type": modification_type}
        if check_size is not None:
            params["check_size"] = str(check_size).lower()
        path = Path(file_path)
        with path.open("rb") as fh:
            files = {"file": (path.name, fh)}
            return self._call(
                "modify_data", id=segment_id, params=params, files=files, pretty=pretty
            )

    # -- подтверждение/сохранение загруженного сегмента --------------------
    def confirm(
        self,
        segment_id: int,
        segment: dict,
        *,
        check_size: Optional[bool] = None,
        pretty: bool = False,
    ) -> Any:
        params = {"check_size": str(check_size).lower()} if check_size is not None else None
        return self._call(
            "confirm", id=segment_id, params=params, json={"segment": segment}, pretty=pretty
        )

    def confirm_client_id(self, segment_id: int, segment: dict, *, pretty: bool = False) -> Any:
        return self._call(
            "confirm_client_id", id=segment_id, json={"segment": segment}, pretty=pretty
        )

    # -- изменение / удаление / переобработка ------------------------------
    def update(self, segment_id: int, segment: dict, *, pretty: bool = False) -> Any:
        return self._call("update", id=segment_id, json={"segment": segment}, pretty=pretty)

    def delete(self, segment_id: int, *, pretty: bool = False) -> Any:
        return self._call("delete", id=segment_id, pretty=pretty)

    def reprocess(self, segment_id: int, *, pretty: bool = False) -> Any:
        return self._call("reprocess", id=segment_id, pretty=pretty)
