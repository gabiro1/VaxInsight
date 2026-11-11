"""add account lifecycle and authentication records

Revision ID: 9c3f4f7a1b22
Revises: 4ab5cfdb6e2d
Create Date: 2026-11-04

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "9c3f4f7a1b22"
down_revision: str | None = "4ab5cfdb6e2d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("status", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("role", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("password_changed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute(
        sa.text(
            """
            UPDATE users
            SET status = CASE
                WHEN is_active THEN 'active'
                ELSE 'deactivated'
            END
            """
        )
    )
    op.alter_column(
        "users",
        "status",
        existing_type=sa.String(length=32),
        nullable=False,
        server_default="active",
    )
    op.create_check_constraint(
        "ck_users_status",
        "users",
        "status IN ('pending', 'active', 'suspended', 'deactivated', 'deleted')",
    )
    op.create_check_constraint(
        "ck_users_role",
        "users",
        "role IS NULL OR role IN ('chw', 'reviewer', 'administrator')",
    )

    op.create_table(
        "account_invitations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("invited_by_id", sa.Uuid(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["invited_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
        sa.CheckConstraint(
            "role IN ('chw', 'reviewer', 'administrator')",
            name="ck_account_invitations_role",
        ),
    )
    op.create_index(
        "ix_account_invitations_email",
        "account_invitations",
        ["email"],
    )
    op.create_index(
        "ix_account_invitations_token_hash",
        "account_invitations",
        ["token_hash"],
    )

    op.create_table(
        "refresh_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("family_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("ix_refresh_sessions_user_id", "refresh_sessions", ["user_id"])
    op.create_index(
        "ix_refresh_sessions_token_hash",
        "refresh_sessions",
        ["token_hash"],
    )

    for table_name in ("password_reset_tokens", "email_verification_tokens"):
        op.create_table(
            table_name,
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("user_id", sa.Uuid(), nullable=False),
            sa.Column("token_hash", sa.String(length=64), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("token_hash"),
        )
        op.create_index(f"ix_{table_name}_user_id", table_name, ["user_id"])
        op.create_index(
            f"ix_{table_name}_token_hash",
            table_name,
            ["token_hash"],
        )

    op.create_table(
        "audit_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("actor_user_id", sa.Uuid(), nullable=True),
        sa.Column("target_user_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("outcome", sa.String(length=32), nullable=False),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["target_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_events_actor_user_id", "audit_events", ["actor_user_id"])
    op.create_index(
        "ix_audit_events_target_user_id", "audit_events", ["target_user_id"]
    )
    op.create_index("ix_audit_events_action", "audit_events", ["action"])

    op.create_table(
        "rate_limit_buckets",
        sa.Column("bucket_key", sa.String(length=255), nullable=False),
        sa.Column("window_started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("request_count", sa.Integer(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("bucket_key"),
    )


def downgrade() -> None:
    op.drop_table("rate_limit_buckets")

    op.drop_index("ix_audit_events_action", table_name="audit_events")
    op.drop_index("ix_audit_events_target_user_id", table_name="audit_events")
    op.drop_index("ix_audit_events_actor_user_id", table_name="audit_events")
    op.drop_table("audit_events")

    for table_name in ("email_verification_tokens", "password_reset_tokens"):
        op.drop_index(f"ix_{table_name}_token_hash", table_name=table_name)
        op.drop_index(f"ix_{table_name}_user_id", table_name=table_name)
        op.drop_table(table_name)

    op.drop_index("ix_refresh_sessions_token_hash", table_name="refresh_sessions")
    op.drop_index("ix_refresh_sessions_user_id", table_name="refresh_sessions")
    op.drop_table("refresh_sessions")

    op.drop_index(
        "ix_account_invitations_token_hash",
        table_name="account_invitations",
    )
    op.drop_index("ix_account_invitations_email", table_name="account_invitations")
    op.drop_table("account_invitations")

    op.drop_constraint("ck_users_role", "users", type_="check")
    op.drop_constraint("ck_users_status", "users", type_="check")
    op.drop_column("users", "last_login_at")
    op.drop_column("users", "password_changed_at")
    op.drop_column("users", "email_verified_at")
    op.drop_column("users", "role")
    op.drop_column("users", "status")
