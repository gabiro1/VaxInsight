from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.notifications import NotificationFrequency
from app.services.notifications import validate_expo_push_token


class NotificationPreferencesUpdate(BaseModel):
    """The user-controlled cadence for new published-content notifications."""

    frequency: NotificationFrequency

    model_config = ConfigDict(extra="forbid")


class NotificationPreferencesResponse(BaseModel):
    user_id: UUID
    frequency: NotificationFrequency
    last_notified_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationDeviceRegistration(BaseModel):
    """Register an Expo token for the authenticated account."""

    token: str = Field(min_length=1, max_length=255)
    platform: str | None = Field(default=None, min_length=1, max_length=32)

    model_config = ConfigDict(extra="forbid")

    @field_validator("token")
    @classmethod
    def validate_token(cls, value: str) -> str:
        return validate_expo_push_token(value)

    @field_validator("platform")
    @classmethod
    def normalize_platform(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        return normalized or None


class NotificationDeviceResponse(BaseModel):
    """The registered device; the token is returned only on registration."""

    id: UUID
    user_id: UUID
    token: str
    platform: str | None
    last_seen_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
