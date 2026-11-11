from html import escape
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_permissions
from app.api.docs import documented_responses
from app.core.config import settings
from app.core.permissions import Permission
from app.database.dependencies import get_db
from app.models.user import User, UserRole
from app.schemas.auth import (
    AccountStatusUpdate,
    EmailVerificationRequest,
    EmailVerificationResendRequest,
    InvitationAccept,
    InvitationCreate,
    InvitationResponse,
    LogoutRequest,
    PasswordChange,
    PasswordResetConfirm,
    PasswordResetRequest,
    ProfileUpdate,
    RefreshTokenRequest,
    RoleUpdate,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)
from app.schemas.common import MessageResponse, TokenCheckResponse
from app.services.audit import add_audit_event
from app.services.auth import (
    AdministratorSelfModificationError,
    EmailAlreadyRegistered,
    InvalidAccountStatus,
    InvalidCredentials,
    InvalidEmailVerificationToken,
    InvalidInvitation,
    InvalidPasswordResetToken,
    LastActiveAdministratorError,
    accept_invitation,
    authenticate_user_account,
    change_account_status,
    change_password,
    change_user_role,
    confirm_password_reset,
    create_email_verification,
    create_invitation,
    delete_account,
    register_user,
    request_email_change,
    request_email_verification,
    request_password_reset,
    verify_email,
)
from app.services.email import EmailDeliveryError, mobile_action_url
from app.services.rate_limit import enforce_rate_limit
from app.services.sessions import (
    InvalidRefreshToken,
    issue_tokens,
    revoke_all_sessions,
    revoke_refresh_token,
    rotate_refresh_token,
)

router = APIRouter()
invitation_manage_dependency = require_permissions(Permission.INVITATION_MANAGE)
user_manage_dependency = require_permissions(Permission.USER_MANAGE)
role_manage_dependency = require_permissions(Permission.ROLE_MANAGE)


@router.get(
    "/accept-invitation",
    response_class=HTMLResponse,
    include_in_schema=False,
)
def invitation_landing_page(
    token: str = Query(..., min_length=32, max_length=512),
):
    """Render a clickable browser handoff for email clients and Expo Go."""

    mobile_url = mobile_action_url("invite", token)
    if mobile_url is None:
        return HTMLResponse(
            content=(
                "<!doctype html><html><body>"
                "<h1>Invitation link unavailable</h1>"
                "<p>Open this invitation from a configured VaxInsight app.</p>"
                "</body></html>"
            ),
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            headers={"Cache-Control": "no-store"},
        )

    safe_mobile_url = escape(mobile_url, quote=True)
    return HTMLResponse(
        content=(
            "<!doctype html><html><head><meta name=\"viewport\" "
            "content=\"width=device-width,initial-scale=1\"></head><body>"
            "<h1>VaxInsight invitation</h1>"
            "<p>Your invitation is ready. Open it in the VaxInsight app to "
            "choose a password.</p>"
            f"<p><a href=\"{safe_mobile_url}\">Open invitation in VaxInsight</a></p>"
            "</body></html>"
        ),
        headers={"Cache-Control": "no-store"},
    )


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    response_description="The newly created pending user profile.",
    summary="Register a community account",
    description=(
        "Create a pending community account without an invitation. Staff roles "
        "are created through the invitation workflow, and every account remains "
        "subject to email verification."
    ),
    responses=documented_responses(
        status.HTTP_403_FORBIDDEN,
        status.HTTP_409_CONFLICT,
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        status.HTTP_429_TOO_MANY_REQUESTS,
        status.HTTP_503_SERVICE_UNAVAILABLE,
    ),
    tags=["Authentication"],
)
def register(
    request: Request,
    user_data: UserRegister,
    db: Session = Depends(get_db),
):
    """Create a pending community account without granting a staff role."""

    if not settings.ALLOW_COMMUNITY_REGISTRATION:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Community registration is disabled",
        )

    enforce_rate_limit(
        db,
        request,
        scope="register",
        limit=settings.REGISTER_RATE_LIMIT,
        identity=user_data.email,
    )

    try:
        user = register_user(db, user_data)
        create_email_verification(db, user)
    except EmailAlreadyRegistered:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        ) from None
    except EmailDeliveryError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Account email delivery is temporarily unavailable",
        ) from None

    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    response_description="Access and refresh tokens for the authenticated account.",
    summary="Authenticate a user",
    description=(
        "Validate account credentials and issue a short-lived JWT access token "
        "with a rotating refresh token."
    ),
    responses=documented_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        status.HTTP_429_TOO_MANY_REQUESTS,
        status.HTTP_503_SERVICE_UNAVAILABLE,
    ),
    tags=["Authentication"],
)
def login(
    request: Request,
    login_data: UserLogin,
    db: Session = Depends(get_db),
):
    """Authenticate a user and return rotating session tokens."""

    enforce_rate_limit(
        db,
        request,
        scope="login",
        limit=settings.LOGIN_RATE_LIMIT,
        identity=login_data.email,
    )

    try:
        user = authenticate_user_account(db, login_data)
    except InvalidCredentials:
        add_audit_event(db, action="login", outcome="failure", request=request)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    return issue_tokens(db, user)


