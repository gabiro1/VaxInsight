"""add minimal narrative review workflow

Revision ID: a7b8c9d0e1f2
Revises: f1a2b3c4d5e6
Create Date: 2026-11-09

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a7b8c9d0e1f2"
down_revision: str | None = "f1a2b3c4d5e6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "narrative_assignments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("narrative_id", sa.Uuid(), nullable=False),
        sa.Column("reviewer_id", sa.Uuid(), nullable=False),
        sa.Column("assigned_by_user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=32),
            server_default="active",
            nullable=False,
        ),
        sa.Column(
            "review_status",
            sa.String(length=32),
            server_default="pending",
            nullable=False,
        ),
        sa.Column(
            "assigned_at",
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
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("revoked_reason", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["narrative_id"], ["narratives.id"]),
        sa.ForeignKeyConstraint(["reviewer_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["assigned_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["revoked_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "status IN ('active', 'revoked')",
            name="ck_narrative_assignments_status",
        ),
        sa.CheckConstraint(
            "review_status IN ('pending', 'in_review', 'reviewed', 'requires_escalation')",
            name="ck_narrative_assignments_review_status",
        ),
    )
    op.create_index(
        "ix_narrative_assignments_reviewer_status",
        "narrative_assignments",
        ["reviewer_id", "status"],
    )
    op.create_index(
        "uq_narrative_assignments_active_narrative",
        "narrative_assignments",
        ["narrative_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
    )

    op.create_table(
        "narrative_reviews",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("assignment_id", sa.Uuid(), nullable=False),
        sa.Column("narrative_id", sa.Uuid(), nullable=False),
        sa.Column("reviewer_id", sa.Uuid(), nullable=False),
        sa.Column("outcome", sa.String(length=64), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "reviewed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["assignment_id"], ["narrative_assignments.id"]),
        sa.ForeignKeyConstraint(["narrative_id"], ["narratives.id"]),
        sa.ForeignKeyConstraint(["reviewer_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "outcome IN ("
            "'needs_further_review', "
            "'evidence_supports_claim', "
            "'evidence_does_not_support_claim', "
            "'insufficient_evidence'"
            ")",
            name="ck_narrative_reviews_outcome",
        ),
    )
    op.create_index(
        "ix_narrative_reviews_assignment_reviewed_at",
        "narrative_reviews",
        ["assignment_id", "reviewed_at"],
    )

    op.create_table(
        "review_evidence_references",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("review_id", sa.Uuid(), nullable=False),
        sa.Column("source_title", sa.String(length=255), nullable=False),
        sa.Column("publisher", sa.String(length=255), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=True),
        sa.Column("publication_date", sa.Date(), nullable=True),
        sa.Column("accessed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("relevance", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["review_id"],
            ["narrative_reviews.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_review_evidence_references_review_id",
        "review_evidence_references",
        ["review_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_review_evidence_references_review_id",
        table_name="review_evidence_references",
    )
    op.drop_table("review_evidence_references")

    op.drop_index(
        "ix_narrative_reviews_assignment_reviewed_at",
        table_name="narrative_reviews",
    )
    op.drop_table("narrative_reviews")

    op.drop_index(
        "uq_narrative_assignments_active_narrative",
        table_name="narrative_assignments",
    )
    op.drop_index(
        "ix_narrative_assignments_reviewer_status",
        table_name="narrative_assignments",
    )
    op.drop_table("narrative_assignments")
