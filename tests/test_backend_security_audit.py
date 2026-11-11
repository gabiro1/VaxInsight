import threading
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest
from app.api.dependencies import require_roles
from app.core.config import Settings, settings
from app.core.security import hash_password
from app.core.tokens import create_access_token
from app.database.database import SessionLocal, engine
from app.main import app, documentation_url
from app.models.auth import (
    AuditEvent,
    EmailVerificationToken,
    PasswordResetToken,
    RefreshSession,
)
from app.models.user import AccountStatus, User, UserRole
from app.services import sessions as session_service
from app.services.auth import request_email_change, verify_email
from app.services.rate_limit import _bucket_key
from app.services.sessions import (
    InvalidRefreshToken,
    issue_tokens,
    revoke_all_sessions,
    rotate_refresh_token,
)
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import delete, or_
from starlette.requests import Request

client = TestClient(app)


def _request(client_host: str) -> Request:
    return Request(
        {
            "type": "http",
            "client": (client_host, 50000),
        }
    )


def _production_settings(**overrides):
    values = {
        "APP_ENV": "production",
        "DEBUG": False,
        "DB_PASSWORD": "local-test-password",
        "DB_SSL_MODE": "require",
        "SECRET_KEY": "s" * 64,
        "SMTP_HOST": "smtp.example.com",
        "SMTP_FROM": "noreply@example.com",
        "SMTP_USE_TLS": True,
        "ACCOUNT_ACTION_BASE_URL": "https://app.example.com/account",
        "RATE_LIMIT_ENABLED": True,
    }
    values.update(overrides)
    return values


def _cleanup_user(user_id):
    db = SessionLocal()
    try:
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
            delete(EmailVerificationToken).where(
                EmailVerificationToken.user_id == user_id
            )
        )
        db.execute(
            delete(PasswordResetToken).where(PasswordResetToken.user_id == user_id)
        )
        db.execute(delete(RefreshSession).where(RefreshSession.user_id == user_id))
        db.execute(delete(User).where(User.id == user_id))
        db.commit()
    finally:
        db.close()


