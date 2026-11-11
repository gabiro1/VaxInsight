from datetime import UTC, datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


class AuditEventQuery(BaseModel):
    """Validate filters and pagination for the administrator audit log."""

    page: int = Field(
        default=1,
        ge=1,
        le=10_000,
        description="1-based page number.",
    )
    page_size: int = Field(
        default=50,
        ge=1,
        le=100,
        description="Number of audit events returned per page.",
    )
    action: str | None = Field(
        default=None,
        min_length=1,
        max_length=64,
        description="Filter by recorded audit action.",
    )
    outcome: str | None = Field(
        default=None,
        min_length=1,
        max_length=32,
        description="Filter by recorded outcome.",
    )
    actor_user_id: UUID | None = Field(
        default=None,
        description="Filter by the user who initiated the event.",
    )
    target_user_id: UUID | None = Field(
        default=None,
        description="Filter by the user affected by the event.",
    )
    start_date: datetime | None = Field(
        default=None,
        description="Include events at or after this UTC timestamp.",
    )
    end_date: datetime | None = Field(
        default=None,
        description="Include events at or before this UTC timestamp.",
    )

    @field_validator("action", "outcome", mode="before")
    @classmethod
    def normalize_text_filter(cls, value: str | None) -> str | None:
        if value is None:
            return None

        normalized = value.strip()
        if not normalized:
            raise ValueError("filter must not be blank")
        return normalized

    @field_validator("start_date", "end_date")
    @classmethod
    def normalize_date_filter(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_date_range(self):
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date < self.start_date
        ):
            raise ValueError("end_date must be on or after start_date")
        return self


class AuditEventResponse(BaseModel):
    id: UUID = Field(description="Unique audit event identifier.")
    actor_user_id: UUID | None = Field(
        description="User who initiated the event, when available."
    )
    target_user_id: UUID | None = Field(
        description="User affected by the event, when available."
    )
    action: str = Field(description="Recorded audit action.")
    outcome: str = Field(description="Recorded outcome of the action.")
    ip_address: str | None = Field(description="Client IP address, when recorded.")
    user_agent: str | None = Field(description="Client user agent, when recorded.")
    created_at: datetime = Field(description="UTC event creation timestamp.")
    details: dict[str, str] = Field(
        default_factory=dict,
        description="Sanitized non-sensitive event details.",
    )


class AuditEventPageResponse(BaseModel):
    items: list[AuditEventResponse] = Field(description="Events in the current page.")
    page: int = Field(description="Current 1-based page number.")
    page_size: int = Field(description="Requested number of events per page.")
    total: int = Field(description="Total number of matching events.")
    total_pages: int = Field(description="Total number of available pages.")
