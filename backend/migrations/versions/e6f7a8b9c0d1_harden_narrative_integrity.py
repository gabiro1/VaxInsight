"""add narrative content and revision integrity constraints

Revision ID: e6f7a8b9c0d1
Revises: e5f6a7b8c9d0
Create Date: 2026-11-05

"""

from collections.abc import Sequence

from alembic import op

revision: str = "e6f7a8b9c0d1"
down_revision: str | None = "e5f6a7b8c9d0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_narratives_content_valid",
        "narratives",
        "length(content) BETWEEN 1 AND 10000 AND length(trim(content)) > 0",
    )
    op.create_check_constraint(
        "ck_narratives_version_positive",
        "narratives",
        "version >= 1",
    )
    op.create_check_constraint(
        "ck_narrative_revisions_content_valid",
        "narrative_revisions",
        "length(content) BETWEEN 1 AND 10000 AND length(trim(content)) > 0",
    )
    op.create_check_constraint(
        "ck_narrative_revisions_version_positive",
        "narrative_revisions",
        "version >= 1",
    )
    op.create_check_constraint(
        "ck_narrative_revisions_action",
        "narrative_revisions",
        "action IN ('created', 'updated')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_narrative_revisions_action",
        "narrative_revisions",
        type_="check",
    )
    op.drop_constraint(
        "ck_narrative_revisions_version_positive",
        "narrative_revisions",
        type_="check",
    )
    op.drop_constraint(
        "ck_narrative_revisions_content_valid",
        "narrative_revisions",
        type_="check",
    )
    op.drop_constraint(
        "ck_narratives_version_positive",
        "narratives",
        type_="check",
    )
    op.drop_constraint(
        "ck_narratives_content_valid",
        "narratives",
        type_="check",
    )