def test_jwt_rejects_wrong_algorithm_type_issuer_audience_and_missing_claim():
    now = datetime.now(UTC)
    payload = {
        "sub": str(uuid4()),
        "iat": now,
        "exp": now + timedelta(minutes=5),
        "jti": str(uuid4()),
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "typ": "access",
    }
    invalid_tokens = [
        jwt.encode(payload, settings.SECRET_KEY, algorithm="HS384"),
        jwt.encode(
            {**payload, "typ": "refresh"}, settings.SECRET_KEY, algorithm="HS256"
        ),
        jwt.encode(
            {**payload, "iss": "unexpected-issuer"},
            settings.SECRET_KEY,
            algorithm="HS256",
        ),
        jwt.encode(
            {**payload, "aud": "unexpected-audience"},
            settings.SECRET_KEY,
            algorithm="HS256",
        ),
        jwt.encode(
            {key: value for key, value in payload.items() if key != "jti"},
            settings.SECRET_KEY,
            algorithm="HS256",
        ),
    ]

    for token in invalid_tokens:
        response = client.get(
            "/api/v1/auth/token-check",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401


def test_jwt_with_empty_subject_is_rejected():
    now = datetime.now(UTC)
    token = jwt.encode(
        {
            "sub": "",
            "iat": now,
            "exp": now + timedelta(minutes=5),
            "jti": str(uuid4()),
            "iss": settings.JWT_ISSUER,
            "aud": settings.JWT_AUDIENCE,
            "typ": "access",
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    response = client.get(
        "/api/v1/auth/token-check",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401


def test_role_dependency_denies_non_administrator_users():
    dependency = require_roles(UserRole.ADMINISTRATOR.value)
    reviewer = User(role=UserRole.REVIEWER.value)

    with pytest.raises(HTTPException) as error:
        dependency(reviewer)

    assert error.value.status_code == 403


def test_production_settings_fail_closed_for_insecure_values():
    assert Settings(**_production_settings()).APP_ENV == "production"

    invalid_values = [
        {"APP_ENV": "prod"},
        {"DEBUG": True},
        {"DB_SSL_MODE": "prefer"},
        {"SMTP_USE_TLS": False},
        {"ACCOUNT_ACTION_BASE_URL": "http://app.example.com/account"},
        {"RATE_LIMIT_ENABLED": False},
    ]

    for invalid in invalid_values:
        with pytest.raises(ValidationError):
            Settings(**_production_settings(**invalid))


def test_production_documentation_url_is_disabled():
    assert documentation_url("production") is None
    assert documentation_url("development") == "/openapi.json"


def test_database_engine_hides_sql_parameters():
    assert engine.hide_parameters is True


def test_security_headers_and_cors_do_not_allow_wildcard_credentials():
    response = client.get(
        "/api/v1/health",
        headers={"Origin": "https://untrusted.example.com"},
    )

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"

    cors_middleware = [
        middleware
        for middleware in app.user_middleware
        if middleware.cls.__name__ == "CORSMiddleware"
    ]
    for middleware in cors_middleware:
        assert middleware.kwargs["allow_credentials"] is False
        assert "*" not in middleware.kwargs["allow_origins"]


def test_validation_errors_do_not_echo_submitted_password():
    password = "A" * 129
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "person@example.com", "password": password},
    )

    assert response.status_code == 422
    assert password not in response.text
    assert all("input" not in detail for detail in response.json()["detail"])


def test_account_rate_limit_keys_are_not_bound_to_client_ip():
    email = "person@example.com"

    first_account_key = _bucket_key("login", _request("198.51.100.10"), email)
    second_account_key = _bucket_key("login", _request("198.51.100.11"), email)
    first_ip_key = _bucket_key("refresh", _request("198.51.100.10"), None)
    second_ip_key = _bucket_key("refresh", _request("198.51.100.11"), None)

    assert first_account_key == second_account_key
    assert first_ip_key != second_ip_key


@pytest.mark.integration
def test_email_change_invalidates_access_tokens_after_reverification(monkeypatch):
    db = SessionLocal()
    user_id = uuid4()
    captured = {}

    def capture_verification_email(email, otp, expires_at):
        captured["otp"] = otp

    monkeypatch.setattr(
        "app.services.auth.send_email_verification_email",
        capture_verification_email,
    )

    try:
        user = User(
            id=user_id,
            email=f"email-change-{user_id}@example.com",
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

        old_access_token = create_access_token(str(user.id))
        request_email_change(db, user, f"new-{user_id}@example.com")
        verify_email(db, f"new-{user_id}@example.com", captured["otp"])

        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {old_access_token}"},
        )

        assert response.status_code == 401
    finally:
        db.close()
        _cleanup_user(user_id)


@pytest.mark.integration
def test_logout_all_cannot_miss_refresh_session_created_during_rotation(monkeypatch):
    setup_db = SessionLocal()
    user_id = uuid4()
    rotation_staged = threading.Event()
    allow_rotation_commit = threading.Event()
    revoke_attempted = threading.Event()
    rotation_result = []
    errors = []
    original_create_session = session_service._create_session
    original_lock_user = session_service.lock_user_session_state

    def staged_create_session(db, user, *, family_id=None):
        result = original_create_session(db, user, family_id=family_id)
        rotation_staged.set()
        if not allow_rotation_commit.wait(timeout=30):
            raise RuntimeError("Timed out allowing refresh rotation")
        return result

    def tracked_user_lock(db, locked_user_id):
        if threading.current_thread().name == "logout-all":
            revoke_attempted.set()
        return original_lock_user(db, locked_user_id)

    try:
        user = User(
            id=user_id,
            email=f"refresh-race-{user_id}@example.com",
            hashed_password=hash_password("StrongPassword123!"),
            is_active=True,
            status=AccountStatus.ACTIVE.value,
            role=UserRole.CHW.value,
            email_verified_at=datetime.now(UTC),
            password_changed_at=datetime.now(UTC),
        )
        setup_db.add(user)
        setup_db.commit()
        setup_db.refresh(user)
        initial_tokens = issue_tokens(setup_db, user)
    finally:
        setup_db.close()

    monkeypatch.setattr(session_service, "_create_session", staged_create_session)
    monkeypatch.setattr(
        session_service,
        "lock_user_session_state",
        tracked_user_lock,
    )

    def rotate_worker():
        db = SessionLocal()
        try:
            rotation_result.append(
                rotate_refresh_token(db, initial_tokens.refresh_token)
            )
        except Exception as error:  # noqa: BLE001 - report worker failures
            errors.append(error)
        finally:
            db.close()

    def revoke_worker():
        db = SessionLocal()
        try:
            revoke_all_sessions(db, user_id)
            db.commit()
        except Exception as error:  # noqa: BLE001 - report worker failures
            errors.append(error)
        finally:
            db.close()

    rotation_thread = threading.Thread(target=rotate_worker, name="rotation")
    revoke_thread = threading.Thread(target=revoke_worker, name="logout-all")

    try:
        rotation_thread.start()
        assert rotation_staged.wait(timeout=30)
        revoke_thread.start()
        assert revoke_attempted.wait(timeout=30)
        allow_rotation_commit.set()

        rotation_thread.join(timeout=30)
        revoke_thread.join(timeout=30)

        assert not rotation_thread.is_alive()
        assert not revoke_thread.is_alive()
        assert errors == []
        assert len(rotation_result) == 1

        verification_db = SessionLocal()
        try:
            sessions = (
                verification_db.query(RefreshSession).filter_by(user_id=user_id).all()
            )
            assert sessions
            assert all(session.revoked_at is not None for session in sessions)

            with pytest.raises(InvalidRefreshToken):
                rotate_refresh_token(
                    verification_db,
                    rotation_result[0].refresh_token,
                )
        finally:
            verification_db.close()
    finally:
        allow_rotation_commit.set()
        rotation_thread.join(timeout=30)
        revoke_thread.join(timeout=30)
        _cleanup_user(user_id)
