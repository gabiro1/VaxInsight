"""add official vaccine content and supervisor question workflow

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-11-10

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b8c9d0e1f2a3"
down_revision: str | None = "a7b8c9d0e1f2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "vaccine_sources",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("authority", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("jurisdiction", sa.String(length=128), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
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
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "authority",
            "name",
            "url",
            "jurisdiction",
            name="uq_vaccine_sources_identity",
        ),
        sa.CheckConstraint(
            "length(trim(authority)) > 0",
            name="ck_vaccine_sources_authority_valid",
        ),
        sa.CheckConstraint(
            "length(trim(name)) > 0",
            name="ck_vaccine_sources_name_valid",
        ),
        sa.CheckConstraint(
            "length(trim(jurisdiction)) > 0",
            name="ck_vaccine_sources_jurisdiction_valid",
        ),
    )
    op.create_index(
        "ix_vaccine_sources_created_by_user_id",
        "vaccine_sources",
        ["created_by_user_id"],
    )

    op.create_table(
        "vaccine_contents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("language", sa.String(length=8), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column(
            "status",
            sa.String(length=32),
            server_default="draft",
            nullable=False,
        ),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("approved_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
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
        sa.ForeignKeyConstraint(["source_id"], ["vaccine_sources.id"]),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["approved_by_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_id",
            "language",
            "category",
            "version",
            name="uq_vaccine_contents_source_language_category_version",
        ),
        sa.CheckConstraint(
            "language IN ('rw', 'en')",
            name="ck_vaccine_contents_language",
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'published')",
            name="ck_vaccine_contents_status",
        ),
        sa.CheckConstraint(
            "version >= 1",
            name="ck_vaccine_contents_version_positive",
        ),
        sa.CheckConstraint(
            "length(trim(title)) > 0",
            name="ck_vaccine_contents_title_valid",
        ),
    )
    op.create_index(
        "ix_vaccine_contents_published_language_category",
        "vaccine_contents",
        ["status", "language", "category"],
    )
    op.create_index(
        "ix_vaccine_contents_created_by_user_id",
        "vaccine_contents",
        ["created_by_user_id"],
    )
    op.create_index(
        "ix_vaccine_contents_approved_by_user_id",
        "vaccine_contents",
        ["approved_by_user_id"],
    )

    op.create_table(
        "vaccine_questions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("asked_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("language", sa.String(length=8), nullable=False),
        sa.Column("topic", sa.String(length=255), nullable=True),
        sa.Column(
            "status",
            sa.String(length=32),
            server_default="pending",
            nullable=False,
        ),
        sa.Column(
            "created_at",
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
        sa.ForeignKeyConstraint(
            ["asked_by_user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "language IN ('rw', 'en')",
            name="ck_vaccine_questions_language",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'awaiting_review', 'responded')",
            name="ck_vaccine_questions_status",
        ),
        sa.CheckConstraint(
            "length(content) BETWEEN 1 AND 10000 AND length(trim(content)) > 0",
            name="ck_vaccine_questions_content_valid",
        ),
    )
    op.create_index(
        "ix_vaccine_questions_owner_created_at",
        "vaccine_questions",
        ["asked_by_user_id", "created_at"],
    )
    op.create_index(
        "ix_vaccine_questions_review_queue",
        "vaccine_questions",
        ["status", "created_at"],
    )

    op.create_table(
        "question_analyses",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("question_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("provider", sa.String(length=255), nullable=True),
        sa.Column("model", sa.String(length=255), nullable=True),
        sa.Column("dataset_version", sa.String(length=255), nullable=True),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("answer", sa.Text(), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("explanation_method", sa.String(length=255), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("limitations", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
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
        sa.ForeignKeyConstraint(
            ["question_id"],
            ["vaccine_questions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "status IN ('pending', 'ready', 'unavailable', 'failed')",
            name="ck_question_analyses_status",
        ),
        sa.CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="ck_question_analyses_confidence",
        ),
    )
    op.create_index(
        "ix_question_analyses_question_created_at",
        "question_analyses",
        ["question_id", "created_at"],
    )

    op.create_table(
        "professional_responses",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("question_id", sa.Uuid(), nullable=False),
        sa.Column("professional_user_id", sa.Uuid(), nullable=True),
        sa.Column("response", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["question_id"],
            ["vaccine_questions.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["professional_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "status IN ('published', 'superseded')",
            name="ck_professional_responses_status",
        ),
    )
    op.create_index(
        "ix_professional_responses_question_status_created_at",
        "professional_responses",
        ["question_id", "status", "created_at"],
    )
    op.create_index(
        "ix_professional_responses_professional_user_id",
        "professional_responses",
        ["professional_user_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_professional_responses_professional_user_id",
        table_name="professional_responses",
    )
    op.drop_index(
        "ix_professional_responses_question_status_created_at",
        table_name="professional_responses",
    )
    op.drop_table("professional_responses")

    op.drop_index(
        "ix_question_analyses_question_created_at",
        table_name="question_analyses",
    )
    op.drop_table("question_analyses")

    op.drop_index(
        "ix_vaccine_questions_review_queue",
        table_name="vaccine_questions",
    )
    op.drop_index(
        "ix_vaccine_questions_owner_created_at",
        table_name="vaccine_questions",
    )
    op.drop_table("vaccine_questions")

    op.drop_index(
        "ix_vaccine_contents_approved_by_user_id",
        table_name="vaccine_contents",
    )
    op.drop_index(
        "ix_vaccine_contents_created_by_user_id",
        table_name="vaccine_contents",
    )
    op.drop_index(
        "ix_vaccine_contents_published_language_category",
        table_name="vaccine_contents",
    )
    op.drop_table("vaccine_contents")

    op.drop_index(
        "ix_vaccine_sources_created_by_user_id",
        table_name="vaccine_sources",
    )
    op.drop_table("vaccine_sources")
