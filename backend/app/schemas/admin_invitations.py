from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.user import UserRole

InvitationStatus = Literal["pending", "accepted", "revoked", "expired"]
InvitationSortField = Literal["created_at", "expires_at", "email", "status"]
InvitationSortOrder = Literal["asc", "desc"]


class InvitationDirectoryQuery(BaseModel):
    page: int = Field(
        default=1,
        ge=1,
        le=10_000,
        description="1-based page number.",
    )
    page_size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Number of invitations returned per page.",
    )
    search: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Normalized invitee email fragment to search for.",
    )
    role: UserRole | None = Field(
        default=None,
        description="Filter by invited application role.",
    )
    status: InvitationStatus | None = Field(
        default=None,
        description="Filter by derived invitation status.",
    )
    sort_by: InvitationSortField = Field(
        default="created_at",
        description="Field used to order the results.",
    )
    sort_order: InvitationSortOrder = Field(
        default="desc",
        description="Result ordering direction.",
    )

    @field_validator("search", mode="before")
    @classmethod
    def normalize_search(cls, value: str | None) -> str | None:
        if value is None:
            return None

        normalized = value.strip()
        if not normalized:
            raise ValueError("search must not be blank")
        return normalized


class AdminInvitationResponse(BaseModel):
    id: UUID = Field(description="Unique invitation identifier.")
    email: EmailStr = Field(description="Invitee email address.")
    role: UserRole = Field(description="Role granted if the invitation is accepted.")
    status: InvitationStatus = Field(description="Derived invitation lifecycle status.")
    created_at: datetime = Field(description="UTC invitation creation timestamp.")
    expires_at: datetime = Field(description="UTC invitation expiry timestamp.")
    accepted_at: datetime | None = Field(
        description="UTC acceptance timestamp, when the invitation was accepted."
    )
    revoked_at: datetime | None = Field(
        description="UTC revocation timestamp, when the invitation was revoked."
    )


class AdminInvitationPageResponse(BaseModel):
    items: list[AdminInvitationResponse] = Field(
        description="Invitations in the current page."
    )
    page: int = Field(description="Current 1-based page number.")
    page_size: int = Field(description="Requested number of invitations per page.")
    total: int = Field(description="Total number of matching invitations.")
    total_pages: int = Field(description="Total number of available pages.")
