"""add owner-scoped narrative records and revision history

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-11-05

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e5f6a7b8c9d0"
down_revision: str | None = "d4e5f6a7b8c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "narratives",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("submitted_by_id", sa.Uuid(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=32),
            server_default="submitted",
            nullable=False,
        ),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column(
            "submitted_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["submitted_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_narratives_submitted_by_submitted_at",
        "narratives",
        ["submitted_by_id", "submitted_at"],
    )

    op.create_table(
        "narrative_revisions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("narrative_id", sa.Uuid(), nullable=False),
        sa.Column("changed_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "changed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["changed_by_user_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["narrative_id"],
            ["narratives.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "narrative_id",
            "version",
            name="uq_narrative_revisions_narrative_version",
        ),
    )


def downgrade() -> None:
    op.drop_table("narrative_revisions")
    op.drop_index(
        "ix_narratives_submitted_by_submitted_at",
        table_name="narratives",
    )
    op.drop_table("narratives")
