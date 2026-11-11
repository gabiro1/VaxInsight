from datetime import UTC, date, datetime
from uuid import UUID

from pydantic import (
    AnyHttpUrl,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.models.narrative import NarrativeStatus
from app.models.review import (
    AssignmentStatus,
    ReviewOutcome,
    ReviewStatus,
)


class ReviewPageQuery(BaseModel):
    page: int = Field(default=1, ge=1, le=10_000)
    page_size: int = Field(default=20, ge=1, le=100)

    model_config = ConfigDict(extra="forbid")


class NarrativeAssignmentCreate(BaseModel):
    reviewer_id: UUID = Field(description="Active reviewer receiving the assignment.")

    model_config = ConfigDict(extra="forbid")


class NarrativeAssignmentReassign(BaseModel):
    reviewer_id: UUID = Field(description="Active reviewer receiving the reassignment.")
    reason: str = Field(
        min_length=1,
        max_length=2000,
        description="Reason the current assignment is being replaced.",
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("reason")
    @classmethod
    def reason_must_not_be_blank(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("reason must not be blank")
        return normalized


class NarrativeAssignmentRevoke(BaseModel):
    reason: str = Field(
        min_length=1,
        max_length=2000,
        description="Reason the assignment is being revoked.",
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("reason")
    @classmethod
    def reason_must_not_be_blank(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("reason must not be blank")
        return normalized


class ReviewEvidenceCreate(BaseModel):
    source_title: str = Field(min_length=1, max_length=255)
    publisher: str = Field(min_length=1, max_length=255)
    url: AnyHttpUrl | None = Field(default=None)
    publication_date: date | None = Field(default=None)
    accessed_at: datetime = Field(
        description="UTC date and time the source was accessed."
    )
    relevance: str = Field(min_length=1, max_length=2000)

    model_config = ConfigDict(extra="forbid")

    @field_validator("source_title", "publisher", "relevance")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("text fields must not be blank")
        return normalized

    @field_validator("accessed_at")
    @classmethod
    def normalize_accessed_at(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)


class ReviewCreate(BaseModel):
    outcome: ReviewOutcome
    notes: str | None = Field(default=None, max_length=10_000)
    evidence: list[ReviewEvidenceCreate] = Field(default_factory=list, max_length=20)

    model_config = ConfigDict(extra="forbid")

    @field_validator("notes")
    @classmethod
    def normalize_notes(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class ReviewStatusUpdate(BaseModel):
    status: ReviewStatus
    reason: str | None = Field(default=None, max_length=2000)

    model_config = ConfigDict(extra="forbid")

    @field_validator("reason")
    @classmethod
    def normalize_reason(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @model_validator(mode="after")
    def escalation_requires_reason(self):
        if self.status == ReviewStatus.REQUIRES_ESCALATION and not self.reason:
            raise ValueError("reason is required when escalating a review")
        return self


class AssignedNarrativeResponse(BaseModel):
    id: UUID
    content: str
    status: NarrativeStatus
    version: int = Field(ge=1)
    submitted_at: datetime
    updated_at: datetime


class NarrativeAssignmentResponse(BaseModel):
    id: UUID
    narrative_id: UUID
    reviewer_id: UUID
    assigned_by_user_id: UUID
    status: AssignmentStatus
    review_status: ReviewStatus
    assigned_at: datetime
    updated_at: datetime
    revoked_at: datetime | None = None
    revoked_by_user_id: UUID | None = None
    revoked_reason: str | None = None
    narrative: AssignedNarrativeResponse | None = None


class NarrativeAssignmentPageResponse(BaseModel):
    items: list[NarrativeAssignmentResponse]
    page: int
    page_size: int
    total: int
    total_pages: int


class ReviewEvidenceResponse(BaseModel):
    id: UUID
    source_title: str
    publisher: str
    url: str | None
    publication_date: date | None
    accessed_at: datetime
    relevance: str
    created_at: datetime


class NarrativeReviewResponse(BaseModel):
    id: UUID
    assignment_id: UUID
    narrative_id: UUID
    reviewer_id: UUID
    outcome: ReviewOutcome
    notes: str | None
    reviewed_at: datetime
    evidence: list[ReviewEvidenceResponse]


class NarrativeReviewHistoryResponse(BaseModel):
    items: list[NarrativeReviewResponse]
    page: int
    page_size: int
    total: int
    total_pages: int
