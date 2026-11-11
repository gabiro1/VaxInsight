import re
from collections.abc import Collection


class UnsafeTestDatabaseConfiguration(RuntimeError):
    """Raised when a test database could overlap a protected database."""


def validate_test_database_name(
    test_database_name: str,
    protected_database_names: Collection[str],
) -> str:
    """Return a safe test database name or fail before any connection is opened."""

    normalized_name = test_database_name.strip().lower()
    protected_names = {
        name.strip().lower() for name in protected_database_names if name.strip()
    }

    if not normalized_name:
        raise UnsafeTestDatabaseConfiguration(
            "VAXINSIGHT_TEST_DB_NAME must not be empty"
        )
    if not re.search(r"(?:^|[_-])test(?:[_-]|$)", normalized_name):
        raise UnsafeTestDatabaseConfiguration(
            "The test database name must contain a separate test segment"
        )
    if normalized_name in {"postgres", "template0", "template1"}:
        raise UnsafeTestDatabaseConfiguration(
            "The test database cannot be a PostgreSQL maintenance database"
        )
    if normalized_name in protected_names:
        raise UnsafeTestDatabaseConfiguration(
            "The test database must be different from development and production databases"
        )

    return test_database_name.strip()
