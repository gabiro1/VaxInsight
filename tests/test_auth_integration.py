from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from app.core.config import settings
from app.core.opaque_tokens import generate_opaque_token, hash_opaque_token
from app.core.security import hash_password
from app.database.database import SessionLocal
from app.main import app
from app.models.auth import (
    AuditEvent,
    EmailVerificationToken,
    PasswordResetToken,
    RateLimitBucket,
    RefreshSession,
)
from app.models.user import AccountStatus, User, UserRole
from app.services.auth import (
    InvalidEmailVerificationToken,
    InvalidPasswordResetToken,
    change_account_status,
    change_password,
    confirm_password_reset,
    create_email_verification,
    request_password_reset,
    verify_email,
)
from app.services.rate_limit import _bucket_key
from app.services.sessions import (
    InvalidRefreshToken,
    issue_tokens,
    rotate_refresh_token,
)
from fastapi.testclient import TestClient
from sqlalchemy import delete, or_
from starlette.requests import Request

client = TestClient(app)


@pytest.mark.integration
def test_postgres_refresh_rotation_persists_and_revokes_sessions():
    db = SessionLocal()
    user_id = uuid4()
    email = f"integration-{user_id}@example.com"

    try:
        user = User(
            id=user_id,
            email=email,
            hashed_password=hash_password("StrongPassword123!"),
            is_active=True,
            status=AccountStatus.ACTIVE.value,
            role=UserRole.CHW.value,
            email_verified_at=datetime.now(UTC),
            password_changed_at=datetime.now(UTC),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        first_tokens = issue_tokens(db, user)
        rotated_tokens = rotate_refresh_token(db, first_tokens.refresh_token)

        assert rotated_tokens.refresh_token != first_tokens.refresh_token

        # The original refresh token must not be reusable.
        with pytest.raises(InvalidRefreshToken):
            rotate_refresh_token(db, first_tokens.refresh_token)

        # Replaying it must revoke the remaining session in its family.
        sessions = db.query(RefreshSession).filter_by(user_id=user.id).all()

        assert len(sessions) == 2
        assert all(session.revoked_at is not None for session in sessions)

    finally:
        db.rollback()
        db.execute(delete(AuditEvent).where(AuditEvent.target_user_id == user_id))
        db.execute(delete(RefreshSession).where(RefreshSession.user_id == user_id))
        db.execute(delete(User).where(User.id == user_id))
        db.commit()
        db.close()


@pytest.mark.integration
def test_postgres_login_refresh_profile_and_logout_flow():
    db = SessionLocal()
    user_id = uuid4()
    email = f"api-integration-{user_id}@example.com"

    try:
        user = User(
            id=user_id,
            email=email,
            hashed_password=hash_password("StrongPassword123!"),
            is_active=True,
            status=AccountStatus.ACTIVE.value,
            role=UserRole.CHW.value,
            email_verified_at=datetime.now(UTC),
            password_changed_at=datetime.now(UTC),
        )
        db.add(user)
        db.commit()

        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": email,
                "password": "StrongPassword123!",
            },
        )
        assert login_response.status_code == 200

        login_data = login_response.json()
        access_token = login_data["access_token"]
        refresh_token = login_data["refresh_token"]

        profile_response = client.get(
            "/api/v1/auth/me",
            headers={
                "Authorization": f"Bearer {access_token}",
            },
        )
        assert profile_response.status_code == 200
        assert profile_response.json()["email"] == email

        refresh_response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_response.status_code == 200

        refresh_data = refresh_response.json()

        logout_response = client.post(
            "/api/v1/auth/logout",
            json={
                "refresh_token": refresh_data["refresh_token"],
            },
            headers={
                "Authorization": f"Bearer {refresh_data['access_token']}",
            },
        )
        assert logout_response.status_code == 200
        assert logout_response.json() == {"message": "Logout successful"}

        rejected_response = client.post(
            "/api/v1/auth/refresh",
            json={
                "refresh_token": refresh_data["refresh_token"],
            },
        )
        assert rejected_response.status_code == 401

    finally:
        db.rollback()
        db.execute(
            delete(AuditEvent).where(
                or_(
                    AuditEvent.actor_user_id == user_id,
                    AuditEvent.target_user_id == user_id,
                )
            )
        )
        db.execute(delete(RefreshSession).where(RefreshSession.user_id == user_id))
        db.execute(delete(User).where(User.id == user_id))
        db.commit()
        db.close()


