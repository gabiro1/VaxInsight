from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

UserRoleValue = Literal["community_member", "chw", "reviewer", "administrator"]
StaffRoleValue = Literal["chw", "reviewer", "administrator"]


class UserRegister(BaseModel):
    """Validate public community registration data."""

    full_name: str = Field(
        min_length=1,
        max_length=255,
        description="The community member's full name.",
        examples=["Amina Uwase"],
    )

    email: EmailStr = Field(
        description="Account email address.",
        examples=["person@example.com"],
    )
    password: str = Field(
        min_length=12,
        max_length=128,
        description="Account password; must contain 12 to 128 characters.",
    )
    confirm_password: str = Field(
        min_length=12,
        max_length=128,
        description="The password repeated for confirmation.",
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("full_name", mode="before")
    @classmethod
    def normalize_full_name(cls, value: str) -> str:
        if isinstance(value, str):
            value = " ".join(value.strip().split())
        return value

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class UserLogin(BaseModel):
    """Validate user login credentials."""

    email: EmailStr = Field(
        description="Account email address.",
        examples=["person@example.com"],
    )
    password: str = Field(
        min_length=1,
        max_length=128,
        description="Account password.",
    )

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()


class UserResponse(BaseModel):
    """Define the public user information returned by the API."""

    id: UUID = Field(description="Unique account identifier.")
    email: EmailStr = Field(description="Current account email address.")
    full_name: str | None = Field(
        default=None,
        description="The account holder's full name, when provided.",
    )
    is_active: bool = Field(description="Whether the account can authenticate.")
    status: str | None = Field(
        default="active",
        description="Account lifecycle status.",
    )
    role: UserRoleValue | None = Field(
        default=None,
        description="Assigned application role, when one is present.",
    )
    email_verified_at: datetime | None = Field(
        default=None,
        description="UTC timestamp when the email address was verified.",
    )
    created_at: datetime = Field(description="UTC account creation timestamp.")
    updated_at: datetime = Field(
        description="UTC timestamp of the last account update."
    )

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """Return the tokens required to authenticate subsequent requests."""

    access_token: str = Field(
        description="JWT access token; send it as a Bearer token.",
    )
    token_type: str = Field(
        default="bearer",
        description="Authentication scheme for the access token.",
    )
    expires_in: int | None = Field(
        default=None,
        description="Access-token lifetime in seconds, when provided.",
    )
    refresh_token: str | None = Field(
        default=None,
        description="Opaque refresh token for obtaining a new access token.",
    )
    refresh_token_expires_in: int | None = Field(
        default=None,
        description="Refresh-token lifetime in seconds, when provided.",
    )


class InvitationCreate(BaseModel):
    email: EmailStr = Field(
        description="Email address that will receive the invitation.",
        examples=["colleague@example.com"],
    )
    role: StaffRoleValue = Field(
        description="Role granted when the invitation is accepted."
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()


class InvitationAccept(BaseModel):
    token: str = Field(
        min_length=32,
        max_length=512,
        description="Single-use invitation token received through email.",
    )
    password: str = Field(
        min_length=12,
        max_length=128,
        description="Password for the newly created account.",
    )


class InvitationResponse(BaseModel):
    message: str = Field(description="Invitation delivery status.")
    expires_at: datetime = Field(
        description="UTC timestamp when the invitation expires."
    )


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(
        min_length=32,
        max_length=512,
        description="Opaque refresh token issued by login or token refresh.",
    )


class LogoutRequest(BaseModel):
    refresh_token: str = Field(
        min_length=32,
        max_length=512,
        description="Refresh token for the session to revoke.",
    )


class PasswordChange(BaseModel):
    current_password: str = Field(
        min_length=1,
        max_length=128,
        description="Current account password.",
    )
    new_password: str = Field(
        min_length=12,
        max_length=128,
        description="Replacement password; must contain 12 to 128 characters.",
    )


class PasswordResetRequest(BaseModel):
    email: EmailStr = Field(
        description="Email address associated with the account.",
        examples=["person@example.com"],
    )

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()


class EmailVerificationResendRequest(BaseModel):
    """Validate an email address for a verification-message resend."""

    email: EmailStr = Field(
        description="Email address that should receive verification instructions.",
        examples=["person@example.com"],
    )

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()


class PasswordResetConfirm(BaseModel):
    token: str = Field(
        min_length=32,
        max_length=512,
        description="Single-use password-reset token received through email.",
    )
    new_password: str = Field(
        min_length=12,
        max_length=128,
        description="Replacement password; must contain 12 to 128 characters.",
    )


class EmailVerificationRequest(BaseModel):
    email: EmailStr = Field(
        description="Email address associated with the verification code.",
        examples=["person@example.com"],
    )
    otp: str = Field(
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
        description="Six-digit, single-use email-verification code.",
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()


class AccountStatusUpdate(BaseModel):
    status: Literal["active", "suspended", "deactivated", "deleted"] = Field(
        description="New lifecycle status for the account."
    )

    model_config = ConfigDict(extra="forbid")


class RoleUpdate(BaseModel):
    role: UserRoleValue = Field(description="New application role for the account.")

    model_config = ConfigDict(extra="forbid")


class ProfileUpdate(BaseModel):
    full_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="The account holder's full name.",
        examples=["Amina Uwase"],
    )
    email: EmailStr | None = Field(
        default=None,
        description="New email address; it must be verified before use.",
        examples=["new-address@example.com"],
    )

    @field_validator("full_name", mode="before")
    @classmethod
    def normalize_full_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            return " ".join(value.strip().split())
        return value

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr | None) -> str | None:
        return str(value).strip().lower() if value is not None else None
