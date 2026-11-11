import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base


class NarrativeStatus(str, Enum):
    """Neutral lifecycle state available before Health Expert workflow approval."""

    SUBMITTED = "submitted"


class NarrativeRevisionAction(str, Enum):
    """Changes captured in the owner-visible narrative history."""

    CREATED = "created"
    UPDATED = "updated"


class Narrative(Base):
    __tablename__ = "narratives"
    __table_args__ = (
        CheckConstraint(
            "length(content) BETWEEN 1 AND 10000 AND length(trim(content)) > 0",
            name="ck_narratives_content_valid",
        ),
        CheckConstraint("version >= 1", name="ck_narratives_version_positive"),
        Index(
            "ix_narratives_submitted_by_submitted_at",
            "submitted_by_id",
            "submitted_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    submitted_by_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        default=NarrativeStatus.SUBMITTED.value,
        server_default=NarrativeStatus.SUBMITTED.value,
        nullable=False,
    )
    version: Mapped[int] = mapped_column(
        Integer,
        default=1,
        server_default="1",
        nullable=False,
    )
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class NarrativeRevision(Base):
    __tablename__ = "narrative_revisions"
    __table_args__ = (
        CheckConstraint(
            "length(content) BETWEEN 1 AND 10000 AND length(trim(content)) > 0",
            name="ck_narrative_revisions_content_valid",
        ),
        CheckConstraint(
            "version >= 1",
            name="ck_narrative_revisions_version_positive",
        ),
        CheckConstraint(
            "action IN ('created', 'updated')",
            name="ck_narrative_revisions_action",
        ),
        UniqueConstraint(
            "narrative_id",
            "version",
            name="uq_narrative_revisions_narrative_version",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    narrative_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("narratives.id", ondelete="CASCADE"),
        nullable=False,
    )
    changed_by_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
