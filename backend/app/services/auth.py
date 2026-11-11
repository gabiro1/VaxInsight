from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, func, or_, select, text, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.account import is_active_account
from app.core.config import settings
from app.core.opaque_tokens import (
    generate_email_verification_otp,
    generate_opaque_token,
    hash_opaque_token,
)
from app.core.security import (
    DUMMY_PASSWORD_HASH,
    hash_password,
    verify_password,
)
from app.core.tokens import create_access_token
from app.models.auth import (
    AuditEvent,
    EmailVerificationToken,
    Invitation,
    PasswordResetToken,
    RefreshSession,
)
from app.models.narrative import Narrative, NarrativeRevision
from app.models.questions import ProfessionalResponse, QuestionAnalysis, VaccineQuestion
from app.models.review import (
    NarrativeAssignment,
    NarrativeReview,
    ReviewEvidenceReference,
)
from app.models.user import AccountStatus, User, UserRole
from app.schemas.auth import UserLogin, UserRegister
from app.services.audit import add_audit_event
from app.services.email import (
    EmailDeliveryError,
    send_email_verification_email,
    send_invitation_email,
    send_password_reset_email,
)
from app.services.sessions import lock_user_session_state, revoke_all_sessions


class EmailAlreadyRegistered(Exception):
    """Raised when an email address is already registered."""


class InvalidCredentials(Exception):
    """Raised when login credentials are invalid."""


class InvalidInvitation(Exception):
    """Raised when an invitation cannot be accepted."""


class InvalidPasswordResetToken(Exception):
    """Raised when a password reset token cannot be used."""


class InvalidEmailVerificationToken(Exception):
    """Raised when an email verification code cannot be used."""


class InvitationNotRevocable(Exception):
    """Raised when an invitation is no longer pending."""


class AdministratorSelfModificationError(Exception):
    """Raised when an administrator attempts to remove their own privileges."""


class LastActiveAdministratorError(Exception):
    """Raised when an operation would leave no active administrator."""


class InvalidAccountStatus(Exception):
    """Raised when an unsupported account status is requested."""


def _lock_administrator_management(db: Session, target: User) -> None:
    """Serialize administrator account changes and refresh the target."""

    db.execute(
        text("SELECT pg_advisory_xact_lock(:lock_key)"),
        {"lock_key": 72419031},
    )
    db.refresh(target)


def _active_administrator_count(db: Session) -> int:
    """Count accounts currently authorized as active administrators."""

    return (
        db.scalar(
            select(func.count(User.id)).where(
                User.role == UserRole.ADMINISTRATOR.value,
                User.status == AccountStatus.ACTIVE.value,
                User.is_active.is_(True),
            )
        )
        or 0
    )


def _reject_account_change(db: Session, error: type[Exception]) -> None:
    """Roll back a rejected change and release its transaction-level lock."""

    db.rollback()
    raise error()


def _invalidate_password_reset_tokens(
    db: Session,
    user_id,
    now: datetime,
) -> None:
    """Invalidate every unused password-reset token for a user."""

    db.execute(
        update(PasswordResetToken)
        .where(
            PasswordResetToken.user_id == user_id,
            PasswordResetToken.used_at.is_(None),
        )
        .values(used_at=now)
    )


def _email_verification_secret(email: str, otp: str) -> str:
    return f"{email.strip().lower()}:{otp}"


def _generate_email_verification_otp(
    db: Session,
    email: str,
) -> tuple[str, str]:
    """Generate an OTP whose stored digest does not collide with old records."""

    for _ in range(10):
        otp = generate_email_verification_otp()
        token_hash = hash_opaque_token(_email_verification_secret(email, otp))
        if (
            db.scalar(
                select(EmailVerificationToken.id).where(
                    EmailVerificationToken.token_hash == token_hash
                )
            )
            is None
        ):
            return otp, token_hash

    raise RuntimeError("Could not generate a unique email verification code")


def _is_unique_email_error(error: IntegrityError) -> bool:
    original_error = getattr(error, "orig", None)
    sqlstate = getattr(original_error, "sqlstate", None)
    message = str(original_error or error).lower()

    return (
        (sqlstate == "23505" and "email" in message)
        or "users_email" in message
        or "unique constraint" in message
    )


