from unittest.mock import MagicMock

import pytest
from app.core.security import verify_password
from app.models.user import User, UserRole
from app.schemas.auth import UserRegister
from app.services.auth import (
    EmailAlreadyRegistered,
    register_user,
)
from sqlalchemy.exc import IntegrityError


def test_register_user_creates_account():
    mock_db = MagicMock()
    mock_db.scalar.return_value = None

    user_data = UserRegister(
        full_name="Amina Uwase",
        email="user@example.com",
        password="SecurePassword123",
        confirm_password="SecurePassword123",
    )

    def refresh_user(user):
        user.id = "test-user-id"

    mock_db.refresh.side_effect = refresh_user

    user = register_user(mock_db, user_data)

    assert isinstance(user, User)
    assert user.email == "user@example.com"
    assert user.full_name == "Amina Uwase"
    assert user.role == UserRole.COMMUNITY_MEMBER.value
    assert user.status == "pending"
    assert user.is_active is False
    assert verify_password(
        "SecurePassword123",
        user.hashed_password,
    )
    assert user.hashed_password != "SecurePassword123"

    mock_db.add.assert_called_once_with(user)
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(user)


def test_register_user_rejects_existing_email():
    mock_db = MagicMock()
    mock_db.scalar.return_value = User(
        email="user@example.com",
        hashed_password="existing-hash",
    )

    user_data = UserRegister(
        full_name="Amina Uwase",
        email="user@example.com",
        password="SecurePassword123",
        confirm_password="SecurePassword123",
    )

    with pytest.raises(EmailAlreadyRegistered):
        register_user(mock_db, user_data)

    mock_db.add.assert_not_called()
    mock_db.commit.assert_not_called()


def test_register_user_handles_duplicate_email_race():
    mock_db = MagicMock()
    mock_db.scalar.return_value = None

    mock_db.commit.side_effect = IntegrityError(
        "INSERT INTO users",
        {},
        Exception("Unique constraint violation"),
    )

    user_data = UserRegister(
        full_name="Amina Uwase",
        email="user@example.com",
        password="SecurePassword123",
        confirm_password="SecurePassword123",
    )

    with pytest.raises(EmailAlreadyRegistered):
        register_user(mock_db, user_data)

    mock_db.rollback.assert_called_once()
