from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError

# Initialize Argon2 password hashing
password_hash = PasswordHash.recommended()
DUMMY_PASSWORD_HASH = password_hash.hash("vaxinsight-unusable-password")


def hash_password(password: str) -> str:
    """Hash a password before storing it."""
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its stored hash."""

    try:
        return password_hash.verify(plain_password, hashed_password)
    except (TypeError, ValueError, UnknownHashError):
        return False