def register_user(db: Session, user_data: UserRegister) -> User:
    """Create a pending community account with no staff privileges."""

    existing_user = db.scalar(select(User).where(User.email == user_data.email))
    if existing_user:
        raise EmailAlreadyRegistered

    now = datetime.now(UTC)
    user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hash_password(user_data.password),
        is_active=False,
        status=AccountStatus.PENDING.value,
        role=UserRole.COMMUNITY_MEMBER.value,
        password_changed_at=now,
    )
    db.add(user)

    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        if _is_unique_email_error(error):
            raise EmailAlreadyRegistered from None
        raise

    db.refresh(user)
    return user


def create_email_verification(
    db: Session,
    user: User,
) -> EmailVerificationToken:
    """Create and deliver a one-time email verification code."""

    now = datetime.now(UTC)

    db.execute(
        update(EmailVerificationToken)
        .where(
            EmailVerificationToken.user_id == user.id,
            EmailVerificationToken.used_at.is_(None),
        )
        .values(used_at=now)
    )

    raw_otp, otp_hash = _generate_email_verification_otp(db, user.email)
    token = EmailVerificationToken(
        user_id=user.id,
        token_hash=otp_hash,
        expires_at=now + timedelta(minutes=settings.EMAIL_VERIFICATION_EXPIRE_MINUTES),
    )
    db.add(token)
    db.flush()

    try:
        send_email_verification_email(
            user.email,
            raw_otp,
            token.expires_at,
        )
        add_audit_event(
            db,
            action="email_verification_requested",
            outcome="success",
            target_user_id=user.id,
        )
        db.commit()
    except EmailDeliveryError:
        db.rollback()
        raise

    return token


def request_email_verification(db: Session, email: str) -> bool:
    """Resend verification without revealing account existence."""

    user = db.scalar(select(User).where(User.email == email))

    if user is None or user.status != AccountStatus.PENDING.value:
        return False

    create_email_verification(db, user)
    return True


def create_invitation(
    db: Session,
    *,
    email: str,
    role: str,
    invited_by: User,
) -> Invitation:
    """Create and deliver a single-use invitation for an approved role."""

    staff_roles = {
        UserRole.CHW.value,
        UserRole.REVIEWER.value,
        UserRole.ADMINISTRATOR.value,
    }
    if role not in staff_roles:
        raise InvalidInvitation

    existing_user = db.scalar(select(User).where(User.email == email))
    if existing_user:
        raise EmailAlreadyRegistered

    now = datetime.now(UTC)

    open_invitations = db.scalars(
        select(Invitation).where(
            Invitation.email == email,
            Invitation.accepted_at.is_(None),
            Invitation.revoked_at.is_(None),
        )
    )

    for invitation in open_invitations:
        invitation.revoked_at = now

    raw_token = generate_opaque_token()

    invitation = Invitation(
        email=email,
        role=role,
        token_hash=hash_opaque_token(raw_token),
        invited_by_id=invited_by.id,
        expires_at=now + timedelta(hours=settings.INVITATION_EXPIRE_HOURS),
    )
    db.add(invitation)
    db.flush()

    try:
        send_invitation_email(
            email,
            raw_token,
            invitation.expires_at,
            role,
        )
        add_audit_event(
            db,
            action="invitation_created",
            outcome="success",
            actor_user_id=invited_by.id,
            details={"role": role},
        )
        db.commit()
    except EmailDeliveryError:
        db.rollback()
        raise

    db.refresh(invitation)
    return invitation


def revoke_invitation(
    db: Session,
    *,
    invitation_id,
    revoked_by: User,
) -> Invitation | None:
    """Revoke one pending invitation and audit the administrator action."""

    invitation = db.scalar(
        select(Invitation).where(Invitation.id == invitation_id).with_for_update()
    )
    now = datetime.now(UTC)

    if invitation is None:
        return None
    expires_at = invitation.expires_at
    if expires_at.tzinfo is None or expires_at.utcoffset() is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if (
        invitation.accepted_at is not None
        or invitation.revoked_at is not None
        or expires_at <= now
    ):
        raise InvitationNotRevocable

    invitation.revoked_at = now
    add_audit_event(
        db,
        action="invitation_revoked",
        outcome="success",
        actor_user_id=revoked_by.id,
        details={"role": invitation.role},
    )
    db.commit()
    db.refresh(invitation)
    return invitation


