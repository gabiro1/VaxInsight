from datetime import UTC, datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.api.dependencies import get_current_user
from app.database.dependencies import get_db
from app.main import app
from app.models.auth import Invitation
from app.models.user import AccountStatus, User, UserRole
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

client = TestClient(app)


def override_database(mock_db):
    def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db


def make_user(role: str) -> User:
    now = datetime.now(UTC)
    return User(
        id=uuid4(),
        email=f"{role}@example.com",
        hashed_password="argon2-hash",
        is_active=True,
        status=AccountStatus.ACTIVE.value,
        role=role,
        created_at=now,
        updated_at=now,
    )


def test_non_admin_cannot_create_invitation(monkeypatch):
    monkeypatch.setattr("app.main.settings.RATE_LIMIT_ENABLED", False)
    mock_db = MagicMock(spec=Session)
    override_database(mock_db)
    app.dependency_overrides[get_current_user] = lambda: make_user(
        UserRole.REVIEWER.value
    )

    try:
        response = client.post(
            "/api/v1/auth/invitations",
            json={"email": "new@example.com", "role": "chw"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403


def test_admin_invitation_response_does_not_expose_raw_token(monkeypatch):
    monkeypatch.setattr("app.main.settings.RATE_LIMIT_ENABLED", False)
    mock_db = MagicMock(spec=Session)
    override_database(mock_db)
    app.dependency_overrides[get_current_user] = lambda: make_user(
        UserRole.ADMINISTRATOR.value
    )
    invitation = Invitation(
        id=uuid4(),
        email="new@example.com",
        role=UserRole.CHW.value,
        token_hash="stored-hash",
        invited_by_id=uuid4(),
        expires_at=datetime.now(UTC),
    )

    try:
        with patch(
            "app.api.routes.auth.create_invitation",
            return_value=invitation,
        ):
            response = client.post(
                "/api/v1/auth/invitations",
                json={"email": "new@example.com", "role": "chw"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert "token" not in response.json()
    assert response.json()["message"] == "Invitation sent"


def test_invitation_acceptance_ignores_untrusted_email_and_role(monkeypatch):
    monkeypatch.setattr("app.main.settings.RATE_LIMIT_ENABLED", False)

    mock_db = MagicMock(spec=Session)
    override_database(mock_db)

    invited_user = make_user(UserRole.CHW.value)
    invited_user.email = "invited-chw@example.com"

    invitation_token = "valid-invitation-token-123456789012345678901234"
    password = "StrongPassword123!"

    try:
        with (
            patch(
                "app.api.routes.auth.accept_invitation",
                return_value=invited_user,
            ) as accept_mock,
            patch(
                "app.api.routes.auth.issue_tokens",
                return_value={
                    "access_token": "test-access-token",
                    "token_type": "bearer",
                    "expires_in": 900,
                    "refresh_token": "test-refresh-token",
                    "refresh_token_expires_in": 86400,
                },
            ),
        ):
            response = client.post(
                "/api/v1/auth/invitations/accept",
                json={
                    "token": invitation_token,
                    "password": password,
                    "email": "attacker@example.com",
                    "role": "administrator",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    accept_mock.assert_called_once_with(
        mock_db,
        invitation_token,
        password,
    )

    assert invited_user.email == "invited-chw@example.com"
    assert invited_user.role == UserRole.CHW.value
