from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.user import AccountStatus, UserRole

UserSortField = Literal[
    "created_at",
    "updated_at",
    "email",
    "last_login_at",
    "status",
    "role",
]
UserSortOrder = Literal["asc", "desc"]


class UserDirectoryQuery(BaseModel):
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
        description="Number of users returned per page.",
    )
    search: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Normalized email fragment to search for.",
    )
    role: UserRole | None = Field(
        default=None,
        description="Filter by application role.",
    )
    status: AccountStatus | None = Field(
        default=None,
        description="Filter by account lifecycle status.",
    )
    email_verified: bool | None = Field(
        default=None,
        description="Filter by email-verification state.",
    )
    sort_by: UserSortField = Field(
        default="created_at",
        description="Field used to order the results.",
    )
    sort_order: UserSortOrder = Field(
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


class AdminUserResponse(BaseModel):
    id: UUID = Field(description="Unique account identifier.")
    email: EmailStr = Field(description="Account email address.")
    role: UserRole | None = Field(description="Assigned application role.")
    status: AccountStatus = Field(description="Account lifecycle status.")
    email_verified: bool = Field(description="Whether the account email is verified.")
    created_at: datetime = Field(description="UTC account creation timestamp.")
    last_login_at: datetime | None = Field(
        description="UTC timestamp of the last successful login, when available."
    )
    updated_at: datetime = Field(
        description="UTC timestamp of the last account update."
    )


class AdminUserPageResponse(BaseModel):
    items: list[AdminUserResponse] = Field(description="Users in the current page.")
    page: int = Field(description="Current 1-based page number.")
    page_size: int = Field(description="Requested number of users per page.")
    total: int = Field(description="Total number of matching users.")
    total_pages: int = Field(description="Total number of available pages.")
