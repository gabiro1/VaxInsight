"""enforce normalized user email storage

Revision ID: b7d2e9f4c613
Revises: a4e8b6c2d901
Create Date: 2026-11-04

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b7d2e9f4c613"
down_revision: str | None = "a4e8b6c2d901"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(sa.text("UPDATE users SET email = lower(email)"))
    op.create_check_constraint(
        "ck_users_email_normalized",
        "users",
        "email = lower(email)",
    )


def downgrade() -> None:
    op.drop_constraint("ck_users_email_normalized", "users", type_="check")
