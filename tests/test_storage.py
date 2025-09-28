from __future__ import annotations

from datetime import datetime

import pytest

from personal_finance_app.config import S3Config
from personal_finance_app import storage
from personal_finance_app.storage import S3Storage


class _FixedDateTime:
    @staticmethod
    def utcnow() -> datetime:
        return datetime(2023, 1, 2, 3, 4, 5)


def test_write_csv(monkeypatch: pytest.MonkeyPatch) -> None:
    class DummyS3:
        def __init__(self) -> None:
            self.calls: list[dict[str, object]] = []

        def put_object(self, **kwargs) -> None:  # type: ignore[no-untyped-def]
            self.calls.append(kwargs)

    monkeypatch.setattr(storage, "datetime", _FixedDateTime)

    client = DummyS3()
    store = S3Storage(S3Config(bucket="finance-bucket", prefix="exports"), s3_client=client)
    metadata = store.write_csv(
        dataset="accounts",
        rows=[{"account_id": "123", "balance": 100}],
    )

    assert metadata.bucket == "finance-bucket"
    assert metadata.key == "exports/accounts_20230102T030405Z.csv"
    assert metadata.record_count == 1
    assert len(client.calls) == 1
    call = client.calls[0]
    assert call["Bucket"] == "finance-bucket"
    assert call["Key"] == "exports/accounts_20230102T030405Z.csv"
    assert call["Body"].decode("utf-8").splitlines() == ["account_id,balance", "123,100"]
