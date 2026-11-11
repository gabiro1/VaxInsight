from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
from jwt.exceptions import InvalidTokenError

from app.core.config import settings


def create_access_token(subject: str) -> str:
    """Create a signed JWT access token."""

    now = datetime.now(UTC)

    expires_at = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": subject,
        "iat": now.timestamp(),
        "exp": expires_at,
        "jti": str(uuid4()),
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "typ": "access",
    }

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def verify_access_token(token: str) -> dict | None:
    """Verify a JWT and return its payload."""

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER,
            options={"require": ["sub", "exp", "iat", "jti", "typ"]},
        )

        if payload.get("typ") != "access":
            return None

        return payload

    except InvalidTokenError:
        return None
