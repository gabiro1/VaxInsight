import hashlib

from fastapi import Request
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings


class RateLimitExceeded(Exception):
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__("Rate limit exceeded")


class RateLimitUnavailable(Exception):
    """Raised when the shared rate-limit store cannot be reached."""


def _bucket_key(scope: str, request: Request, identity: str | None) -> str:
    if identity is not None:
        # Keep account-bound limits stable when a client changes networks.
        material = f"{scope}|identity|{identity}"
    else:
        ip_address = request.client.host if request.client else "unknown"
        material = f"{scope}|ip|{ip_address}"

    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()

    return f"auth:{scope}:{digest}"


def enforce_rate_limit(
    db: Session,
    request: Request,
    *,
    scope: str,
    limit: int,
    identity: str | None = None,
) -> None:
    """
    Apply a PostgreSQL-backed fixed-window rate limit.

    Requests are counted in a shared PostgreSQL table, so the
    limit applies across multiple application instances.
    """

    if not settings.RATE_LIMIT_ENABLED:
        return

    key = _bucket_key(scope, request, identity)

    statement = text(
        """
        INSERT INTO rate_limit_buckets (
            bucket_key,
            window_started_at,
            request_count,
            updated_at
        )
        VALUES (
            :bucket_key,
            now(),
            1,
            now()
        )
        ON CONFLICT (bucket_key) DO UPDATE
        SET
            window_started_at = CASE
                WHEN rate_limit_buckets.window_started_at
                    <= now() - (:window_seconds * interval '1 second')
                THEN now()
                ELSE rate_limit_buckets.window_started_at
            END,

            request_count = CASE
                WHEN rate_limit_buckets.window_started_at
                    <= now() - (:window_seconds * interval '1 second')
                THEN 1
                ELSE rate_limit_buckets.request_count + 1
            END,

            updated_at = now()

        RETURNING
            request_count,
            GREATEST(
                1,
                CEIL(
                    EXTRACT(
                        EPOCH FROM (
                            window_started_at
                            + (:window_seconds * interval '1 second')
                            - now()
                        )
                    )
                )
            )::integer AS retry_after
        """
    )

    try:
        result = db.execute(
            statement,
            {
                "bucket_key": key,
                "window_seconds": settings.RATE_LIMIT_WINDOW_SECONDS,
            },
        ).one()

        request_count, retry_after = result

        # Persist the updated request count before raising
        # a rate-limit exception.
        db.commit()

    except SQLAlchemyError as error:
        db.rollback()
        raise RateLimitUnavailable from error

    if request_count > limit:
        raise RateLimitExceeded(retry_after)
