"""add an expiration index for rate-limit bucket cleanup

Revision ID: d4e5f6a7b8c9
Revises: c1d2e3f4a5b6
Create Date: 2026-11-05

"""

from collections.abc import Sequence

from alembic import op

revision: str = "d4e5f6a7b8c9"
down_revision: str | None = "c1d2e3f4a5b6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_rate_limit_buckets_window_started_at_bucket_key",
        "rate_limit_buckets",
        ["window_started_at", "bucket_key"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_rate_limit_buckets_window_started_at_bucket_key",
        table_name="rate_limit_buckets",
    )
