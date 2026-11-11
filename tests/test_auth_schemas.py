import pytest
from app.schemas.auth import EmailVerificationRequest, UserLogin, UserRegister
from pydantic import ValidationError


def test_registration_accepts_valid_data():
    user = UserRegister(
        full_name="Amina Uwase",
        email="user@example.com",
        password="SecurePassword123",
        confirm_password="SecurePassword123",
    )

    assert user.full_name == "Amina Uwase"
    assert user.email == "user@example.com"
    assert user.password == "SecurePassword123"


def test_registration_normalizes_email():
    user = UserRegister(
        full_name="  Amina   Uwase  ",
        email="  USER@EXAMPLE.COM  ",
        password="SecurePassword123",
        confirm_password="SecurePassword123",
    )

    assert user.full_name == "Amina Uwase"
    assert user.email == "user@example.com"


def test_registration_rejects_invalid_email():
    with pytest.raises(ValidationError):
        UserRegister(
            full_name="Amina Uwase",
            email="invalid-email",
            password="SecurePassword123",
            confirm_password="SecurePassword123",
        )


def test_registration_rejects_short_password():
    with pytest.raises(ValidationError):
        UserRegister(
            full_name="Amina Uwase",
            email="user@example.com",
            password="short",
            confirm_password="short",
        )


def test_registration_rejects_mismatched_password_confirmation():
    with pytest.raises(ValidationError):
        UserRegister(
            full_name="Amina Uwase",
            email="user@example.com",
            password="SecurePassword123",
            confirm_password="DifferentPassword123",
        )


def test_registration_rejects_blank_full_name():
    with pytest.raises(ValidationError):
        UserRegister(
            full_name="   ",
            email="user@example.com",
            password="SecurePassword123",
            confirm_password="SecurePassword123",
        )


def test_login_accepts_valid_credentials():
    user = UserLogin(
        email="user@example.com",
        password="password123",
    )

    assert user.email == "user@example.com"


def test_login_rejects_empty_password():
    with pytest.raises(ValidationError):
        UserLogin(
            email="user@example.com",
            password="",
        )


def test_email_verification_accepts_a_six_digit_otp():
    verification = EmailVerificationRequest(
        email=" USER@EXAMPLE.COM ",
        otp="012345",
    )

    assert verification.email == "user@example.com"
    assert verification.otp == "012345"


@pytest.mark.parametrize("otp", ["12345", "1234567", "12ab56"])
def test_email_verification_rejects_invalid_otp(otp):
    with pytest.raises(ValidationError):
        EmailVerificationRequest(email="user@example.com", otp=otp)
