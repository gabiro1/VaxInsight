from types import SimpleNamespace
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from app.schemas.auth import UserLogin
from app.services.auth import InvalidCredentials, authenticate_user


def test_authenticate_user_successfully():
    """A valid user should receive an access token."""

    user = SimpleNamespace(
        id=uuid4(),
        hashed_password="argon2-hash",
        is_active=True,
    )

    db = Mock()
    db.scalar.return_value = user

    login_data = UserLogin(
        email="user@example.com",
        password="CorrectPassword123!",
    )

    with (
        patch(
            "app.services.auth.verify_password",
            return_value=True,
        ),
        patch(
            "app.services.auth.create_access_token",
            return_value="test-jwt-token",
        ) as mock_create_token,
    ):
        token = authenticate_user(db, login_data)

    assert token == "test-jwt-token"
    mock_create_token.assert_called_once_with(subject=str(user.id))


def test_authenticate_user_with_unknown_email():
    """An unknown email should be rejected."""

    db = Mock()
    db.scalar.return_value = None

    login_data = UserLogin(
        email="unknown@example.com",
        password="CorrectPassword123!",
    )

    with (
        patch("app.services.auth.verify_password") as mock_verify,
        pytest.raises(InvalidCredentials),
    ):
        authenticate_user(db, login_data)

    mock_verify.assert_called_once()


def test_authenticate_user_with_wrong_password():
    """An incorrect password should be rejected."""

    user = SimpleNamespace(
        id=uuid4(),
        hashed_password="argon2-hash",
        is_active=True,
    )

    db = Mock()
    db.scalar.return_value = user

    login_data = UserLogin(
        email="user@example.com",
        password="WrongPassword123!",
    )

    with (
        patch(
            "app.services.auth.verify_password",
            return_value=False,
        ),
        pytest.raises(InvalidCredentials),
    ):
        authenticate_user(db, login_data)


def test_authenticate_inactive_user():
    """An inactive account should not receive an access token."""

    user = SimpleNamespace(
        id=uuid4(),
        hashed_password="argon2-hash",
        is_active=False,
    )

    db = Mock()
    db.scalar.return_value = user

    login_data = UserLogin(
        email="inactive@example.com",
        password="CorrectPassword123!",
    )

    with (
        patch(
            "app.services.auth.verify_password",
            return_value=True,
        ),
        patch(
            "app.services.auth.create_access_token",
        ) as mock_create_token,
        pytest.raises(InvalidCredentials),
    ):
        authenticate_user(db, login_data)

    mock_create_token.assert_not_called()
