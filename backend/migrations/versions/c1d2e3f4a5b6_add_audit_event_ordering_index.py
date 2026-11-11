"""add an ordering index for audit event pagination

Revision ID: c1d2e3f4a5b6
Revises: b7d2e9f4c613
Create Date: 2026-11-05

"""

from collections.abc import Sequence

from alembic import op

revision: str = "c1d2e3f4a5b6"
down_revision: str | None = "b7d2e9f4c613"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_audit_events_created_at_id",
        "audit_events",
        ["created_at", "id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_audit_events_created_at_id",
        table_name="audit_events",
    )
