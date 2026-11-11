from datetime import UTC, datetime, timedelta

import jwt
from app.core.config import settings
from app.core.tokens import create_access_token, verify_access_token


def test_valid_token_is_verified():
    token = create_access_token("test-user-123")

    payload = verify_access_token(token)

    assert payload is not None
    assert payload["sub"] == "test-user-123"


def test_invalid_token_is_rejected():
    payload = verify_access_token("invalid.token.value")

    assert payload is None


def test_empty_token_is_rejected():
    payload = verify_access_token("")

    assert payload is None


def test_expired_token_is_rejected():
    expired_token = jwt.encode(
        {
            "sub": "test-user-123",
            "exp": datetime.now(UTC) - timedelta(minutes=5),
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    payload = verify_access_token(expired_token)

    assert payload is None
