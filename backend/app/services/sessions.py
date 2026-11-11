from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.account import is_active_account
from app.core.config import settings
from app.core.opaque_tokens import generate_opaque_token, hash_opaque_token
from app.core.tokens import create_access_token
from app.models.auth import RefreshSession
from app.models.user import User
from app.schemas.auth import TokenResponse
from app.services.audit import add_audit_event


class InvalidRefreshToken(Exception):
    """Raised when a refresh token cannot be used."""


def lock_user_session_state(db: Session, user_id: UUID) -> User | None:
    """Serialize refresh-session issuance and revocation for one user."""

    return db.scalar(select(User).where(User.id == user_id).with_for_update())


def _create_session(
    db: Session,
    user: User,
    *,
    family_id: UUID | None = None,
) -> tuple[str, RefreshSession]:
    raw_token = generate_opaque_token()
    now = datetime.now(UTC)
    session = RefreshSession(
        user_id=user.id,
        family_id=family_id or uuid4(),
        token_hash=hash_opaque_token(raw_token),
        expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(session)
    return raw_token, session


def issue_tokens(
    db: Session,
    user: User,
    *,
    audit_action: str = "login",
) -> TokenResponse:
    """Issue an access token and a persisted rotating refresh token."""

    locked_user = lock_user_session_state(db, user.id)
    if locked_user is None or not is_active_account(locked_user):
        raise InvalidRefreshToken
    user = locked_user

    raw_refresh_token, _ = _create_session(db, user)
    user.last_login_at = datetime.now(UTC)
    add_audit_event(
        db,
        action=audit_action,
        outcome="success",
        actor_user_id=user.id,
        target_user_id=user.id,
    )
    db.commit()

    return TokenResponse(
        access_token=create_access_token(subject=str(user.id)),
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        refresh_token=raw_refresh_token,
        refresh_token_expires_in=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
    )


def rotate_refresh_token(db: Session, raw_token: str) -> TokenResponse:
    token_hash = hash_opaque_token(raw_token)
    session = db.scalar(
        select(RefreshSession).where(RefreshSession.token_hash == token_hash)
    )

    if session is None:
        raise InvalidRefreshToken

    user = lock_user_session_state(db, session.user_id)
    if user is None:
        raise InvalidRefreshToken

    session = db.scalar(
        select(RefreshSession)
        .where(RefreshSession.token_hash == token_hash)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    now = datetime.now(UTC)

    if session is None:
        raise InvalidRefreshToken

    if session.revoked_at is not None:
        sessions = db.scalars(
            select(RefreshSession).where(
                RefreshSession.family_id == session.family_id,
                RefreshSession.revoked_at.is_(None),
            )
        )
        for active_session in sessions:
            active_session.revoked_at = now
        db.commit()
        raise InvalidRefreshToken

    if session.expires_at <= now:
        session.revoked_at = now
        db.commit()
        raise InvalidRefreshToken

    if not is_active_account(user):
        session.revoked_at = now
        db.commit()
        raise InvalidRefreshToken

    session.revoked_at = now
    session.last_used_at = now
    raw_refresh_token, _ = _create_session(
        db,
        user,
        family_id=session.family_id,
    )
    add_audit_event(
        db,
        action="refresh_token_rotated",
        outcome="success",
        actor_user_id=user.id,
        target_user_id=user.id,
    )
    db.commit()

    return TokenResponse(
        access_token=create_access_token(subject=str(user.id)),
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        refresh_token=raw_refresh_token,
        refresh_token_expires_in=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
    )


def revoke_refresh_token(db: Session, raw_token: str, user: User) -> None:
    locked_user = lock_user_session_state(db, user.id)
    if locked_user is None:
        return

    session = db.scalar(
        select(RefreshSession)
        .where(
            RefreshSession.token_hash == hash_opaque_token(raw_token),
            RefreshSession.user_id == locked_user.id,
        )
        .with_for_update()
    )
    if session is not None and session.revoked_at is None:
        session.revoked_at = datetime.now(UTC)

    add_audit_event(
        db,
        action="logout",
        outcome="success",
        actor_user_id=locked_user.id,
        target_user_id=locked_user.id,
    )
    db.commit()


def revoke_all_sessions(db: Session, user_id: UUID) -> None:
    if lock_user_session_state(db, user_id) is None:
        return

    now = datetime.now(UTC)
    sessions = db.scalars(
        select(RefreshSession).where(
            RefreshSession.user_id == user_id,
            RefreshSession.revoked_at.is_(None),
        )
    )
    for session in sessions:
        session.revoked_at = now