@router.post(
    "/invitations",
    response_model=InvitationResponse,
    status_code=status.HTTP_201_CREATED,
    response_description="Invitation delivery status and expiry.",
    summary="Create an account invitation",
    description=(
        "Allow an administrator to invite approved personnel by email without "
        "sharing a password or exposing the invitation token in the response."
    ),
    responses=documented_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_409_CONFLICT,
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        status.HTTP_429_TOO_MANY_REQUESTS,
        status.HTTP_503_SERVICE_UNAVAILABLE,
    ),
    tags=["Invitation Management"],
)
def create_account_invitation(
    request: Request,
    invitation_data: InvitationCreate,
    current_user: User = Depends(invitation_manage_dependency),
    db: Session = Depends(get_db),
):
    """Invite approved personnel without sharing a password."""

    enforce_rate_limit(
        db,
        request,
        scope="invitation",
        limit=settings.INVITATION_RATE_LIMIT,
        identity=invitation_data.email,
    )

    try:
        invitation = create_invitation(
            db,
            email=invitation_data.email,
            role=invitation_data.role,
            invited_by=current_user,
        )
    except EmailAlreadyRegistered:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        ) from None
    except (EmailDeliveryError, InvalidInvitation):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The invitation could not be delivered",
        ) from None

    return InvitationResponse(
        message="Invitation sent",
        expires_at=invitation.expires_at,
    )


@router.post(
    "/invitations/accept",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    response_description="Access and refresh tokens for the invited account.",
    summary="Accept an account invitation",
    description=(
        "Consume a valid single-use invitation, create the invited account, and "
        "establish its first authenticated session."
    ),
    responses=documented_responses(
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_409_CONFLICT,
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        status.HTTP_429_TOO_MANY_REQUESTS,
        status.HTTP_503_SERVICE_UNAVAILABLE,
    ),
    tags=["Invitation Management"],
)
def accept_account_invitation(
    request: Request,
    invitation_data: InvitationAccept,
    db: Session = Depends(get_db),
):
    """Accept a single-use invitation and establish the first session."""

    enforce_rate_limit(
        db,
        request,
        scope="invitation_accept",
        limit=settings.INVITATION_RATE_LIMIT,
    )

    try:
        user = accept_invitation(
            db,
            invitation_data.token,
            invitation_data.password,
        )
    except EmailAlreadyRegistered:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this invitation already exists",
        ) from None
    except InvalidInvitation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The invitation is invalid or expired",
        ) from None

    return issue_tokens(db, user, audit_action="invitation_login")


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    response_description="A new access token and rotated refresh token.",
    summary="Refresh an access token",
    description=(
        "Rotate a valid refresh token and issue a new authenticated session pair."
    ),
    responses=documented_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        status.HTTP_429_TOO_MANY_REQUESTS,
        status.HTTP_503_SERVICE_UNAVAILABLE,
    ),
    tags=["Authentication"],
)
def refresh_tokens(
    request: Request,
    token_data: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    enforce_rate_limit(
        db,
        request,
        scope="refresh",
        limit=settings.LOGIN_RATE_LIMIT,
    )

    try:
        return rotate_refresh_token(db, token_data.refresh_token)
    except InvalidRefreshToken:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        ) from None


