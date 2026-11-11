from unittest.mock import patch

from app.main import app
from app.models.user import User
from app.schemas.auth import TokenResponse
from app.services.auth import InvalidCredentials
from fastapi.testclient import TestClient

client = TestClient(app)


def test_login_successfully_returns_access_token():
    with (
        patch(
            "app.api.routes.auth.authenticate_user_account",
            return_value=User(
                id="00000000-0000-0000-0000-000000000001",
                email="user@example.com",
                hashed_password="argon2-hash",
                is_active=True,
            ),
        ),
        patch(
            "app.api.routes.auth.issue_tokens",
            return_value=TokenResponse(
                access_token="test-jwt-token",
                refresh_token="test-refresh-token",
            ),
        ),
    ):
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "user@example.com",
                "password": "StrongPassword123!",
            },
        )

    assert response.status_code == 200
    assert response.json()["access_token"] == "test-jwt-token"
    assert response.json()["token_type"] == "bearer"


def test_login_with_invalid_credentials():
    with patch(
        "app.api.routes.auth.authenticate_user_account",
        side_effect=InvalidCredentials(),
    ):
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "user@example.com",
                "password": "WrongPassword123!",
            },
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


def test_login_with_invalid_email():
    with patch("app.api.routes.auth.authenticate_user_account") as mock_authenticate:
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "invalid-email",
                "password": "StrongPassword123!",
            },
        )

    assert response.status_code == 422
    mock_authenticate.assert_not_called()


def test_login_without_password():
    with patch("app.api.routes.auth.authenticate_user_account") as mock_authenticate:
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "user@example.com",
            },
        )

    assert response.status_code == 422
    mock_authenticate.assert_not_called()
