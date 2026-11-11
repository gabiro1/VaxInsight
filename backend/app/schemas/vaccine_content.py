from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import (
    AliasChoices,
    AnyHttpUrl,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.models.vaccine_content import ContentLanguage, VaccineContentStatus


def _normalized_text(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError("text must not be blank")
    return normalized


class VaccineSourceCreate(BaseModel):
    """Source metadata supplied by an administrator."""

    authority: str = Field(min_length=1, max_length=255)
    name: str = Field(min_length=1, max_length=255)
    url: AnyHttpUrl
    jurisdiction: str = Field(min_length=1, max_length=128)

    model_config = ConfigDict(extra="forbid")

    _normalize_text = field_validator("authority", "name", "jurisdiction")(
        _normalized_text
    )


class VaccineContentCreate(BaseModel):
    """Validate administrator-managed registry content without seeding data."""

    source: VaccineSourceCreate | None = None
    source_authority: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        validation_alias=AliasChoices("source_authority", "authority"),
    )
    source_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        validation_alias=AliasChoices("source_name", "name"),
    )
    source_url: AnyHttpUrl | None = Field(
        default=None,
        validation_alias=AliasChoices("source_url", "url"),
    )
    source_jurisdiction: str | None = Field(
        default=None,
        min_length=1,
        max_length=128,
        validation_alias=AliasChoices("source_jurisdiction", "jurisdiction"),
    )
    language: ContentLanguage
    category: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=255)
    summary: str = Field(min_length=1, max_length=5000)
    body: str = Field(min_length=1, max_length=100_000)
    version: int = Field(default=1, ge=1)
    status: VaccineContentStatus = VaccineContentStatus.DRAFT
    # These fields are accepted for clients that carry approval metadata, but the
    # authenticated administrator remains the server-authoritative approver.
    approved_by_user_id: UUID | None = None
    approved_at: datetime | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("source_authority", "source_name", "source_jurisdiction")
    @classmethod
    def normalize_source_text(cls, value: str | None) -> str | None:
        return _normalized_text(value) if value is not None else None

    @field_validator("category", "title", "summary", "body")
    @classmethod
    def normalize_content_text(cls, value: str) -> str:
        return _normalized_text(value)

    @model_validator(mode="after")
    def normalize_source(self):
        flat_source_values = (
            self.source_authority,
            self.source_name,
            self.source_url,
            self.source_jurisdiction,
        )
        if self.source is not None:
            if any(value is not None for value in flat_source_values):
                raise ValueError("source cannot be combined with flat source fields")
            return self

        if not all(value is not None for value in flat_source_values):
            raise ValueError(
                "source or all source authority, name, url, and jurisdiction fields "
                "are required"
            )

        self.source = VaccineSourceCreate(
            authority=self.source_authority,
            name=self.source_name,
            url=self.source_url,
            jurisdiction=self.source_jurisdiction,
        )
        return self


class VaccineSourceResponse(BaseModel):
    id: UUID
    authority: str
    name: str
    url: str
    jurisdiction: str
    created_by_user_id: UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VaccineContentResponse(BaseModel):
    id: UUID
    source: VaccineSourceResponse
    language: Literal["rw", "en"]
    category: str
    title: str
    summary: str
    body: str
    version: int = Field(ge=1)
    status: Literal["draft", "published"]
    published_at: datetime | None
    created_by_user_id: UUID | None
    approved_by_user_id: UUID | None
    approved_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
