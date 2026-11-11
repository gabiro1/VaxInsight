import sys
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from app import cli
from app.core.config import settings
from app.database.database import SessionLocal
from app.models.auth import RateLimitBucket
from app.services.rate_limit import _bucket_key, enforce_rate_limit
from app.services.rate_limit_cleanup import (
    RateLimitCleanupError,
    cleanup_expired_rate_limit_buckets,
)
from sqlalchemy import delete, text
from sqlalchemy.exc import SQLAlchemyError
from starlette.requests import Request

pytestmark = pytest.mark.integration


def _request(client_host: str = "198.51.100.10") -> Request:
    return Request(
        {
            "type": "http",
            "client": (client_host, 50000),
        }
    )


def _bucket_key_for_test() -> str:
    return f"cleanup-test:{uuid4()}"


def _insert_bucket(db, key: str, window_started_at: datetime) -> None:
    db.add(
        RateLimitBucket(
            bucket_key=key,
            window_started_at=window_started_at,
            request_count=1,
        )
    )
    db.commit()


def _delete_buckets(keys: set[str]) -> None:
    db = SessionLocal()
    try:
        db.execute(delete(RateLimitBucket).where(RateLimitBucket.bucket_key.in_(keys)))
        db.commit()
    finally:
        db.close()


@pytest.fixture
def cleanup_database():
    db = SessionLocal()
    keys: set[str] = set()
    try:
        cleanup_expired_rate_limit_buckets(
            db,
            batch_size=1000,
            max_batches=100,
        )
        yield db, keys
    finally:
        db.close()
        _delete_buckets(keys)


def test_expired_buckets_are_deleted_and_active_buckets_remain(cleanup_database):
    db, keys = cleanup_database
    now = datetime.now(UTC)
    expired_key = _bucket_key_for_test()
    active_key = _bucket_key_for_test()
    keys.update({expired_key, active_key})

    _insert_bucket(db, expired_key, now - timedelta(seconds=120))
    _insert_bucket(db, active_key, now - timedelta(seconds=1))

    deleted_count = cleanup_expired_rate_limit_buckets(
        db,
        window_seconds=60,
        batch_size=10,
        max_batches=10,
    )

    assert deleted_count == 1
    assert db.get(RateLimitBucket, expired_key) is None
    assert db.get(RateLimitBucket, active_key) is not None


def test_bucket_at_expiration_boundary_is_expired(cleanup_database):
    db, keys = cleanup_database
    key = _bucket_key_for_test()
    keys.add(key)

    _insert_bucket(
        db,
        key,
        datetime.now(UTC) - timedelta(seconds=60),
    )

    deleted_count = cleanup_expired_rate_limit_buckets(
        db,
        window_seconds=60,
        batch_size=10,
        max_batches=10,
    )

    # The enforcement SQL uses <=, so the exact boundary is expired.
    assert deleted_count == 1
    assert db.get(RateLimitBucket, key) is None


def test_cleanup_returns_zero_when_no_expired_records_exist(cleanup_database):
    db, keys = cleanup_database
    key = _bucket_key_for_test()
    keys.add(key)
    _insert_bucket(db, key, datetime.now(UTC))

    assert (
        cleanup_expired_rate_limit_buckets(
            db,
            window_seconds=60,
            batch_size=10,
            max_batches=10,
        )
        == 0
    )
    assert db.get(RateLimitBucket, key) is not None


def test_cleanup_respects_batch_limit_and_is_idempotent(cleanup_database):
    db, keys = cleanup_database
    now = datetime.now(UTC) - timedelta(seconds=120)
    for _ in range(5):
        key = _bucket_key_for_test()
        keys.add(key)
        _insert_bucket(db, key, now)

    assert (
        cleanup_expired_rate_limit_buckets(
            db,
            window_seconds=60,
            batch_size=2,
            max_batches=1,
        )
        == 2
    )
    assert (
        db.query(RateLimitBucket).filter(RateLimitBucket.bucket_key.in_(keys)).count()
        == 3
    )

    assert (
        cleanup_expired_rate_limit_buckets(
            db,
            window_seconds=60,
            batch_size=2,
            max_batches=1,
        )
        == 2
    )
    assert (
        cleanup_expired_rate_limit_buckets(
            db,
            window_seconds=60,
            batch_size=2,
            max_batches=1,
        )
        == 1
    )
    assert (
        cleanup_expired_rate_limit_buckets(
            db,
            window_seconds=60,
            batch_size=2,
            max_batches=1,
        )
        == 0
    )


def test_cleanup_does_not_remove_bucket_reset_by_active_enforcement(
    cleanup_database,
    monkeypatch,
):
    db, keys = cleanup_database
    key = _bucket_key("cleanup-test", _request(), "cleanup@example.com")
    keys.add(key)
    _insert_bucket(db, key, datetime.now(UTC) - timedelta(seconds=120))
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", True)

    enforce_rate_limit(
        db,
        _request(),
        scope="cleanup-test",
        limit=10,
        identity="cleanup@example.com",
    )
    deleted_count = cleanup_expired_rate_limit_buckets(
        db,
        window_seconds=60,
        batch_size=10,
        max_batches=10,
    )

    bucket = db.get(RateLimitBucket, key)
    assert deleted_count == 0
    assert bucket is not None
    assert bucket.request_count == 1


def test_expiration_index_exists(cleanup_database):
    db, _ = cleanup_database
    index_exists = db.scalar(
        text(
            """
            SELECT 1
            FROM pg_indexes
            WHERE tablename = 'rate_limit_buckets'
              AND indexname =
                  'ix_rate_limit_buckets_window_started_at_bucket_key'
            """
        )
    )

    assert index_exists == 1


def test_cleanup_wraps_database_failures():
    db = SessionLocal()
    original_execute = db.execute

    def raise_database_error(*args, **kwargs):
        raise SQLAlchemyError("database unavailable")

    db.execute = raise_database_error
    try:
        with pytest.raises(RateLimitCleanupError):
            cleanup_expired_rate_limit_buckets(db, batch_size=1, max_batches=1)
    finally:
        db.execute = original_execute
        db.close()


def test_cli_cleanup_reports_deleted_count(monkeypatch, capsys):
    fake_db = MagicMock()
    monkeypatch.setattr(cli, "SessionLocal", lambda: fake_db)
    monkeypatch.setattr(
        cli,
        "cleanup_expired_rate_limit_buckets",
        lambda db, batch_size=None, max_batches=None: 7,
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["app.cli", "cleanup-rate-limits", "--batch-size", "25"],
    )

    cli.main()

    assert capsys.readouterr().out == "Expired rate-limit buckets removed: 7\n"
    fake_db.close.assert_called_once()


def test_cli_cleanup_returns_failure_status_without_exposing_keys(monkeypatch, capsys):
    fake_db = MagicMock()
    monkeypatch.setattr(cli, "SessionLocal", lambda: fake_db)
    monkeypatch.setattr(
        cli,
        "cleanup_expired_rate_limit_buckets",
        MagicMock(side_effect=RateLimitCleanupError),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["app.cli", "cleanup-rate-limits"],
    )

    with pytest.raises(SystemExit) as error:
        cli.main()

    assert error.value.code == 1
    assert "Rate-limit cleanup failed" in capsys.readouterr().err
    fake_db.close.assert_called_once()
