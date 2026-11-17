"""add notification preferences and Expo push devices

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
Create Date: 2026-11-16

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c9d0e1f2a3b4"
down_revision: str | None = "b8c9d0e1f2a3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "notification_preferences",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "frequency",
            sa.String(length=16),
            server_default="daily",
            nullable=False,
        ),
        sa.Column("last_notified_at", sa.DateTime(timezone=True), nullable=True),
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
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("user_id"),
        sa.CheckConstraint(
            "frequency IN ('hourly', 'daily', 'two_days', 'monthly')",
            name="ck_notification_preferences_frequency",
        ),
    )

    # Existing accounts receive the same default as newly initialized preferences.
    op.execute(
        sa.text(
            "INSERT INTO notification_preferences (user_id, frequency) "
            "SELECT id, 'daily' FROM users"
        )
    )

    op.create_table(
        "notification_devices",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("token", sa.String(length=255), nullable=False),
        sa.Column("platform", sa.String(length=32), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
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
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token", name="uq_notification_devices_token"),
    )
    op.create_index(
        "ix_notification_devices_user_id",
        "notification_devices",
        ["user_id"],
    )
    op.create_index(
        "ix_notification_devices_user_id_last_seen_at",
        "notification_devices",
        ["user_id", "last_seen_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_notification_devices_user_id_last_seen_at",
        table_name="notification_devices",
    )
    op.drop_index(
        "ix_notification_devices_user_id",
        table_name="notification_devices",
    )
    op.drop_table("notification_devices")
    op.drop_table("notification_preferences")