@pytest.mark.integration
def test_password_change_invalidates_outstanding_reset_token(monkeypatch):
    db = SessionLocal()
    user_id = uuid4()
    email = f"password-change-{user_id}@example.com"
    captured = {}

    def fake_send_reset_email(email, raw_token, expires_at):
        captured["token"] = raw_token

    monkeypatch.setattr(
        "app.services.auth.send_password_reset_email",
        fake_send_reset_email,
    )

    try:
        user = User(
            id=user_id,
            email=email,
            hashed_password=hash_password("StrongPassword123!"),
            is_active=True,
            status=AccountStatus.ACTIVE.value,
            role=UserRole.CHW.value,
            email_verified_at=datetime.now(UTC),
            password_changed_at=datetime.now(UTC),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Request a password-reset token.
        assert request_password_reset(db, email) is True
        assert "token" in captured

        # Change the password through the normal password-change service.
        change_password(
            db,
            user,
            "StrongPassword123!",
            "AnotherStrongPassword456!",
        )

        # The previously issued reset token must no longer work.
        with pytest.raises(InvalidPasswordResetToken):
            confirm_password_reset(
                db,
                captured["token"],
                "ThirdStrongPassword789!",
            )

    finally:
        db.rollback()
        db.execute(
            delete(AuditEvent).where(
                or_(
                    AuditEvent.actor_user_id == user_id,
                    AuditEvent.target_user_id == user_id,
                )
            )
        )
        db.execute(
            delete(PasswordResetToken).where(PasswordResetToken.user_id == user_id)
        )
        db.execute(delete(RefreshSession).where(RefreshSession.user_id == user_id))
        db.execute(delete(User).where(User.id == user_id))
        db.commit()
        db.close()


@pytest.mark.integration
def test_password_reset_invalidates_other_outstanding_reset_tokens():
    db = SessionLocal()
    user_id = uuid4()
    email = f"reset-invalidation-{user_id}@example.com"

    first_raw_token = generate_opaque_token()
    second_raw_token = generate_opaque_token()

    try:
        user = User(
            id=user_id,
            email=email,
            hashed_password=hash_password("InitialPassword123!"),
            is_active=True,
            status=AccountStatus.ACTIVE.value,
            email_verified_at=datetime.now(UTC),
        )
        db.add(user)
        db.flush()

        now = datetime.now(UTC)

        first_token = PasswordResetToken(
            user_id=user.id,
            token_hash=hash_opaque_token(first_raw_token),
            expires_at=now + timedelta(minutes=30),
        )

        second_token = PasswordResetToken(
            user_id=user.id,
            token_hash=hash_opaque_token(second_raw_token),
            expires_at=now + timedelta(minutes=30),
        )

        db.add_all([first_token, second_token])
        db.commit()

        # The first token successfully resets the password.
        confirm_password_reset(
            db,
            first_raw_token,
            "NewPassword123!",
        )

        # The second outstanding token must now be invalid.
        with pytest.raises(InvalidPasswordResetToken):
            confirm_password_reset(
                db,
                second_raw_token,
                "AnotherPassword123!",
            )

    finally:
        db.rollback()
        db.execute(
            delete(AuditEvent).where(
                or_(
                    AuditEvent.actor_user_id == user_id,
                    AuditEvent.target_user_id == user_id,
                )
            )
        )
        db.execute(
            delete(PasswordResetToken).where(PasswordResetToken.user_id == user_id)
        )
        db.execute(delete(RefreshSession).where(RefreshSession.user_id == user_id))
        db.execute(delete(User).where(User.id == user_id))
        db.commit()
        db.close()


@pytest.mark.integration
def test_suspending_account_revokes_existing_refresh_token():
    db = SessionLocal()
    admin_id = uuid4()
    user_id = uuid4()

    admin_email = f"admin-{admin_id}@example.com"
    user_email = f"suspended-{user_id}@example.com"

    try:
        admin = User(
            id=admin_id,
            email=admin_email,
            hashed_password=hash_password("AdminPassword123!"),
            is_active=True,
            status=AccountStatus.ACTIVE.value,
            role=UserRole.ADMINISTRATOR.value,
            email_verified_at=datetime.now(UTC),
        )

        user = User(
            id=user_id,
            email=user_email,
            hashed_password=hash_password("StrongPassword123!"),
            is_active=True,
            status=AccountStatus.ACTIVE.value,
            role=UserRole.CHW.value,
            email_verified_at=datetime.now(UTC),
        )

        db.add_all([admin, user])
        db.commit()
        db.refresh(admin)
        db.refresh(user)

        # Issue a valid refresh token while the user is active.
        tokens = issue_tokens(db, user)
        refresh_token = tokens.refresh_token

        # Suspend the user through the actual account-management service.
        change_account_status(
            db,
            actor=admin,
            target=user,
            new_status=AccountStatus.SUSPENDED.value,
        )

        # Confirm the existing database session was revoked.
        session = db.query(RefreshSession).filter_by(user_id=user_id).one()

        assert session.revoked_at is not None

        # The previously issued refresh token must now be rejected.
        with pytest.raises(InvalidRefreshToken):
            rotate_refresh_token(db, refresh_token)

    finally:
        db.rollback()

        db.execute(
            delete(AuditEvent).where(
                or_(
                    AuditEvent.actor_user_id.in_([admin_id, user_id]),
                    AuditEvent.target_user_id.in_([admin_id, user_id]),
                )
            )
        )
        db.execute(
            delete(RefreshSession).where(
                RefreshSession.user_id.in_([admin_id, user_id])
            )
        )
        db.execute(delete(User).where(User.id.in_([admin_id, user_id])))

        db.commit()
        db.close()


@pytest.mark.integration
def test_logout_all_revokes_every_refresh_session():
    db = SessionLocal()
    user_id = uuid4()
    email = f"logout-all-{user_id}@example.com"

    try:
        user = User(
            id=user_id,
            email=email,
            hashed_password=hash_password("StrongPassword123!"),
            is_active=True,
            status=AccountStatus.ACTIVE.value,
            role=UserRole.CHW.value,
            email_verified_at=datetime.now(UTC),
            password_changed_at=datetime.now(UTC),
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        # Simulate two separate login sessions (e.g. laptop and phone).
        first_tokens = issue_tokens(db, user)
        second_tokens = issue_tokens(db, user)

        assert first_tokens.refresh_token != second_tokens.refresh_token

        # Call the real logout-all API endpoint.
        response = client.post(
            "/api/v1/auth/logout-all",
            headers={
                "Authorization": f"Bearer {first_tokens.access_token}",
            },
        )

        assert response.status_code == 200
        assert response.json() == {"message": "All sessions logged out successfully"}

        # Both refresh tokens must now be rejected.
        with pytest.raises(InvalidRefreshToken):
            rotate_refresh_token(db, first_tokens.refresh_token)

        with pytest.raises(InvalidRefreshToken):
            rotate_refresh_token(db, second_tokens.refresh_token)

        # Confirm that every persisted session is revoked.
        sessions = db.query(RefreshSession).filter_by(user_id=user_id).all()

        assert len(sessions) == 2
        assert all(session.revoked_at is not None for session in sessions)

    finally:
        db.rollback()

        db.execute(
            delete(AuditEvent).where(
                or_(
                    AuditEvent.actor_user_id == user_id,
                    AuditEvent.target_user_id == user_id,
                )
            )
        )
        db.execute(delete(RefreshSession).where(RefreshSession.user_id == user_id))
        db.execute(delete(User).where(User.id == user_id))

        db.commit()
        db.close()


@pytest.mark.integration
def test_postgres_email_verification_activates_pending_account(monkeypatch):
    db = SessionLocal()
    user_id = uuid4()
    email = f"email-verification-{user_id}@example.com"
    captured_tokens = []

    def capture_verification_email(recipient, raw_otp, expires_at):
        captured_tokens.append(raw_otp)

    monkeypatch.setattr(
        "app.services.auth.send_email_verification_email",
        capture_verification_email,
    )

    try:
        user = User(
            id=user_id,
            email=email,
            hashed_password=hash_password("StrongPassword123!"),
            is_active=False,
            status=AccountStatus.PENDING.value,
            role=UserRole.CHW.value,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        create_email_verification(db, user)

        assert len(captured_tokens) == 1

        raw_otp = captured_tokens[0]
        assert raw_otp.isdigit()
        assert len(raw_otp) == 6

        stored_token = db.query(EmailVerificationToken).filter_by(user_id=user_id).one()

        # The database must never store the raw verification code.
        assert stored_token.token_hash == hash_opaque_token(f"{email}:{raw_otp}")
        assert stored_token.token_hash != raw_otp

        verified_user = verify_email(db, email, raw_otp)

        assert verified_user.status == AccountStatus.ACTIVE.value
        assert verified_user.is_active is True
        assert verified_user.email_verified_at is not None
        assert stored_token.used_at is not None

    finally:
        db.rollback()
        db.execute(
            delete(EmailVerificationToken).where(
                EmailVerificationToken.user_id == user_id
            )
        )
        db.execute(delete(AuditEvent).where(AuditEvent.target_user_id == user_id))
        db.execute(delete(User).where(User.id == user_id))
        db.commit()
        db.close()


@pytest.mark.integration
def test_postgres_expired_email_verification_token_is_rejected(monkeypatch):
    db = SessionLocal()
    user_id = uuid4()
    email = f"expired-verification-{user_id}@example.com"
    captured_tokens = []

    def capture_verification_email(recipient, raw_otp, expires_at):
        captured_tokens.append(raw_otp)

    monkeypatch.setattr(
        "app.services.auth.send_email_verification_email",
        capture_verification_email,
    )

    try:
        user = User(
            id=user_id,
            email=email,
            hashed_password=hash_password("StrongPassword123!"),
            is_active=False,
            status=AccountStatus.PENDING.value,
            role=UserRole.CHW.value,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        create_email_verification(db, user)

        raw_otp = captured_tokens[0]

        verification_record = (
            db.query(EmailVerificationToken).filter_by(user_id=user_id).one()
        )

        verification_record.expires_at = datetime.now(UTC) - timedelta(minutes=1)
        db.commit()

        with pytest.raises(InvalidEmailVerificationToken):
            verify_email(db, email, raw_otp)

        db.refresh(user)

        assert user.status == AccountStatus.PENDING.value
        assert user.is_active is False
        assert user.email_verified_at is None

    finally:
        db.rollback()
        db.execute(
            delete(EmailVerificationToken).where(
                EmailVerificationToken.user_id == user_id
            )
        )
        db.execute(delete(AuditEvent).where(AuditEvent.target_user_id == user_id))
        db.execute(delete(User).where(User.id == user_id))
        db.commit()
        db.close()


@pytest.mark.integration
def test_postgres_email_verification_token_cannot_be_reused(monkeypatch):
    db = SessionLocal()
    user_id = uuid4()
    email = f"reused-verification-{user_id}@example.com"
    captured_tokens = []

    def capture_verification_email(recipient, raw_otp, expires_at):
        captured_tokens.append(raw_otp)

    monkeypatch.setattr(
        "app.services.auth.send_email_verification_email",
        capture_verification_email,
    )

    try:
        user = User(
            id=user_id,
            email=email,
            hashed_password=hash_password("StrongPassword123!"),
            is_active=False,
            status=AccountStatus.PENDING.value,
            role=UserRole.CHW.value,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        create_email_verification(db, user)
        raw_otp = captured_tokens[0]

        # First use must succeed.
        verified_user = verify_email(db, email, raw_otp)

        assert verified_user.status == AccountStatus.ACTIVE.value
        assert verified_user.email_verified_at is not None

        # Second use of the same code must fail.
        with pytest.raises(InvalidEmailVerificationToken):
            verify_email(db, email, raw_otp)

    finally:
        db.rollback()
        db.execute(
            delete(EmailVerificationToken).where(
                EmailVerificationToken.user_id == user_id
            )
        )
        db.execute(delete(AuditEvent).where(AuditEvent.target_user_id == user_id))
        db.execute(delete(User).where(User.id == user_id))
        db.commit()
        db.close()


@pytest.mark.integration
def test_postgres_resending_email_verification_invalidates_old_token(monkeypatch):
    db = SessionLocal()
    user_id = uuid4()
    email = f"resend-verification-{user_id}@example.com"
    captured_tokens = []

    def capture_verification_email(recipient, raw_otp, expires_at):
        captured_tokens.append(raw_otp)

    monkeypatch.setattr(
        "app.services.auth.send_email_verification_email",
        capture_verification_email,
    )

    try:
        user = User(
            id=user_id,
            email=email,
            hashed_password=hash_password("StrongPassword123!"),
            is_active=False,
            status=AccountStatus.PENDING.value,
            role=UserRole.CHW.value,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # First verification request.
        create_email_verification(db, user)
        old_otp = captured_tokens[0]

        # Resend verification.
        create_email_verification(db, user)
        new_otp = captured_tokens[1]

        assert old_otp != new_otp
        assert len(captured_tokens) == 2

        # Previous token must be rejected.
        with pytest.raises(InvalidEmailVerificationToken):
            verify_email(db, email, old_otp)

        # New token must still work.
        verified_user = verify_email(db, email, new_otp)

        assert verified_user.status == AccountStatus.ACTIVE.value
        assert verified_user.email_verified_at is not None

        verification_records = (
            db.query(EmailVerificationToken).filter_by(user_id=user_id).all()
        )

        assert len(verification_records) == 2
        assert all(record.used_at is not None for record in verification_records)

    finally:
        db.rollback()
        db.execute(
            delete(EmailVerificationToken).where(
                EmailVerificationToken.user_id == user_id
            )
        )
        db.execute(delete(AuditEvent).where(AuditEvent.target_user_id == user_id))
        db.execute(delete(User).where(User.id == user_id))
        db.commit()
        db.close()


@pytest.mark.integration
def test_postgres_email_verification_does_not_reactivate_suspended_account(
    monkeypatch,
):
    db = SessionLocal()
    user_id = uuid4()
    email = f"suspended-verification-{user_id}@example.com"
    captured_tokens = []

    def capture_verification_email(recipient, raw_otp, expires_at):
        captured_tokens.append(raw_otp)

    monkeypatch.setattr(
        "app.services.auth.send_email_verification_email",
        capture_verification_email,
    )

    try:
        user = User(
            id=user_id,
            email=email,
            hashed_password=hash_password("StrongPassword123!"),
            is_active=False,
            status=AccountStatus.SUSPENDED.value,
            role=UserRole.CHW.value,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        create_email_verification(db, user)
        raw_otp = captured_tokens[0]

        verified_user = verify_email(db, email, raw_otp)

        assert verified_user.email_verified_at is not None
        assert verified_user.status == AccountStatus.SUSPENDED.value
        assert verified_user.is_active is False

    finally:
        db.rollback()
        db.execute(
            delete(EmailVerificationToken).where(
                EmailVerificationToken.user_id == user_id
            )
        )
        db.execute(delete(AuditEvent).where(AuditEvent.target_user_id == user_id))
        db.execute(delete(User).where(User.id == user_id))
        db.commit()
        db.close()


@pytest.mark.integration
def test_login_rate_limit_expires_without_suspending_account(monkeypatch):
    db = SessionLocal()
    user_id = uuid4()
    email = f"rate-limit-{user_id}@example.com"
    bucket_key = None

    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", True)
    monkeypatch.setattr(settings, "LOGIN_RATE_LIMIT", 2)
    monkeypatch.setattr(settings, "RATE_LIMIT_WINDOW_SECONDS", 60)

    try:
        user = User(
            id=user_id,
            email=email,
            hashed_password=hash_password("StrongPassword123!"),
            is_active=True,
            status=AccountStatus.ACTIVE.value,
            role=UserRole.CHW.value,
            email_verified_at=datetime.now(UTC),
            password_changed_at=datetime.now(UTC),
        )

        db.add(user)
        db.commit()

        # Match the client address used by FastAPI TestClient.
        request = Request(
            {
                "type": "http",
                "client": ("testclient", 50000),
            }
        )

        bucket_key = _bucket_key("login", request, email)

        login_url = "/api/v1/auth/login"

        credentials = {
            "email": email,
            "password": "WrongPassword123!",
        }

        # Two failed attempts are allowed.
        first = client.post(login_url, json=credentials)
        second = client.post(login_url, json=credentials)

        assert first.status_code == 401
        assert second.status_code == 401

        # The third attempt exceeds the configured limit.
        blocked = client.post(login_url, json=credentials)

        assert blocked.status_code == 429

        initial_retry_after = int(blocked.headers["Retry-After"])

        assert 1 <= initial_retry_after <= 60

        db.expire_all()
        user = db.get(User, user_id)

        # Rate limiting must not suspend or deactivate the account.
        assert user is not None
        assert user.status == AccountStatus.ACTIVE.value
        assert user.is_active is True

        # Simulate 45 seconds having elapsed in the 60-second window.
        bucket = db.get(RateLimitBucket, bucket_key)
        assert bucket is not None

        bucket.window_started_at = datetime.now(UTC) - timedelta(seconds=45)

        db.commit()

        # Another attempt must still be blocked, but the remaining
        # retry time should now be approximately 15 seconds.
        retry_check = client.post(login_url, json=credentials)

        assert retry_check.status_code == 429

        remaining_retry_after = int(retry_check.headers["Retry-After"])

        assert 1 <= remaining_retry_after <= 15
        assert remaining_retry_after < initial_retry_after

        # Simulate the 60-second window having expired.
        bucket = db.get(RateLimitBucket, bucket_key)
        assert bucket is not None

        bucket.window_started_at = datetime.now(UTC) - timedelta(seconds=61)

        db.commit()

        # The correct credentials must now be processed normally.
        recovered = client.post(
            login_url,
            json={
                "email": email,
                "password": "StrongPassword123!",
            },
        )

        assert recovered.status_code == 200
        assert "access_token" in recovered.json()
        assert "refresh_token" in recovered.json()

        db.expire_all()
        user = db.get(User, user_id)

        assert user is not None
        assert user.status == AccountStatus.ACTIVE.value
        assert user.is_active is True

    finally:
        db.rollback()

        db.execute(delete(AuditEvent).where(AuditEvent.target_user_id == user_id))

        db.execute(delete(RefreshSession).where(RefreshSession.user_id == user_id))

        if bucket_key is not None:
            db.execute(
                delete(RateLimitBucket).where(RateLimitBucket.bucket_key == bucket_key)
            )

        db.execute(delete(User).where(User.id == user_id))

        db.commit()
        db.close()
