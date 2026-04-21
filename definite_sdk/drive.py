"""Client for writing files to Definite Drive."""

import io
import os
from dataclasses import dataclass
from typing import BinaryIO, Optional, Union

import requests

UPLOAD_URL_ENDPOINT = "/v3/drive/upload-url"

WritableData = Union[bytes, str, os.PathLike, BinaryIO]


@dataclass(frozen=True)
class DriveWriteResult:
    """Result of a Drive write.

    - gcs_path: full GCS URI, usable in SQL via read_parquet(...), read_csv(...), etc.
    - drive_path: the path a pipeline sandbox sees (/home/user/drive/...).
    - path: the relative path within the team's drive (e.g. 'ingest/events.parquet').
    - expires_at: ISO 8601 timestamp when the file will be auto-deleted (temp writes only).
    """

    gcs_path: str
    drive_path: str
    path: str
    expires_at: Optional[str] = None


class DefiniteDriveClient:
    """Write files to Definite Drive.

    Initialization:
    >>> client = DefiniteClient("MY_API_KEY")
    >>> drive = client.get_drive_client()

    Writing a file with an explicit path:
    >>> result = drive.write_file(b"hello", path="notes/greeting.txt")
    >>> print(result.gcs_path)

    Writing a temporary file (auto-deleted after ttl_days):
    >>> result = drive.write_temporary_file(parquet_bytes, name="events.parquet")
    >>> sql_client.execute(
    ...     f"CREATE TABLE LAKE.MY_SCHEMA.events AS "
    ...     f"SELECT * FROM read_parquet('{result.gcs_path}')"
    ... )
    """

    def __init__(self, api_key: str, api_url: str):
        self._api_key = api_key
        self._api_url = api_url.rstrip("/")

    def write_file(
        self,
        data: WritableData,
        path: str,
    ) -> DriveWriteResult:
        """Write data to a specific path in Drive. The file persists until explicitly deleted."""
        instructions = self._get_upload_instructions({"path": path})
        self._put_bytes(instructions["upload_url"], instructions["headers"], data)
        return self._result_from(instructions)

    def write_temporary_file(
        self,
        data: WritableData,
        name: Optional[str] = None,
        *,
        ttl_days: int = 7,
    ) -> DriveWriteResult:
        """Write data to a temporary path. Auto-deleted after ttl_days (1..30).

        The server chooses the destination path under `_tmp/<date>/<uuid>/<name>`.
        Use the returned `gcs_path` to ingest via SQL before the TTL elapses.
        """
        instructions = self._get_upload_instructions(
            {
                "temporary": True,
                "ttl_days": ttl_days,
                "filename_hint": name,
            }
        )
        self._put_bytes(instructions["upload_url"], instructions["headers"], data)
        return self._result_from(instructions)

    def _get_upload_instructions(self, body: dict) -> dict:
        resp = requests.post(
            self._api_url + UPLOAD_URL_ENDPOINT,
            headers={"Authorization": "Bearer " + self._api_key},
            json=body,
        )
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def _put_bytes(upload_url: str, headers: dict, data: WritableData) -> None:
        stream, close_after = _as_stream(data)
        try:
            put = requests.put(upload_url, data=stream, headers=headers)
            put.raise_for_status()
        finally:
            if close_after:
                stream.close()

    @staticmethod
    def _result_from(instructions: dict) -> DriveWriteResult:
        gcs_path: str = instructions["gcs_path"]
        # Strip bucket prefix to recover the drive-relative path.
        # Format: gs://<bucket>/<team_id>/drive/<rel_path>
        try:
            rel_path = gcs_path.split("/drive/", 1)[1]
        except IndexError:
            rel_path = gcs_path
        return DriveWriteResult(
            gcs_path=gcs_path,
            drive_path=instructions["drive_path"],
            path=rel_path,
            expires_at=instructions.get("expires_at"),
        )


def _as_stream(data: WritableData) -> tuple[BinaryIO, bool]:
    """Normalize input into a file-like object for requests.put(data=...).

    Returns (stream, close_after) where close_after indicates whether this function
    opened the stream and is responsible for closing it.
    """
    if isinstance(data, bytes):
        return io.BytesIO(data), True
    if isinstance(data, str):
        return io.BytesIO(data.encode("utf-8")), True
    if isinstance(data, os.PathLike) or (isinstance(data, str) and os.path.isfile(data)):
        return open(os.fspath(data), "rb"), True
    # Assume a readable file-like object; caller owns its lifecycle.
    return data, False  # type: ignore[return-value]
