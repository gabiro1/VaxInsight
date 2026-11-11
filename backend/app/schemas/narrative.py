import unicodedata
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.review import ReviewStatus

MAX_NARRATIVE_CONTENT_LENGTH = 10_000
NarrativeStatusValue = Literal["submitted"]


class NarrativeCreate(BaseModel):
    """Validate the neutral narrative content accepted by the record foundation."""

    content: str = Field(
        min_length=1,
        max_length=MAX_NARRATIVE_CONTENT_LENGTH,
        description="The submitted vaccine-related narrative text.",
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("content")
    @classmethod
    def content_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("content must contain non-whitespace characters")
        if any(
            unicodedata.category(character) == "Cc" and character not in "\t\n\r"
            for character in value
        ):
            raise ValueError("content contains unsupported control characters")
        return value


class NarrativeUpdate(NarrativeCreate):
    """Validate an owner update without allowing lifecycle fields to be changed."""


class NarrativeListQuery(BaseModel):
    """Validate owner-scoped narrative list filters."""

    page: int = Field(default=1, ge=1, le=10_000)
    page_size: int = Field(default=20, ge=1, le=100)
    status: NarrativeStatusValue | None = Field(
        default=None,
        description="Filter by the currently supported neutral lifecycle state.",
    )
    submitted_after: datetime | None = Field(
        default=None,
        description="Include narratives submitted at or after this timestamp.",
    )
    submitted_before: datetime | None = Field(
        default=None,
        description="Include narratives submitted at or before this timestamp.",
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def date_range_is_valid(self):
        if (
            self.submitted_after is not None
            and self.submitted_before is not None
            and self.submitted_after > self.submitted_before
        ):
            raise ValueError("submitted_after must be before submitted_before")
        return self


class NarrativeHistoryQuery(BaseModel):
    """Validate pagination for owner-visible narrative revisions."""

    page: int = Field(default=1, ge=1, le=10_000)
    page_size: int = Field(default=20, ge=1, le=100)

    model_config = ConfigDict(extra="forbid")


class NarrativeResponse(BaseModel):
    id: UUID = Field(description="Unique narrative identifier.")
    submitted_by_id: UUID = Field(description="Account that submitted the narrative.")
    content: str = Field(description="Submitted narrative text.")
    status: NarrativeStatusValue = Field(description="Current neutral lifecycle state.")
    review_status: ReviewStatus | None = Field(
        default=None,
        description=(
            "Status-only metadata for the owner's active review assignment. "
            "Internal notes, outcomes, evidence, and Health Expert history are excluded."
        ),
    )
    version: int = Field(ge=1, description="Current narrative revision number.")
    submitted_at: datetime = Field(description="UTC narrative submission timestamp.")
    updated_at: datetime = Field(description="UTC timestamp of the latest update.")

    model_config = ConfigDict(from_attributes=True)


class NarrativePageResponse(BaseModel):
    items: list[NarrativeResponse] = Field(
        description="Narratives in the current page."
    )
    page: int = Field(description="Current one-based page number.")
    page_size: int = Field(description="Requested number of narratives per page.")
    total: int = Field(description="Total number of matching narratives.")
    total_pages: int = Field(description="Total number of available pages.")


class NarrativeRevisionResponse(BaseModel):
    id: UUID = Field(description="Unique revision identifier.")
    narrative_id: UUID = Field(description="Narrative represented by this revision.")
    changed_by_user_id: UUID = Field(description="Account that made the change.")
    version: int = Field(ge=1, description="Revision number within the narrative.")
    action: Literal["created", "updated"] = Field(
        description="Type of change recorded for the revision."
    )
    content: str = Field(description="Narrative content at this revision.")
    changed_at: datetime = Field(description="UTC revision timestamp.")

    model_config = ConfigDict(from_attributes=True)


class NarrativeRevisionPageResponse(BaseModel):
    items: list[NarrativeRevisionResponse] = Field(
        description="Narrative revisions in the current page."
    )
    page: int = Field(description="Current one-based page number.")
    page_size: int = Field(description="Requested number of revisions per page.")
    total: int = Field(description="Total number of revisions.")
    total_pages: int = Field(description="Total number of available pages.")
