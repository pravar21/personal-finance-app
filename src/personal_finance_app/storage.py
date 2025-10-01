"""Utilities for writing structured data to AWS S3."""
from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Mapping

from typing import Protocol, runtime_checkable

try:  # pragma: no cover - boto3 is available in AWS Lambda but may be absent locally.
    import boto3
except ModuleNotFoundError:  # pragma: no cover - exercised in unit tests
    boto3 = None  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency for type checking only.
    from botocore.client import BaseClient
except ModuleNotFoundError:  # pragma: no cover - used in local testing environments
    @runtime_checkable
    class BaseClient(Protocol):  # type: ignore[no-redef]
        def put_object(self, **kwargs: object) -> object:  # pragma: no cover - protocol only
            ...

from .config import S3Config


@dataclass
class S3ObjectMetadata:
    """Metadata describing where a CSV payload was persisted."""

    bucket: str
    key: str
    record_count: int

    def to_dict(self) -> Mapping[str, object]:
        return {"bucket": self.bucket, "key": self.key, "record_count": self.record_count}


class S3Storage:
    """Handles writing CSV exports to Amazon S3."""

    def __init__(self, config: S3Config, *, s3_client: BaseClient | None = None) -> None:
        self._config = config
        if s3_client is not None:
            self._s3 = s3_client
        else:
            if boto3 is None:  # pragma: no cover - defensive guard for local execution
                raise RuntimeError("boto3 is required to create an S3 client")
            self._s3 = boto3.client("s3")

    def write_csv(self, *, dataset: str, rows: Iterable[Mapping[str, object]]) -> S3ObjectMetadata:
        buffer = io.StringIO()
        writer = None
        count = 0
        for row in rows:
            if writer is None:
                writer = csv.DictWriter(buffer, fieldnames=list(row.keys()))
                writer.writeheader()
            writer.writerow({key: _stringify(value) for key, value in row.items()})
            count += 1
        if writer is None:
            # Ensure we still write an empty file with just a header row to make downstream
            # processing predictable.
            buffer.write("id\n")
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        key = f"{self._config.prefix}/{dataset}_{timestamp}.csv"
        body = buffer.getvalue().encode("utf-8")
        self._s3.put_object(Bucket=self._config.bucket, Key=key, Body=body)
        return S3ObjectMetadata(bucket=self._config.bucket, key=key, record_count=count)


def _stringify(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, (str, int, float)):
        return str(value)
    return json.dumps(value, default=str)