@router.post(
    "/logout",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    response_description="The current session was logged out.",
    summary="Log out the current session",
    description="Revoke the supplied refresh token for the authenticated account.",
    responses=documented_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_422_UNPROCESSABLE_CONTENT,
    ),
    tags=["Accounts"],
)
def logout(
    token_data: LogoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    revoke_refresh_token(db, token_data.refresh_token, current_user)
    return {"message": "Logout successful"}


@router.post(
    "/logout-all",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    response_description="All sessions were logged out.",
    summary="Log out all sessions",
    description="Revoke every active refresh session for the authenticated account.",
    responses=documented_responses(status.HTTP_401_UNAUTHORIZED),
    tags=["Accounts"],
)
def logout_all(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    revoke_all_sessions(db, current_user.id)
    add_audit_event(
        db,
        action="logout_all",
        outcome="success",
        actor_user_id=current_user.id,
        target_user_id=current_user.id,
    )
    db.commit()
    return {"message": "All sessions logged out successfully"}


@router.post(
    "/password/change",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    response_description="The account password was changed successfully.",
    summary="Change the account password",
    description=(
        "Change the authenticated account password after validating the current "
        "password. Existing sessions are handled by the authentication service."
    ),
    responses=documented_responses(
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_422_UNPROCESSABLE_CONTENT,
    ),
    tags=["Accounts"],
)
def change_my_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        change_password(
            db,
            current_user,
            password_data.current_password,
            password_data.new_password,
        )
    except InvalidCredentials:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        ) from None
    return {"message": "Password changed successfully"}


@router.post(
    "/password-reset/request",
    response_model=MessageResponse,
    status_code=status.HTTP_202_ACCEPTED,
    response_description="A generic password-reset request acknowledgement.",
    summary="Request a password reset",
    description=(
        "Request password-reset instructions. The response is intentionally "
        "generic so it does not disclose whether an email is registered."
    ),
    responses=documented_responses(
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        status.HTTP_429_TOO_MANY_REQUESTS,
        status.HTTP_503_SERVICE_UNAVAILABLE,
    ),
    tags=["Accounts"],
)
def request_password_reset_endpoint(
    request: Request,
    reset_data: PasswordResetRequest,
    db: Session = Depends(get_db),
):
    enforce_rate_limit(
        db,
        request,
        scope="password_reset",
        limit=settings.RESET_RATE_LIMIT,
        identity=reset_data.email,
    )

    try:
        request_password_reset(db, reset_data.email)
    except EmailDeliveryError:
        # Keep reset responses indistinguishable for existing and unknown emails.
        db.rollback()

    return {"message": "If an account exists, password reset instructions will be sent"}


@router.post(
    "/password-reset/confirm",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    response_description="The password reset was completed successfully.",
    summary="Confirm a password reset",
    description="Consume a valid password-reset token and set a new password.",
    responses=documented_responses(
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        status.HTTP_429_TOO_MANY_REQUESTS,
        status.HTTP_503_SERVICE_UNAVAILABLE,
    ),
    tags=["Accounts"],
)
def confirm_password_reset_endpoint(
    request: Request,
    reset_data: PasswordResetConfirm,
    db: Session = Depends(get_db),
):
    enforce_rate_limit(
        db,
        request,
        scope="password_reset_confirm",
        limit=settings.RESET_RATE_LIMIT,
    )
    try:
        confirm_password_reset(
            db,
            reset_data.token,
            reset_data.new_password,
        )
    except InvalidPasswordResetToken:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The password reset token is invalid or expired",
        ) from None
    return {"message": "Password reset successful"}


@router.post(
    "/email/verify",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    response_description="Access and refresh tokens for the verified account.",
    summary="Verify an email address",
    description=(
        "Consume a valid six-digit email-verification code, activate the account, "
        "and establish an authenticated session."
    ),
    responses=documented_responses(
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        status.HTTP_429_TOO_MANY_REQUESTS,
        status.HTTP_503_SERVICE_UNAVAILABLE,
    ),
    tags=["Accounts"],
)
def verify_email_endpoint(
    request: Request,
    verification_data: EmailVerificationRequest,
    db: Session = Depends(get_db),
):
    enforce_rate_limit(
        db,
        request,
        scope="email_verify",
        limit=settings.RESET_RATE_LIMIT,
    )
    try:
        user = verify_email(
            db,
            verification_data.email,
            verification_data.otp,
        )
        return issue_tokens(db, user, audit_action="email_verification_login")
    except InvalidEmailVerificationToken:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The email verification code is invalid or expired",
        ) from None
    except InvalidRefreshToken:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verified, but the account is not active",
        ) from None


@router.post(
    "/email/verify/resend",
    response_model=MessageResponse,
    status_code=status.HTTP_202_ACCEPTED,
    response_description="A generic email-verification request acknowledgement.",
    summary="Resend email-verification instructions",
    description=(
        "Request a new email-verification message. The response remains generic "
        "to avoid disclosing account state."
    ),
    responses=documented_responses(
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        status.HTTP_429_TOO_MANY_REQUESTS,
        status.HTTP_503_SERVICE_UNAVAILABLE,
    ),
    tags=["Accounts"],
)
def resend_email_verification(
    request: Request,
    verification_data: EmailVerificationResendRequest,
    db: Session = Depends(get_db),
):
    enforce_rate_limit(
        db,
        request,
        scope="email_verify_resend",
        limit=settings.RESET_RATE_LIMIT,
        identity=verification_data.email,
    )
    try:
        request_email_verification(db, verification_data.email)
    except EmailDeliveryError:
        db.rollback()

    return {"message": "If verification is required, instructions will be sent"}


