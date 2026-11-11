from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from app.core.opaque_tokens import hash_opaque_token
from app.models.auth import Invitation, RefreshSession
from app.models.user import AccountStatus, User, UserRole
from app.services.auth import (
    EmailAlreadyRegistered,
    InvalidInvitation,
    accept_invitation,
    create_invitation,
)
from app.services.sessions import InvalidRefreshToken, rotate_refresh_token


def make_admin() -> User:
    return User(
        id=uuid4(),
        email="admin@example.com",
        hashed_password="argon2-hash",
        is_active=True,
        status=AccountStatus.ACTIVE.value,
        role=UserRole.ADMINISTRATOR.value,
    )


def test_create_invitation_stores_only_token_hash():
    db = MagicMock()
    db.scalar.return_value = None
    db.scalars.return_value = []
    admin = make_admin()

    with patch("app.services.auth.send_invitation_email") as send_email:
        invitation = create_invitation(
            db,
            email="chw@example.com",
            role=UserRole.CHW.value,
            invited_by=admin,
        )

    raw_token = send_email.call_args.args[1]

    assert invitation.token_hash == hash_opaque_token(raw_token)
    assert invitation.token_hash != raw_token
    assert send_email.call_args.args[0] == "chw@example.com"
    db.commit.assert_called_once()


def test_create_invitation_rejects_community_role():
    db = MagicMock()

    with pytest.raises(InvalidInvitation):
        create_invitation(
            db,
            email="community@example.com",
            role=UserRole.COMMUNITY_MEMBER.value,
            invited_by=make_admin(),
        )

    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_accept_invitation_is_single_use():
    token = "test-invitation-token-123456789012345678901234"

    invitation = Invitation(
        id=uuid4(),
        email="reviewer@example.com",
        role=UserRole.REVIEWER.value,
        token_hash=hash_opaque_token(token),
        invited_by_id=uuid4(),
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )

    db = MagicMock()
    db.scalar.side_effect = [invitation, None]

    with patch("app.services.auth.hash_password", return_value="new-hash"):
        user = accept_invitation(db, token, "StrongPassword123!")

    assert user.email == "reviewer@example.com"
    assert user.role == UserRole.REVIEWER.value
    assert user.status == AccountStatus.ACTIVE.value
    assert invitation.accepted_at is not None
    db.commit.assert_called_once()


def test_expired_invitation_is_rejected():
    token = "expired-token-123456789012345678901234"

    invitation = Invitation(
        id=uuid4(),
        email="expired@example.com",
        role=UserRole.CHW.value,
        token_hash=hash_opaque_token(token),
        invited_by_id=uuid4(),
        expires_at=datetime.now(UTC) - timedelta(minutes=1),
    )

    db = MagicMock()
    db.scalar.return_value = invitation

    with pytest.raises(InvalidInvitation):
        accept_invitation(db, token, "StrongPassword123!")


def test_revoked_invitation_is_rejected():
    token = "revoked-invitation-token-123456789012345678901234"

    invitation = Invitation(
        id=uuid4(),
        email="revoked@example.com",
        role=UserRole.CHW.value,
        token_hash=hash_opaque_token(token),
        invited_by_id=uuid4(),
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        revoked_at=datetime.now(UTC),
    )

    db = MagicMock()
    db.scalar.return_value = invitation

    with pytest.raises(InvalidInvitation):
        accept_invitation(
            db,
            token,
            "StrongPassword123!",
        )

    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_invitation_rejects_existing_account():
    db = MagicMock()

    db.scalar.return_value = User(
        id=uuid4(),
        email="existing@example.com",
        hashed_password="hash",
        is_active=True,
        status=AccountStatus.ACTIVE.value,
    )

    with pytest.raises(EmailAlreadyRegistered):
        create_invitation(
            db,
            email="existing@example.com",
            role=UserRole.CHW.value,
            invited_by=make_admin(),
        )


def test_reused_refresh_token_revokes_remaining_family_sessions():
    family_id = uuid4()

    old_session = RefreshSession(
        id=uuid4(),
        user_id=uuid4(),
        family_id=family_id,
        token_hash=hash_opaque_token("refresh-token-123456789012345678901234"),
        expires_at=datetime.now(UTC) + timedelta(days=1),
        revoked_at=datetime.now(UTC),
    )

    active_session = RefreshSession(
        id=uuid4(),
        user_id=old_session.user_id,
        family_id=family_id,
        token_hash=hash_opaque_token("other-refresh-token"),
        expires_at=datetime.now(UTC) + timedelta(days=1),
    )

    db = MagicMock()
    db.scalar.return_value = old_session
    db.scalars.return_value = [active_session]

    with pytest.raises(InvalidRefreshToken):
        rotate_refresh_token(
            db,
            "refresh-token-123456789012345678901234",
        )

    assert active_session.revoked_at is not None
    db.commit.assert_called_once()
