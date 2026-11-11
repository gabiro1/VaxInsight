import uuid
from datetime import date, datetime
from enum import Enum

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base


class AssignmentStatus(str, Enum):
    """Lifecycle of a narrative Health Expert assignment."""

    ACTIVE = "active"
    REVOKED = "revoked"


class ReviewStatus(str, Enum):
    """Workflow state for the current assignment."""

    PENDING = "pending"
    IN_REVIEW = "in_review"
    REVIEWED = "reviewed"
    REQUIRES_ESCALATION = "requires_escalation"


class ReviewOutcome(str, Enum):
    """Neutral human-review outcomes, not claims of medical truth."""

    NEEDS_FURTHER_REVIEW = "needs_further_review"
    EVIDENCE_SUPPORTS_CLAIM = "evidence_supports_claim"
    EVIDENCE_DOES_NOT_SUPPORT_CLAIM = "evidence_does_not_support_claim"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class NarrativeAssignment(Base):
    __tablename__ = "narrative_assignments"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'revoked')",
            name="ck_narrative_assignments_status",
        ),
        CheckConstraint(
            "review_status IN ('pending', 'in_review', 'reviewed', 'requires_escalation')",
            name="ck_narrative_assignments_review_status",
        ),
        Index(
            "ix_narrative_assignments_reviewer_status",
            "reviewer_id",
            "status",
        ),
        Index(
            "uq_narrative_assignments_active_narrative",
            "narrative_id",
            unique=True,
            postgresql_where=text("status = 'active'"),
            sqlite_where=text("status = 'active'"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    narrative_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("narratives.id"),
        nullable=False,
    )
    reviewer_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    assigned_by_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default=AssignmentStatus.ACTIVE.value,
        server_default=AssignmentStatus.ACTIVE.value,
        nullable=False,
    )
    review_status: Mapped[str] = mapped_column(
        String(32),
        default=ReviewStatus.PENDING.value,
        server_default=ReviewStatus.PENDING.value,
        nullable=False,
    )
    assigned_at: Mapped[datetime] = mapped_column(
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
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    revoked_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )
    revoked_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )


class NarrativeReview(Base):
    __tablename__ = "narrative_reviews"
    __table_args__ = (
        CheckConstraint(
            "outcome IN ("
            "'needs_further_review', "
            "'evidence_supports_claim', "
            "'evidence_does_not_support_claim', "
            "'insufficient_evidence'"
            ")",
            name="ck_narrative_reviews_outcome",
        ),
        Index(
            "ix_narrative_reviews_assignment_reviewed_at",
            "assignment_id",
            "reviewed_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    assignment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("narrative_assignments.id"),
        nullable=False,
    )
    narrative_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("narratives.id"),
        nullable=False,
    )
    reviewer_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    outcome: Mapped[str] = mapped_column(String(64), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class ReviewEvidenceReference(Base):
    __tablename__ = "review_evidence_references"
    __table_args__ = (Index("ix_review_evidence_references_review_id", "review_id"),)

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    review_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("narrative_reviews.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_title: Mapped[str] = mapped_column(String(255), nullable=False)
    publisher: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    publication_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    accessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    relevance: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
