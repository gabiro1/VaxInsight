"""add community registration profile fields

Revision ID: f1a2b3c4d5e6
Revises: e6f7a8b9c0d1
Create Date: 2026-11-05

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f1a2b3c4d5e6"
down_revision: str | None = "e6f7a8b9c0d1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("full_name", sa.String(length=255), nullable=True),
    )

    op.drop_constraint("ck_users_role", "users", type_="check")
    op.create_check_constraint(
        "ck_users_role",
        "users",
        "role IS NULL OR role IN ('community_member', 'chw', 'reviewer', 'administrator')",
    )
    op.create_check_constraint(
        "ck_users_full_name_valid",
        "users",
        "full_name IS NULL OR (length(full_name) BETWEEN 1 AND 255 AND length(trim(full_name)) > 0)",
    )
    op.create_check_constraint(
        "ck_users_community_name_required",
        "users",
        "role IS NULL OR role <> 'community_member' OR (full_name IS NOT NULL AND length(trim(full_name)) > 0)",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_users_community_name_required",
        "users",
        type_="check",
    )
    op.drop_constraint("ck_users_full_name_valid", "users", type_="check")
    op.drop_constraint("ck_users_role", "users", type_="check")
    op.create_check_constraint(
        "ck_users_role",
        "users",
        "role IS NULL OR role IN ('chw', 'reviewer', 'administrator')",
    )
    op.drop_column("users", "full_name")
