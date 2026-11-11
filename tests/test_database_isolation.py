import os

import pytest
from app.core.config import settings
from app.database.configuration import (
    UnsafeTestDatabaseConfiguration,
    validate_test_database_name,
)
from app.database.database import engine
from sqlalchemy import text


def test_backend_tests_use_the_dedicated_database():
    with engine.connect() as connection:
        current_database = connection.execute(text("SELECT current_database()")).scalar_one()

    assert settings.APP_ENV == "test"
    assert settings.DB_NAME == os.environ["VAXINSIGHT_TEST_DB_NAME"]
    assert current_database == settings.DB_NAME
    assert settings.DB_NAME != os.environ["VAXINSIGHT_DEVELOPMENT_DB_NAME"]
    assert settings.DB_NAME not in {
        "vaccine_ai",
        "vaccine_ai_prod",
        "vaccine_ai_production",
        "production",
    }
    if os.environ.get("VAXINSIGHT_PRODUCTION_DB_NAME"):
        assert settings.DB_NAME != os.environ["VAXINSIGHT_PRODUCTION_DB_NAME"]


@pytest.mark.parametrize(
    "database_name",
    ["vaccine_ai", "vaccine_ai_prod", "vaccine_ai_production", "postgres"],
)
def test_test_database_guard_rejects_protected_database_names(database_name):
    with pytest.raises(UnsafeTestDatabaseConfiguration):
        validate_test_database_name(database_name, {database_name})


def test_test_database_guard_requires_a_test_segment():
    with pytest.raises(UnsafeTestDatabaseConfiguration):
        validate_test_database_name("vaccine_ai_sandbox", set())


def test_test_database_guard_rejects_a_protected_test_named_database():
    with pytest.raises(UnsafeTestDatabaseConfiguration):
        validate_test_database_name("vaccine_ai_test", {"vaccine_ai_test"})
