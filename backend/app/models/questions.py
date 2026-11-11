import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


class QuestionStatus(str, Enum):
    """Public lifecycle state for a community question."""

    PENDING = "pending"
    AWAITING_REVIEW = "awaiting_review"
    RESPONDED = "responded"


class QuestionAnalysisStatus(str, Enum):
    """Outcome of one immutable analysis run."""

    PENDING = "pending"
    READY = "ready"
    UNAVAILABLE = "unavailable"
    FAILED = "failed"


class ProfessionalResponseStatus(str, Enum):
    """Publication state for a professional answer."""

    PUBLISHED = "published"
    SUPERSEDED = "superseded"


class VaccineQuestion(Base):
    __tablename__ = "vaccine_questions"
    __table_args__ = (
        CheckConstraint(
            "language IN ('rw', 'en')",
            name="ck_vaccine_questions_language",
        ),
        CheckConstraint(
            "status IN ('pending', 'awaiting_review', 'responded')",
            name="ck_vaccine_questions_status",
        ),
        CheckConstraint(
            "length(content) BETWEEN 1 AND 10000 AND length(trim(content)) > 0",
            name="ck_vaccine_questions_content_valid",
        ),
        Index(
            "ix_vaccine_questions_owner_created_at",
            "asked_by_user_id",
            "created_at",
        ),
        Index(
            "ix_vaccine_questions_review_queue",
            "status",
            "created_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    asked_by_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(8), nullable=False)
    topic: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32),
        default=QuestionStatus.PENDING.value,
        server_default=QuestionStatus.PENDING.value,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
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

    analyses: Mapped[list["QuestionAnalysis"]] = relationship(
        back_populates="question",
        passive_deletes=True,
    )
    professional_responses: Mapped[list["ProfessionalResponse"]] = relationship(
        back_populates="question",
        passive_deletes=True,
    )


class QuestionAnalysis(Base):
    __tablename__ = "question_analyses"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'ready', 'unavailable', 'failed')",
            name="ck_question_analyses_status",
        ),
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="ck_question_analyses_confidence",
        ),
        Index(
            "ix_question_analyses_question_created_at",
            "question_id",
            "created_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("vaccine_questions.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    provider: Mapped[str | None] = mapped_column(String(255), nullable=True)
    model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    dataset_version: Mapped[str | None] = mapped_column(String(255), nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    explanation_method: Mapped[str | None] = mapped_column(String(255), nullable=True)
    confidence: Mapped[float | None] = mapped_column(nullable=True)
    limitations: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
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

    question: Mapped[VaccineQuestion] = relationship(
        back_populates="analyses",
    )


class ProfessionalResponse(Base):
    __tablename__ = "professional_responses"
    __table_args__ = (
        CheckConstraint(
            "status IN ('published', 'superseded')",
            name="ck_professional_responses_status",
        ),
        Index(
            "ix_professional_responses_question_status_created_at",
            "question_id",
            "status",
            "created_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("vaccine_questions.id", ondelete="CASCADE"),
        nullable=False,
    )
    professional_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    response: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    question: Mapped[VaccineQuestion] = relationship(
        back_populates="professional_responses",
    )
