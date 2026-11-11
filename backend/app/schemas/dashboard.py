from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.narrative import NarrativeStatus
from app.models.review import ReviewStatus


class RoleStatistics(BaseModel):
    community_member: int = Field(ge=0, description="Number of community accounts.")
    chw: int = Field(ge=0, description="Number of CHW accounts.")
    reviewer: int = Field(ge=0, description="Number of Health Expert accounts.")
    administrator: int = Field(ge=0, description="Number of administrator accounts.")
    unassigned: int = Field(ge=0, description="Number of accounts without a role.")


class UserStatistics(BaseModel):
    total: int = Field(ge=0, description="Total number of user accounts.")
    active: int = Field(ge=0, description="Number of active user accounts.")
    pending: int = Field(ge=0, description="Number of pending user accounts.")
    suspended: int = Field(ge=0, description="Number of suspended user accounts.")
    deactivated: int = Field(ge=0, description="Number of deactivated user accounts.")
    deleted: int = Field(ge=0, description="Number of deleted user accounts.")
    by_role: RoleStatistics = Field(description="User counts grouped by role.")


class InvitationStatistics(BaseModel):
    total: int = Field(ge=0, description="Total number of invitations.")
    pending: int = Field(ge=0, description="Number of pending invitations.")
    accepted: int = Field(ge=0, description="Number of accepted invitations.")
    expired: int = Field(ge=0, description="Number of expired invitations.")
    revoked: int = Field(ge=0, description="Number of revoked invitations.")


class SessionStatistics(BaseModel):
    active: int = Field(ge=0, description="Number of active refresh sessions.")
    revoked: int = Field(ge=0, description="Number of revoked refresh sessions.")
    expired: int = Field(ge=0, description="Number of expired refresh sessions.")


class PlatformStatistics(BaseModel):
    period_days: int = Field(
        ge=1, description="Number of days used for the platform activity metrics."
    )
    total_narratives: int = Field(
        ge=0, description="Narratives submitted during the reporting period."
    )
    active_users: int = Field(ge=0, description="Currently active user accounts.")
    review_completion_rate: int = Field(
        ge=0,
        le=100,
        description="Percentage of assignments created during the period that are reviewed.",
    )
    trusted_info_rate: int = Field(
        ge=0,
        le=100,
        description=(
            "Percentage of completed reviews during the period whose outcome "
            "indicates that the evidence supports the claim."
        ),
    )


class DashboardSummaryResponse(BaseModel):
    users: UserStatistics = Field(description="User account statistics.")
    invitations: InvitationStatistics = Field(description="Invitation statistics.")
    sessions: SessionStatistics = Field(description="Refresh session statistics.")
    platform: PlatformStatistics = Field(
        description="Non-sensitive platform metrics for the administrator home screen."
    )


class PersonalNarrativeSummary(BaseModel):
    """Owner-safe narrative information for a personal dashboard."""

    id: UUID = Field(description="Unique narrative identifier.")
    content: str = Field(description="Submitted narrative text.")
    status: NarrativeStatus = Field(description="Current neutral narrative state.")
    review_status: ReviewStatus | None = Field(
        default=None,
        description=(
            "Current status of the owner's active review assignment, without "
            "Health Expert notes, outcomes, or evidence."
        ),
    )
    version: int = Field(ge=1, description="Current narrative revision number.")
    submitted_at: datetime = Field(description="UTC narrative submission timestamp.")
    updated_at: datetime = Field(description="UTC timestamp of the latest update.")


class PersonalActivitySummary(BaseModel):
    """Personal CHW activity metrics derived from owned records only."""

    submitted: int = Field(
        ge=0,
        description="Total narratives submitted by the authenticated account.",
    )
    under_review: int = Field(
        ge=0,
        description=(
            "Owned narratives with an active pending, in-review, or escalated "
            "assignment."
        ),
    )
    reviewed: int = Field(
        ge=0,
        description="Owned narratives whose active assignment is reviewed.",
    )


class PersonalDashboardSummaryResponse(BaseModel):
    """Authenticated-user dashboard data with no cross-user aggregates."""

    activity: PersonalActivitySummary
    recent_narratives: list[PersonalNarrativeSummary] = Field(
        description="The latest owned narratives and status-only review metadata."
    )
