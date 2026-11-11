import hashlib
import secrets


def generate_opaque_token() -> str:
    """Create a high-entropy token suitable for one-time or refresh use."""

    return secrets.token_urlsafe(48)


def generate_email_verification_otp() -> str:
    """Create a six-digit, zero-padded email verification code."""

    return f"{secrets.randbelow(1_000_000):06d}"


def hash_opaque_token(token: str) -> str:
    """Store only a deterministic digest of an opaque token."""

    return hashlib.sha256(token.encode("utf-8")).hexdigest()
