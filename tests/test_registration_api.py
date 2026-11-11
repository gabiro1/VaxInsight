from datetime import UTC, datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.core.config import settings
from app.database.dependencies import get_db
from app.main import app
from app.models.user import User
from app.schemas.auth import TokenResponse
from app.services.auth import EmailAlreadyRegistered
from app.services.email import EmailDeliveryError
from fastapi.testclient import TestClient

client = TestClient(app)


def test_register_community_account_successfully_when_enabled(
    monkeypatch,
):
    now = datetime.now(UTC)

    mock_user = User(
        id=uuid4(),
        email="student@example.com",
        full_name="Amina Uwase",
        hashed_password="$argon2id$example-hash",
        is_active=False,
        status="pending",
        role="community_member",
        created_at=now,
        updated_at=now,
    )

    monkeypatch.setattr(settings, "ALLOW_COMMUNITY_REGISTRATION", True)
    with (
        patch(
            "app.api.routes.auth.register_user",
            return_value=mock_user,
        ),
        patch("app.api.routes.auth.create_email_verification"),
    ):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "full_name": "Amina Uwase",
                "email": "student@example.com",
                "password": "StrongPassword123!",
                "confirm_password": "StrongPassword123!",
            },
        )

    assert response.status_code == 201
    assert response.json()["email"] == "student@example.com"
    assert response.json()["full_name"] == "Amina Uwase"
    assert response.json()["role"] == "community_member"
    assert response.json()["is_active"] is False
    assert response.json()["status"] == "pending"
    assert "hashed_password" not in response.json()


def test_register_existing_email_when_community_registration_is_enabled(monkeypatch):
    monkeypatch.setattr(settings, "ALLOW_COMMUNITY_REGISTRATION", True)
    with patch(
        "app.api.routes.auth.register_user",
        side_effect=EmailAlreadyRegistered(),
    ):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "full_name": "Amina Uwase",
                "email": "student@example.com",
                "password": "StrongPassword123!",
                "confirm_password": "StrongPassword123!",
            },
        )

    assert response.status_code == 409
    assert response.json()["detail"] == ("An account with this email already exists")


def test_register_is_disabled_when_configured(monkeypatch):
    monkeypatch.setattr(settings, "ALLOW_COMMUNITY_REGISTRATION", False)

    with patch("app.api.routes.auth.register_user") as mock_register:
        response = client.post(
            "/api/v1/auth/register",
            json={
                "full_name": "Amina Uwase",
                "email": "student@example.com",
                "password": "StrongPassword123!",
                "confirm_password": "StrongPassword123!",
            },
        )

    assert response.status_code == 403
    assert response.json()["detail"] == "Community registration is disabled"
    mock_register.assert_not_called()


def test_register_with_invalid_email():
    with patch("app.api.routes.auth.register_user") as mock_register:
        response = client.post(
            "/api/v1/auth/register",
            json={
                "full_name": "Amina Uwase",
                "email": "not-an-email",
                "password": "StrongPassword123!",
                "confirm_password": "StrongPassword123!",
            },
        )

    assert response.status_code == 422
    mock_register.assert_not_called()


def test_register_rejects_mismatched_password_confirmation():
    with patch("app.api.routes.auth.register_user") as mock_register:
        response = client.post(
            "/api/v1/auth/register",
            json={
                "full_name": "Amina Uwase",
                "email": "student@example.com",
                "password": "StrongPassword123!",
                "confirm_password": "DifferentPassword123!",
            },
        )

    assert response.status_code == 422
    mock_register.assert_not_called()


def test_register_rejects_staff_role_field():
    with patch("app.api.routes.auth.register_user") as mock_register:
        response = client.post(
            "/api/v1/auth/register",
            json={
                "full_name": "Amina Uwase",
                "email": "student@example.com",
                "password": "StrongPassword123!",
                "confirm_password": "StrongPassword123!",
                "role": "administrator",
            },
        )

    assert response.status_code == 422
    mock_register.assert_not_called()


def test_resend_email_verification_returns_generic_response(monkeypatch):
    monkeypatch.setattr(
        "app.api.routes.auth.enforce_rate_limit",
        lambda *args, **kwargs: None,
    )

    with patch(
        "app.api.routes.auth.request_email_verification",
        return_value=True,
    ) as mock_request:
        response = client.post(
            "/api/v1/auth/email/verify/resend",
            json={"email": "  CHW@EXAMPLE.COM  "},
        )

    assert response.status_code == 202
    assert response.json() == {
        "message": "If verification is required, instructions will be sent"
    }
    mock_request.assert_called_once()
    assert mock_request.call_args.args[1] == "chw@example.com"


def test_resend_email_verification_returns_same_response_for_unknown_email(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.routes.auth.enforce_rate_limit",
        lambda *args, **kwargs: None,
    )

    with patch(
        "app.api.routes.auth.request_email_verification",
        return_value=False,
    ) as mock_request:
        response = client.post(
            "/api/v1/auth/email/verify/resend",
            json={"email": "unknown@example.com"},
        )

    assert response.status_code == 202
    assert response.json() == {
        "message": "If verification is required, instructions will be sent"
    }
    mock_request.assert_called_once()


def test_resend_email_verification_hides_email_delivery_failure(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.routes.auth.enforce_rate_limit",
        lambda *args, **kwargs: None,
    )

    with patch(
        "app.api.routes.auth.request_email_verification",
        side_effect=EmailDeliveryError,
    ):
        response = client.post(
            "/api/v1/auth/email/verify/resend",
            json={"email": "chw@example.com"},
        )

    assert response.status_code == 202
    assert response.json() == {
        "message": "If verification is required, instructions will be sent"
    }


def test_resend_email_verification_rejects_invalid_email():
    with patch("app.api.routes.auth.request_email_verification") as mock_request:
        response = client.post(
            "/api/v1/auth/email/verify/resend",
            json={"email": "not-an-email"},
        )

    assert response.status_code == 422
    mock_request.assert_not_called()


def test_email_verification_returns_tokens_for_direct_home_redirect(monkeypatch):
    mock_db = MagicMock()

    def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(
        "app.api.routes.auth.enforce_rate_limit",
        lambda *args, **kwargs: None,
    )
    user = User(
        id=uuid4(),
        email="user@example.com",
        hashed_password="$argon2id$example-hash",
        is_active=True,
        status="active",
        role="community_member",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    tokens = TokenResponse(
        access_token="access-token",
        refresh_token="refresh-token",
        expires_in=1800,
        refresh_token_expires_in=2_592_000,
    )

    try:
        with (
            patch("app.api.routes.auth.verify_email", return_value=user) as verify,
            patch("app.api.routes.auth.issue_tokens", return_value=tokens) as issue,
        ):
            response = client.post(
                "/api/v1/auth/email/verify",
                json={"email": " USER@EXAMPLE.COM ", "otp": "012345"},
            )

        assert response.status_code == 200
        assert response.json()["access_token"] == "access-token"
        verify.assert_called_once_with(mock_db, "user@example.com", "012345")
        issue.assert_called_once_with(
            mock_db,
            user,
            audit_action="email_verification_login",
        )
    finally:
        app.dependency_overrides.clear()


def test_email_verification_rejects_non_numeric_otp():
    with patch("app.api.routes.auth.verify_email") as verify:
        response = client.post(
            "/api/v1/auth/email/verify",
            json={"email": "user@example.com", "otp": "12ab56"},
        )

    assert response.status_code == 422
    verify.assert_not_called()
