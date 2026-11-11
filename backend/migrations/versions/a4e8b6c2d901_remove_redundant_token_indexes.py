"""remove redundant token indexes

Revision ID: a4e8b6c2d901
Revises: 9c3f4f7a1b22
Create Date: 2026-11-04

"""

from collections.abc import Sequence

from alembic import op

revision: str = "a4e8b6c2d901"
down_revision: str | None = "9c3f4f7a1b22"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


TOKEN_INDEXES = (
    ("ix_account_invitations_token_hash", "account_invitations"),
    ("ix_refresh_sessions_token_hash", "refresh_sessions"),
    ("ix_password_reset_tokens_token_hash", "password_reset_tokens"),
    ("ix_email_verification_tokens_token_hash", "email_verification_tokens"),
)


def upgrade() -> None:
    for index_name, table_name in TOKEN_INDEXES:
        op.drop_index(index_name, table_name=table_name)


def downgrade() -> None:
    for index_name, table_name in TOKEN_INDEXES:
        op.create_index(index_name, table_name, ["token_hash"])
