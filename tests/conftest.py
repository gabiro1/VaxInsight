from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import psycopg
import pytest
from dotenv import dotenv_values
from psycopg import sql

# Make the backend package available to pytest
PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"

sys.path.insert(0, str(BACKEND_DIR))

from app.database.configuration import validate_test_database_name  # noqa: I001


_ENV_FILE_VALUES = {
    key: value
    for key, value in dotenv_values(PROJECT_ROOT / ".env").items()
    if value is not None
}


def _configured_value(name: str, default: str | None = None) -> str | None:
    return os.environ.get(name) or _ENV_FILE_VALUES.get(name) or default


def _database_connection_kwargs(database_name: str) -> dict[str, object]:
    password = _configured_value("DB_PASSWORD")
    if not password:
        raise RuntimeError(
            "A DB_PASSWORD environment variable or .env value is required to provision "
            "the dedicated test database"
        )

    return {
        "host": _configured_value("DB_HOST", "localhost"),
        "port": int(_configured_value("DB_PORT", "5432")),
        "dbname": database_name,
        "user": _configured_value("DB_USER", "postgres"),
        "password": password,
        "sslmode": _configured_value("DB_SSL_MODE", "prefer"),
        "connect_timeout": 10,
    }


def _protected_database_names(test_database_name: str) -> set[str]:
    configured_database_names = {
        value
        for value in (
            _ENV_FILE_VALUES.get("DB_NAME"),
            os.environ.get("DB_NAME"),
            _configured_value("VAXINSIGHT_PRODUCTION_DB_NAME"),
            _configured_value("PRODUCTION_DB_NAME"),
            "vaccine_ai",
            "vaccine_ai_prod",
            "vaccine_ai_production",
            "production",
        )
        if value
    }
    return {
        value
        for value in configured_database_names
        if value.strip().lower() != test_database_name.strip().lower()
    }


TEST_DATABASE_NAME = validate_test_database_name(
    os.environ.get("VAXINSIGHT_TEST_DB_NAME", "vaccine_ai_test"),
    _protected_database_names(
        os.environ.get("VAXINSIGHT_TEST_DB_NAME", "vaccine_ai_test")
    ),
)
DEVELOPMENT_DATABASE_NAME = _configured_value("DB_NAME", "vaccine_ai")
PRODUCTION_DATABASE_NAME = _configured_value("VAXINSIGHT_PRODUCTION_DB_NAME") or _configured_value(
    "PRODUCTION_DB_NAME"
)

configured_app_environment = _configured_value("APP_ENV", "development")
if configured_app_environment == "production":
    raise RuntimeError(
        "Refusing to run tests while APP_ENV is configured as production; use a test "
        "environment and a dedicated test database"
    )

# These overrides happen before any test imports the application settings or engine.
os.environ["APP_ENV"] = "test"
os.environ["DB_NAME"] = TEST_DATABASE_NAME
os.environ["VAXINSIGHT_TEST_DB_NAME"] = TEST_DATABASE_NAME
os.environ["VAXINSIGHT_DEVELOPMENT_DB_NAME"] = DEVELOPMENT_DATABASE_NAME
if PRODUCTION_DATABASE_NAME:
    os.environ["VAXINSIGHT_PRODUCTION_DB_NAME"] = PRODUCTION_DATABASE_NAME


def _ensure_test_database_exists() -> None:
    maintenance_database = _configured_value("VAXINSIGHT_POSTGRES_MAINTENANCE_DB", "postgres")
    if maintenance_database.strip().lower() in {
        name.strip().lower()
        for name in _protected_database_names(TEST_DATABASE_NAME)
    } or maintenance_database.strip().lower() == TEST_DATABASE_NAME.strip().lower():
        raise RuntimeError(
            "The PostgreSQL maintenance database must not be the development, production, "
            "or dedicated test database"
        )
    connection_kwargs = _database_connection_kwargs(maintenance_database)
    connection_kwargs.pop("dbname")

    try:
        with psycopg.connect(
            dbname=maintenance_database,
            **connection_kwargs,
            autocommit=True,
        ) as connection:
            existing = connection.execute(
                "SELECT pg_get_userbyid(datdba) FROM pg_database WHERE datname = %s",
                (TEST_DATABASE_NAME,),
            ).fetchone()
            if existing is None:
                connection.execute(
                    sql.SQL("CREATE DATABASE {} OWNER {}").format(
                        sql.Identifier(TEST_DATABASE_NAME),
                        sql.Identifier(str(_configured_value("DB_USER", "postgres"))),
                    )
                )
            elif str(existing[0]).lower() != str(
                _configured_value("DB_USER", "postgres")
            ).lower():
                raise RuntimeError(
                    f"The dedicated test database {TEST_DATABASE_NAME!r} must be owned by "
                    f"the configured DB_USER"
                )
    except psycopg.Error as error:
        raise RuntimeError(
            "Could not provision the dedicated PostgreSQL test database. Create "
            f"{TEST_DATABASE_NAME!r} with DB_USER as its owner, or grant DB_USER "
            "CREATEDB permission, then rerun pytest."
        ) from error


def _reset_test_database() -> None:
    try:
        with psycopg.connect(
            **_database_connection_kwargs(TEST_DATABASE_NAME),
            autocommit=True,
        ) as connection:
            connection.execute("DROP SCHEMA IF EXISTS public CASCADE")
            connection.execute("CREATE SCHEMA public")
            connection.execute(
                sql.SQL("ALTER SCHEMA public OWNER TO {}").format(
                    sql.Identifier(str(_configured_value("DB_USER", "postgres")))
                )
            )
    except psycopg.Error as error:
        raise RuntimeError(
            f"Could not reset the isolated test database {TEST_DATABASE_NAME!r}"
        ) from error


def _upgrade_test_database() -> None:
    environment = os.environ.copy()
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=PROJECT_ROOT,
        env=environment,
        check=True,
    )


@pytest.fixture(scope="session", autouse=True)
def isolated_test_database():
    """Provision and migrate only the dedicated database before any test runs."""

    _ensure_test_database_exists()
    _reset_test_database()
    _upgrade_test_database()
    yield TEST_DATABASE_NAME
