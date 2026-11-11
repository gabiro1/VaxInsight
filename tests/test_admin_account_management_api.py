from datetime import UTC, datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from app.api.dependencies import get_current_user
from app.database.dependencies import get_db
from app.main import app
from app.models.user import AccountStatus, User, UserRole
from app.services.auth import LastActiveAdministratorError
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def make_user(role: str) -> User:
    now = datetime.now(UTC)

    return User(
        id=uuid4(),
        email=f"{uuid4()}@example.com",
        hashed_password="argon2-test-hash",
        is_active=True,
        status=AccountStatus.ACTIVE.value,
        role=role,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def admin_api_client():
    mock_db = MagicMock(spec=Session)
    admin = make_user(UserRole.ADMINISTRATOR.value)

    def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: admin

    client = TestClient(app)

    try:
        yield client, mock_db, admin
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize(
    "new_status",
    [
        AccountStatus.SUSPENDED.value,
        AccountStatus.DEACTIVATED.value,
        AccountStatus.DELETED.value,
    ],
)
def test_administrator_cannot_deactivate_own_account(admin_api_client, new_status):
    client, mock_db, admin = admin_api_client
    mock_db.get.return_value = admin

    response = client.patch(
        f"/api/v1/auth/admin/users/{admin.id}/status",
        json={"status": new_status},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "An administrator cannot deactivate their own account"
    )


def test_administrator_cannot_demote_own_role(admin_api_client):
    client, mock_db, admin = admin_api_client
    mock_db.get.return_value = admin

    response = client.patch(
        f"/api/v1/auth/admin/users/{admin.id}/role",
        json={"role": UserRole.CHW.value},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "An administrator cannot remove their own administrator role"
    )


def test_last_active_administrator_deactivation_returns_409(
    admin_api_client,
):
    client, mock_db, _admin = admin_api_client
    target = make_user(UserRole.ADMINISTRATOR.value)
    mock_db.get.return_value = target

    with patch(
        "app.api.routes.auth.change_account_status",
        side_effect=LastActiveAdministratorError,
    ):
        response = client.patch(
            f"/api/v1/auth/admin/users/{target.id}/status",
            json={"status": AccountStatus.SUSPENDED.value},
        )

    assert response.status_code == 409
    assert response.json()["detail"] == ("Cannot remove the last active administrator")


def test_last_active_administrator_demotion_returns_409(
    admin_api_client,
):
    client, mock_db, _admin = admin_api_client
    target = make_user(UserRole.ADMINISTRATOR.value)
    mock_db.get.return_value = target

    with patch(
        "app.api.routes.auth.change_user_role",
        side_effect=LastActiveAdministratorError,
    ):
        response = client.patch(
            f"/api/v1/auth/admin/users/{target.id}/role",
            json={"role": UserRole.REVIEWER.value},
        )

    assert response.status_code == 409
    assert response.json()["detail"] == ("Cannot remove the last active administrator")


def test_invalid_account_status_returns_422(admin_api_client):
    client, mock_db, _admin = admin_api_client
    target = make_user(UserRole.CHW.value)
    mock_db.get.return_value = target

    response = client.patch(
        f"/api/v1/auth/admin/users/{target.id}/status",
        json={"status": "pending"},
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    "endpoint,payload",
    [
        ("status", {"status": "suspended"}),
        ("role", {"role": "chw"}),
    ],
)
def test_unauthenticated_user_cannot_manage_accounts(
    admin_api_client, endpoint, payload
):
    client, _mock_db, _admin = admin_api_client

    app.dependency_overrides.pop(get_current_user, None)

    response = client.patch(
        f"/api/v1/auth/admin/users/{uuid4()}/{endpoint}",
        json=payload,
    )

    assert response.status_code == 401


@pytest.mark.parametrize(
    "role",
    [
        UserRole.CHW.value,
        UserRole.REVIEWER.value,
    ],
)
@pytest.mark.parametrize(
    "endpoint,payload",
    [
        ("status", {"status": "suspended"}),
        ("role", {"role": "chw"}),
    ],
)
def test_non_administrator_cannot_manage_accounts(
    admin_api_client, role, endpoint, payload
):
    client, _mock_db, _admin = admin_api_client
    non_admin = make_user(role)

    app.dependency_overrides[get_current_user] = lambda: non_admin

    response = client.patch(
        f"/api/v1/auth/admin/users/{uuid4()}/{endpoint}",
        json=payload,
    )

    assert response.status_code == 403