@router.patch(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    response_description="The current account profile.",
    summary="Update the current account profile",
    description=(
        "Update the authenticated account's full name or request an email change. "
        "A new email requires verification before it becomes active."
    ),
    responses=documented_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_409_CONFLICT,
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        status.HTTP_503_SERVICE_UNAVAILABLE,
    ),
    tags=["Accounts"],
)
def update_my_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    email_changed = (
        profile_data.email is not None and profile_data.email != current_user.email
    )
    full_name_changed = (
        profile_data.full_name is not None
        and profile_data.full_name != current_user.full_name
    )

    if full_name_changed:
        current_user.full_name = profile_data.full_name

    if email_changed:
        try:
            request_email_change(db, current_user, profile_data.email)
        except EmailAlreadyRegistered:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists",
            ) from None
        except EmailDeliveryError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Email verification delivery is temporarily unavailable",
            ) from None
    elif full_name_changed:
        db.commit()
        db.refresh(current_user)

    if email_changed:
        db.refresh(current_user)

    return current_user


@router.delete(
    "/me",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    response_description="The current account and its data were permanently deleted.",
    summary="Delete the current account",
    description=(
        "Permanently delete the authenticated account and all account-owned data. "
        "This action cannot be undone, and the email address can be registered again."
    ),
    responses=documented_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_409_CONFLICT,
    ),
    tags=["Accounts"],
)
def delete_my_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        delete_account(db, current_user)
    except LastActiveAdministratorError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete the last active administrator",
        ) from None

    return {"message": "Account deleted successfully"}


@router.patch(
    "/admin/users/{user_id}/status",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    response_description="The updated user profile.",
    summary="Change a user account status",
    description=(
        "Allow an administrator to change a user's account status while preserving "
        "the availability of at least one active administrator."
    ),
    responses=documented_responses(
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
        status.HTTP_409_CONFLICT,
        status.HTTP_422_UNPROCESSABLE_CONTENT,
    ),
    tags=["User Management"],
)
def update_account_status(
    user_id: UUID,
    status_data: AccountStatusUpdate,
    current_user: User = Depends(user_manage_dependency),
    db: Session = Depends(get_db),
):
    target_user = db.get(User, user_id)
    if target_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    if target_user.id == current_user.id and status_data.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An administrator cannot deactivate their own account",
        )

    try:
        change_account_status(
            db,
            actor=current_user,
            target=target_user,
            new_status=status_data.status,
        )
    except AdministratorSelfModificationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An administrator cannot deactivate their own account",
        ) from None
    except LastActiveAdministratorError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot remove the last active administrator",
        ) from None
    except InvalidAccountStatus:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Invalid account status",
        ) from None
    return target_user


@router.patch(
    "/admin/users/{user_id}/role",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    response_description="The updated user profile.",
    summary="Change a user role",
    description=(
        "Allow an administrator to change a user's role while preserving the "
        "availability of at least one active administrator."
    ),
    responses=documented_responses(
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
        status.HTTP_409_CONFLICT,
        status.HTTP_422_UNPROCESSABLE_CONTENT,
    ),
    tags=["User Management"],
)
def update_account_role(
    user_id: UUID,
    role_data: RoleUpdate,
    current_user: User = Depends(role_manage_dependency),
    db: Session = Depends(get_db),
):
    target_user = db.get(User, user_id)
    if target_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    if (
        target_user.id == current_user.id
        and role_data.role != UserRole.ADMINISTRATOR.value
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An administrator cannot remove their own administrator role",
        )

    try:
        change_user_role(
            db,
            actor=current_user,
            target=target_user,
            role=role_data.role,
        )
    except AdministratorSelfModificationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An administrator cannot remove their own administrator role",
        ) from None
    except LastActiveAdministratorError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot remove the last active administrator",
        ) from None
    return target_user


@router.get(
    "/token-check",
    response_model=TokenCheckResponse,
    status_code=status.HTTP_200_OK,
    response_description="Access-token verification status.",
    summary="Verify an access token",
    description="Confirm that the supplied JWT belongs to an active account.",
    responses=documented_responses(status.HTTP_401_UNAUTHORIZED),
    tags=["Authentication"],
)
def token_check(current_user: User = Depends(get_current_user)):
    """Verify the authenticated user's access token."""

    return {
        "authenticated": True,
        "message": "Access token verified successfully",
        "subject": str(current_user.id),
    }


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    response_description="The current authenticated user profile.",
    summary="Get the current account profile",
    description="Retrieve the public profile fields for the authenticated account.",
    responses=documented_responses(status.HTTP_401_UNAUTHORIZED),
    tags=["Accounts"],
)
def get_my_profile(current_user: User = Depends(get_current_user)):
    """Retrieve the currently authenticated user's profile."""

    return current_user
