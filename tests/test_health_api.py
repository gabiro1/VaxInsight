from unittest.mock import MagicMock

from app.core.config import settings
from app.database.dependencies import get_db
from app.main import app
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

client = TestClient(app)


def test_health_endpoint_returns_healthy_status():
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["application"] == settings.APP_NAME


def test_database_health_endpoint_confirms_connection():
    response = client.get("/api/v1/health/database")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert "PostgreSQL" in data["message"]


def test_root_endpoint_returns_welcome_message():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["message"] == "Welcome to VaxInsight API"
    assert response.json()["documentation"] == "/docs"


def test_database_health_endpoint_returns_503_when_database_fails():
    mock_db = MagicMock()

    mock_db.execute.side_effect = OperationalError(
        "SELECT 1",
        {},
        Exception("Database connection failed"),
    )

    def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db

    try:
        response = client.get("/api/v1/health/database")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json()["detail"] == "Database temporarily unavailable"