def accept_invitation(
    db: Session,
    token_value: str,
    password: str,
) -> User:
    """Create an active, verified account from a valid invitation."""

    invitation = db.scalar(
        select(Invitation)
        .where(Invitation.token_hash == hash_opaque_token(token_value))
        .with_for_update()
    )

    now = datetime.now(UTC)

    if (
        invitation is None
        or invitation.accepted_at is not None
        or invitation.revoked_at is not None
        or invitation.expires_at <= now
    ):
        raise InvalidInvitation

    existing_user = db.scalar(select(User).where(User.email == invitation.email))

    if existing_user:
        raise EmailAlreadyRegistered

    user = User(
        email=invitation.email,
        hashed_password=hash_password(password),
        is_active=True,
        status=AccountStatus.ACTIVE.value,
        role=invitation.role,
        email_verified_at=now,
        password_changed_at=now,
    )

    db.add(user)
    invitation.accepted_at = now
    db.flush()

    add_audit_event(
        db,
        action="invitation_accepted",
        outcome="success",
        target_user_id=user.id,
        details={"role": invitation.role},
    )

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise EmailAlreadyRegistered from None

    db.refresh(user)
    return user


def authenticate_user_account(
    db: Session,
    login_data: UserLogin,
) -> User:
    """Authenticate credentials while keeping unknown-email timing comparable."""

    user = db.scalar(
        select(User).where(User.email == login_data.email).with_for_update()
    )

    password_hash_value = user.hashed_password if user else DUMMY_PASSWORD_HASH
    password_valid = verify_password(
        login_data.password,
        password_hash_value,
    )

    if not user or not password_valid or not is_active_account(user):
        raise InvalidCredentials

    return user


def authenticate_user(
    db: Session,
    login_data: UserLogin,
) -> str:
    """Authenticate a user and return an access token."""

    user = authenticate_user_account(db, login_data)
    return create_access_token(subject=str(user.id))


def change_password(
    db: Session,
    user: User,
    current_password: str,
    new_password: str,
) -> None:
    """Change password and invalidate existing reset tokens and sessions."""

    locked_user = lock_user_session_state(db, user.id)
    if locked_user is None or not is_active_account(locked_user):
        raise InvalidCredentials
    user = locked_user

    if not verify_password(current_password, user.hashed_password):
        raise InvalidCredentials

    now = datetime.now(UTC)

    user.hashed_password = hash_password(new_password)
    user.password_changed_at = now

    _invalidate_password_reset_tokens(db, user.id, now)
    revoke_all_sessions(db, user.id)

    add_audit_event(
        db,
        action="password_changed",
        outcome="success",
        actor_user_id=user.id,
        target_user_id=user.id,
    )

    db.commit()


def request_password_reset(
    db: Session,
    email: str,
) -> bool:
    """Send a reset email when the account exists without exposing that fact."""

    user = db.scalar(select(User).where(User.email == email))

    if user is None or not is_active_account(user):
        return False

    now = datetime.now(UTC)

    db.execute(
        update(PasswordResetToken)
        .where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at.is_(None),
        )
        .values(used_at=now)
    )

    raw_token = generate_opaque_token()

    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=hash_opaque_token(raw_token),
        expires_at=now + timedelta(minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES),
    )

    db.add(reset_token)
    db.flush()

    try:
        send_password_reset_email(
            user.email,
            raw_token,
            reset_token.expires_at,
        )
        add_audit_event(
            db,
            action="password_reset_requested",
            outcome="success",
            target_user_id=user.id,
        )
        db.commit()
    except EmailDeliveryError:
        db.rollback()
        raise

    return True


