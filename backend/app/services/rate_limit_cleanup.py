from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings


class RateLimitCleanupError(Exception):
    """Raised when expired rate-limit buckets cannot be removed."""


_DELETE_EXPIRED_BUCKETS = text(
    """
    WITH expired AS (
        SELECT bucket_key
        FROM rate_limit_buckets
        WHERE window_started_at
            <= now() - (:window_seconds * interval '1 second')
        ORDER BY window_started_at, bucket_key
        LIMIT :batch_size
        FOR UPDATE SKIP LOCKED
    )
    DELETE FROM rate_limit_buckets AS bucket
    USING expired
    WHERE bucket.bucket_key = expired.bucket_key
      AND bucket.window_started_at
          <= now() - (:window_seconds * interval '1 second')
    RETURNING bucket.bucket_key
    """
)


def cleanup_expired_rate_limit_buckets(
    db: Session,
    *,
    window_seconds: int | None = None,
    batch_size: int | None = None,
    max_batches: int | None = None,
) -> int:
    """Delete expired buckets in bounded, independently committed batches."""

    window_seconds = (
        settings.RATE_LIMIT_WINDOW_SECONDS if window_seconds is None else window_seconds
    )
    batch_size = (
        settings.RATE_LIMIT_CLEANUP_BATCH_SIZE if batch_size is None else batch_size
    )
    max_batches = (
        settings.RATE_LIMIT_CLEANUP_MAX_BATCHES if max_batches is None else max_batches
    )

    if window_seconds <= 0 or batch_size <= 0 or max_batches <= 0:
        raise ValueError("Cleanup limits and window_seconds must be positive")

    deleted_count = 0

    try:
        for _ in range(max_batches):
            result = db.execute(
                _DELETE_EXPIRED_BUCKETS,
                {
                    "window_seconds": window_seconds,
                    "batch_size": batch_size,
                },
            )
            deleted_in_batch = len(result.fetchall())
            db.commit()
            deleted_count += deleted_in_batch

            if deleted_in_batch < batch_size:
                break
    except SQLAlchemyError as error:
        db.rollback()
        raise RateLimitCleanupError(
            "Unable to remove expired rate-limit buckets"
        ) from error

    return deleted_count
