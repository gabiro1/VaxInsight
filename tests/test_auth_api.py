from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

import jwt
import pytest
from app.core.config import settings
from app.core.tokens import create_access_token
from app.database.dependencies import get_db
from app.main import app
from app.models.user import User
from app.schemas.auth import UserLogin
from app.services.auth import (
    InvalidCredentials,
    LastActiveAdministratorError,
    authenticate_user_account,
)
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

client = TestClient(app)


def create_test_user(is_active=True):
    now = datetime.now(UTC)

    return User(
        id=uuid4(),
        email="test@example.com",
        hashed_password="test-hashed-password",
        is_active=is_active,
        created_at=now,
        updated_at=now,
    )


def override_database(mock_db):
    def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db


def test_protected_endpoint_rejects_unauthenticated_request():
    response = client.get("/api/v1/auth/token-check")

    assert response.status_code == 401


def test_protected_endpoint_accepts_valid_token():
    test_user = create_test_user()

    mock_db = MagicMock(spec=Session)
    mock_db.scalar.return_value = test_user

    override_database(mock_db)

    try:
        token = create_access_token(str(test_user.id))

        response = client.get(
            "/api/v1/auth/token-check",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.json()["authenticated"] is True
        assert response.json()["subject"] == str(test_user.id)

        mock_db.scalar.assert_called_once()

    finally:
        app.dependency_overrides.clear()


def test_protected_endpoint_rejects_invalid_token():
    response = client.get(
        "/api/v1/auth/token-check",
        headers={"Authorization": "Bearer invalid.token.value"},
    )

    assert response.status_code == 401


def test_me_endpoint_rejects_unauthenticated_request():
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_logout_returns_success_message():
    test_user = create_test_user()
    mock_db = MagicMock(spec=Session)
    mock_db.scalar.return_value = test_user

    override_database(mock_db)

    try:
        token = create_access_token(str(test_user.id))

        with patch("app.api.routes.auth.revoke_refresh_token") as revoke_token:
            response = client.post(
                "/api/v1/auth/logout",
                headers={"Authorization": f"Bearer {token}"},
                json={"refresh_token": "refresh-token-" + "x" * 32},
            )

        assert response.status_code == 200
        assert response.json() == {"message": "Logout successful"}
        revoke_token.assert_called_once_with(
            mock_db,
            "refresh-token-" + "x" * 32,
            test_user,
        )

    finally:
        app.dependency_overrides.clear()


def test_logout_all_returns_success_message():
    test_user = create_test_user()
    mock_db = MagicMock(spec=Session)
    mock_db.scalar.return_value = test_user

    override_database(mock_db)

    try:
        token = create_access_token(str(test_user.id))

        with patch("app.api.routes.auth.revoke_all_sessions") as revoke_all:
            response = client.post(
                "/api/v1/auth/logout-all",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 200
        assert response.json() == {"message": "All sessions logged out successfully"}
        revoke_all.assert_called_once_with(mock_db, test_user.id)

    finally:
        app.dependency_overrides.clear()


def test_delete_account_returns_success_message():
    test_user = create_test_user()
    mock_db = MagicMock(spec=Session)
    mock_db.scalar.return_value = test_user

    override_database(mock_db)

    try:
        token = create_access_token(str(test_user.id))

        with patch("app.api.routes.auth.delete_account") as delete:
            response = client.delete(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 200
        assert response.json() == {"message": "Account deleted successfully"}
        delete.assert_called_once_with(mock_db, test_user)
    finally:
        app.dependency_overrides.clear()


def test_delete_account_rejects_deleting_last_administrator():
    test_user = create_test_user()
    mock_db = MagicMock(spec=Session)
    mock_db.scalar.return_value = test_user

    override_database(mock_db)

    try:
        token = create_access_token(str(test_user.id))

        with patch(
            "app.api.routes.auth.delete_account",
            side_effect=LastActiveAdministratorError,
        ):
            response = client.delete(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 409
        assert response.json() == {
            "detail": "Cannot delete the last active administrator"
        }
    finally:
        app.dependency_overrides.clear()


def test_password_change_returns_success_message():
    test_user = create_test_user()
    mock_db = MagicMock(spec=Session)
    mock_db.scalar.return_value = test_user

    override_database(mock_db)

    try:
        token = create_access_token(str(test_user.id))

        with patch("app.api.routes.auth.change_password") as change_password:
            response = client.post(
                "/api/v1/auth/password/change",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "current_password": "CurrentPassword123!",
                    "new_password": "NewPassword123!",
                },
            )

        assert response.status_code == 200
        assert response.json() == {"message": "Password changed successfully"}
        change_password.assert_called_once_with(
            mock_db,
            test_user,
            "CurrentPassword123!",
            "NewPassword123!",
        )

    finally:
        app.dependency_overrides.clear()


def test_password_reset_confirmation_returns_success_message(monkeypatch):
    mock_db = MagicMock(spec=Session)
    override_database(mock_db)
    monkeypatch.setattr(
        "app.api.routes.auth.enforce_rate_limit",
        lambda *args, **kwargs: None,
    )

    try:
        with patch("app.api.routes.auth.confirm_password_reset") as confirm_reset:
            response = client.post(
                "/api/v1/auth/password-reset/confirm",
                json={
                    "token": "t" * 32,
                    "new_password": "NewPassword123!",
                },
            )

        assert response.status_code == 200
        assert response.json() == {"message": "Password reset successful"}
        confirm_reset.assert_called_once_with(
            mock_db,
            "t" * 32,
            "NewPassword123!",
        )

    finally:
        app.dependency_overrides.clear()


def test_me_endpoint_returns_authenticated_user_profile():
    test_user = create_test_user()

    mock_db = MagicMock(spec=Session)
    mock_db.scalar.return_value = test_user

    override_database(mock_db)

    try:
        token = create_access_token(str(test_user.id))

        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.json()["id"] == str(test_user.id)
        assert response.json()["email"] == test_user.email
        assert response.json()["is_active"] is True

        assert "hashed_password" not in response.json()

    finally:
        app.dependency_overrides.clear()


def test_me_endpoint_updates_full_name_without_ending_the_session():
    test_user = create_test_user()
    mock_db = MagicMock(spec=Session)
    mock_db.scalar.return_value = test_user

    override_database(mock_db)

    try:
        token = create_access_token(str(test_user.id))

        response = client.patch(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            json={"full_name": "  Amina   Uwase  "},
        )

        assert response.status_code == 200
        assert response.json()["full_name"] == "Amina Uwase"
        assert test_user.full_name == "Amina Uwase"
        mock_db.commit.assert_called_once()
    finally:
        app.dependency_overrides.clear()


def test_me_endpoint_rejects_inactive_user():
    test_user = create_test_user(is_active=False)

    mock_db = MagicMock(spec=Session)
    mock_db.scalar.return_value = test_user

    override_database(mock_db)

    try:
        token = create_access_token(str(test_user.id))

        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 401

    finally:
        app.dependency_overrides.clear()


def test_me_endpoint_rejects_suspended_user_even_if_is_active_true():
    test_user = create_test_user(is_active=True)
    test_user.status = "suspended"

    mock_db = MagicMock(spec=Session)
    mock_db.scalar.return_value = test_user

    override_database(mock_db)

    try:
        token = create_access_token(str(test_user.id))

        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 401

    finally:
        app.dependency_overrides.clear()


def test_me_endpoint_rejects_deactivated_user_even_if_is_active_true():
    test_user = create_test_user(is_active=True)
    test_user.status = "deactivated"

    mock_db = MagicMock(spec=Session)
    mock_db.scalar.return_value = test_user

    override_database(mock_db)

    try:
        token = create_access_token(str(test_user.id))

        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 401

    finally:
        app.dependency_overrides.clear()


def test_me_endpoint_rejects_nonexistent_user():
    mock_db = MagicMock(spec=Session)
    mock_db.scalar.return_value = None

    override_database(mock_db)

    try:
        token = create_access_token(str(uuid4()))

        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 401

    finally:
        app.dependency_overrides.clear()


def test_me_endpoint_rejects_token_issued_before_password_change():
    test_user = create_test_user()
    mock_db = MagicMock(spec=Session)
    mock_db.scalar.return_value = test_user

    override_database(mock_db)

    try:
        token = create_access_token(str(test_user.id))
        test_user.password_changed_at = datetime.now(UTC) + timedelta(seconds=1)

        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_me_endpoint_rejects_token_when_password_changes_within_same_second():
    test_user = create_test_user()
    mock_db = MagicMock(spec=Session)
    mock_db.scalar.return_value = test_user

    override_database(mock_db)

    try:
        token = create_access_token(str(test_user.id))

        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={
                "verify_signature": False,
                "verify_exp": False,
                "verify_aud": False,
                "verify_iss": False,
            },
        )

        issued_at = datetime.fromtimestamp(payload["iat"], UTC)

        # Simulate a password change 500 milliseconds after token issuance.
        test_user.password_changed_at = issued_at + timedelta(milliseconds=500)

        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 401

    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize("status", ["suspended", "deactivated"])
def test_login_rejects_inactive_account_status(status, monkeypatch):
    test_user = create_test_user(is_active=True)
    test_user.status = status

    mock_db = MagicMock(spec=Session)
    mock_db.scalar.return_value = test_user

    # Isolate the account-status check from password hashing.
    monkeypatch.setattr(
        "app.services.auth.verify_password",
        lambda password, password_hash: True,
    )

    login_data = UserLogin(
        email=test_user.email,
        password="ValidPassword123!",
    )

    with pytest.raises(InvalidCredentials):
        authenticate_user_account(mock_db, login_data)

    mock_db.scalar.assert_called_once()