def confirm_password_reset(
    db: Session,
    token_value: str,
    new_password: str,
) -> None:
    """Reset password and invalidate every outstanding reset token and session."""

    token_hash = hash_opaque_token(token_value)
    reset_token = db.scalar(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
    )

    if reset_token is None:
        raise InvalidPasswordResetToken

    user = lock_user_session_state(db, reset_token.user_id)

    if user is None or not is_active_account(user):
        raise InvalidPasswordResetToken

    reset_token = db.scalar(
        select(PasswordResetToken)
        .where(PasswordResetToken.token_hash == token_hash)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    now = datetime.now(UTC)

    if (
        reset_token is None
        or reset_token.used_at is not None
        or reset_token.expires_at <= now
    ):
        raise InvalidPasswordResetToken

    user.hashed_password = hash_password(new_password)
    user.password_changed_at = now

    _invalidate_password_reset_tokens(db, user.id, now)
    revoke_all_sessions(db, user.id)

    add_audit_event(
        db,
        action="password_reset_completed",
        outcome="success",
        target_user_id=user.id,
    )

    db.commit()


def verify_email(
    db: Session,
    email: str,
    otp: str,
) -> User:
    """Verify an email OTP and activate a pending account."""

    token_hash = hash_opaque_token(_email_verification_secret(email, otp))
    verification_token = db.scalar(
        select(EmailVerificationToken).where(
            EmailVerificationToken.token_hash == token_hash
        )
    )

    if verification_token is None:
        raise InvalidEmailVerificationToken

    user = lock_user_session_state(db, verification_token.user_id)

    if user is None:
        raise InvalidEmailVerificationToken

    verification_token = db.scalar(
        select(EmailVerificationToken)
        .where(EmailVerificationToken.token_hash == token_hash)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    now = datetime.now(UTC)

    if (
        verification_token is None
        or verification_token.used_at is not None
        or verification_token.expires_at <= now
    ):
        raise InvalidEmailVerificationToken

    user.email_verified_at = now

    if user.status == AccountStatus.PENDING.value:
        user.status = AccountStatus.ACTIVE.value
        user.is_active = True

    verification_token.used_at = now

    add_audit_event(
        db,
        action="email_verified",
        outcome="success",
        target_user_id=user.id,
    )

    db.commit()
    db.refresh(user)

    return user


def request_email_change(
    db: Session,
    user: User,
    new_email: str,
) -> None:
    """Start an email change; the new address must be verified before reactivation."""

    existing_user = db.scalar(select(User).where(User.email == new_email))

    if existing_user and existing_user.id != user.id:
        raise EmailAlreadyRegistered

    now = datetime.now(UTC)

    user.email = new_email
    user.email_verified_at = None
    user.status = AccountStatus.PENDING.value
    user.is_active = False
    # Invalidate access tokens while the account is pending email verification.
    user.password_changed_at = now

    revoke_all_sessions(db, user.id)

    db.execute(
        update(EmailVerificationToken)
        .where(
            EmailVerificationToken.user_id == user.id,
            EmailVerificationToken.used_at.is_(None),
        )
        .values(used_at=now)
    )

    raw_otp, otp_hash = _generate_email_verification_otp(db, new_email)

    verification_token = EmailVerificationToken(
        user_id=user.id,
        token_hash=otp_hash,
        expires_at=now + timedelta(minutes=settings.EMAIL_VERIFICATION_EXPIRE_MINUTES),
    )

    db.add(verification_token)
    db.flush()

    try:
        send_email_verification_email(
            new_email,
            raw_otp,
            verification_token.expires_at,
        )
        add_audit_event(
            db,
            action="email_change_requested",
            outcome="success",
            actor_user_id=user.id,
            target_user_id=user.id,
        )
        db.commit()
    except EmailDeliveryError:
        db.rollback()
        raise


def change_account_status(
    db: Session,
    *,
    actor: User,
    target: User,
    new_status: str,
) -> None:
    """Update account status while preserving administrator availability."""

    allowed_statuses = {
        AccountStatus.ACTIVE.value,
        AccountStatus.SUSPENDED.value,
        AccountStatus.DEACTIVATED.value,
        AccountStatus.DELETED.value,
    }

    if new_status not in allowed_statuses:
        raise InvalidAccountStatus

    # Serialize administrator status changes before reading current state.
    _lock_administrator_management(db, target)

    # An administrator cannot deactivate their own account.
    if actor.id == target.id and new_status != AccountStatus.ACTIVE.value:
        _reject_account_change(db, AdministratorSelfModificationError)

    target_is_active_admin = (
        target.role == UserRole.ADMINISTRATOR.value
        and target.status == AccountStatus.ACTIVE.value
        and target.is_active is True
    )

    # Never allow the last active administrator to lose active status.
    if target_is_active_admin and new_status != AccountStatus.ACTIVE.value:  # noqa: SIM102
        if _active_administrator_count(db) <= 1:
            _reject_account_change(db, LastActiveAdministratorError)

    target.status = new_status
    target.is_active = new_status == AccountStatus.ACTIVE.value

    if not target.is_active:
        revoke_all_sessions(db, target.id)

    add_audit_event(
        db,
        action="account_status_changed",
        outcome="success",
        actor_user_id=actor.id,
        target_user_id=target.id,
        details={"status": new_status},
    )

    db.commit()


def change_user_role(
    db: Session,
    *,
    actor: User,
    target: User,
    role: str,
) -> None:
    """Change a user's role while preserving administrator availability."""

    if role not in {item.value for item in UserRole}:
        raise InvalidInvitation

    # Serialize administrator role changes before reading current state.
    _lock_administrator_management(db, target)

    # An administrator cannot remove their own administrator role.
    if actor.id == target.id and role != UserRole.ADMINISTRATOR.value:
        _reject_account_change(db, AdministratorSelfModificationError)

    target_is_active_admin = (
        target.role == UserRole.ADMINISTRATOR.value
        and target.status == AccountStatus.ACTIVE.value
        and target.is_active is True
    )

    # Never allow the last active administrator to be demoted.
    if target_is_active_admin and role != UserRole.ADMINISTRATOR.value:  # noqa: SIM102
        if _active_administrator_count(db) <= 1:
            _reject_account_change(db, LastActiveAdministratorError)

    target.role = role

    add_audit_event(
        db,
        action="account_role_changed",
        outcome="success",
        actor_user_id=actor.id,
        target_user_id=target.id,
        details={"role": role},
    )

    db.commit()


def delete_account(db: Session, user: User) -> None:
    """Permanently remove an account and every row that references it."""

    locked_user = db.scalar(
        select(User).where(User.id == user.id).with_for_update()
    )
    if locked_user is None:
        return

    if (
        locked_user.role == UserRole.ADMINISTRATOR.value
        and locked_user.status == AccountStatus.ACTIVE.value
        and locked_user.is_active
    ):
        _lock_administrator_management(db, locked_user)
        if _active_administrator_count(db) <= 1:
            _reject_account_change(db, LastActiveAdministratorError)

    user_id = locked_user.id
    owned_narrative_ids = select(Narrative.id).where(
        Narrative.submitted_by_id == user_id
    )
    affected_assignment_ids = select(NarrativeAssignment.id).where(
        or_(
            NarrativeAssignment.narrative_id.in_(owned_narrative_ids),
            NarrativeAssignment.reviewer_id == user_id,
            NarrativeAssignment.assigned_by_user_id == user_id,
            NarrativeAssignment.revoked_by_user_id == user_id,
        )
    )
    affected_review_ids = select(NarrativeReview.id).where(
        or_(
            NarrativeReview.assignment_id.in_(affected_assignment_ids),
            NarrativeReview.narrative_id.in_(owned_narrative_ids),
            NarrativeReview.reviewer_id == user_id,
        )
    )
    owned_question_ids = select(VaccineQuestion.id).where(
        VaccineQuestion.asked_by_user_id == user_id
    )

    try:
        db.execute(
            delete(ReviewEvidenceReference).where(
                ReviewEvidenceReference.review_id.in_(affected_review_ids)
            )
        )
        db.execute(
            delete(NarrativeReview).where(NarrativeReview.id.in_(affected_review_ids))
        )
        db.execute(
            delete(NarrativeAssignment).where(
                NarrativeAssignment.id.in_(affected_assignment_ids)
            )
        )
        db.execute(
            delete(NarrativeRevision).where(
                or_(
                    NarrativeRevision.narrative_id.in_(owned_narrative_ids),
                    NarrativeRevision.changed_by_user_id == user_id,
                )
            )
        )
        db.execute(
            delete(Narrative).where(Narrative.submitted_by_id == user_id)
        )

        # Questions are owned data and must not survive a hard account deletion.
        # Responses written by the deleted account on another user's question are
        # retained by the database and their professional_user_id is set to NULL.
        db.execute(
            delete(ProfessionalResponse).where(
                ProfessionalResponse.question_id.in_(owned_question_ids)
            )
        )
        db.execute(
            delete(QuestionAnalysis).where(
                QuestionAnalysis.question_id.in_(owned_question_ids)
            )
        )
        db.execute(
            delete(VaccineQuestion).where(VaccineQuestion.asked_by_user_id == user_id)
        )

        db.execute(
            delete(Invitation).where(
                or_(
                    Invitation.invited_by_id == user_id,
                    Invitation.email == locked_user.email,
                )
            )
        )
        for model in (
            RefreshSession,
            PasswordResetToken,
            EmailVerificationToken,
        ):
            db.execute(delete(model).where(model.user_id == user_id))

        db.execute(
            delete(AuditEvent).where(
                or_(
                    AuditEvent.actor_user_id == user_id,
                    AuditEvent.target_user_id == user_id,
                )
            )
        )
        # These creator/approver references use ON DELETE SET NULL. Explicitly
        # leaving them untouched preserves published content and source metadata.
        db.execute(delete(User).where(User.id == user_id))
        db.commit()
    except Exception:
        db.rollback()
        raise
