from datetime import UTC, datetime
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from app.api.dependencies import (
    get_current_user,
    require_any_permissions,
    require_permissions,
)
from app.core.permissions import (
    ALL_PERMISSIONS,
    FUTURE_PERMISSIONS,
    IMPLEMENTED_PERMISSIONS,
    PERMISSION_BY_NAME,
    PERMISSION_DEFINITIONS,
    ROLE_PERMISSIONS,
    Permission,
    effective_permissions_for_user,
    has_permission,
    permissions_for_role,
    validate_permission,
)
from app.database.dependencies import get_db
from app.main import app
from app.models.user import AccountStatus, User, UserRole
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

client = TestClient(app)


def make_user(
    role: str | None,
    *,
    status: str = AccountStatus.ACTIVE.value,
    is_active: bool = True,
) -> User:
    now = datetime.now(UTC)
    return User(
        id=uuid4(),
        email=f"{uuid4()}@example.com",
        hashed_password="argon2-hash",
        is_active=is_active,
        status=status,
        role=role,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def admin_api_client():
    mock_db = MagicMock(spec=Session)
    admin = make_user(UserRole.ADMINISTRATOR.value)

    def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: admin
    return client, mock_db, admin


def test_permission_catalogue_and_role_mapping_are_explicit():
    definition_names = {definition.name for definition in PERMISSION_DEFINITIONS}

    assert definition_names == ALL_PERMISSIONS
    assert set(PERMISSION_BY_NAME) == ALL_PERMISSIONS
    assert IMPLEMENTED_PERMISSIONS.isdisjoint(FUTURE_PERMISSIONS)
    assert IMPLEMENTED_PERMISSIONS | FUTURE_PERMISSIONS == ALL_PERMISSIONS
    assert set(ROLE_PERMISSIONS) == {role.value for role in UserRole}
    assert all(
        assigned <= IMPLEMENTED_PERMISSIONS for assigned in ROLE_PERMISSIONS.values()
    )
    assert not any(
        future_permission in assigned
        for assigned in ROLE_PERMISSIONS.values()
        for future_permission in FUTURE_PERMISSIONS
    )


def test_unknown_permissions_fail_closed():
    with pytest.raises(ValueError, match="Unknown permission"):
        validate_permission("permission.escalate")

    with pytest.raises(ValueError, match="Unknown permission"):
        require_permissions("permission.escalate")

    with pytest.raises(ValueError, match="reserved for future use"):
        require_permissions(Permission.ANALYSIS_REQUEST)


def test_permission_checks_support_all_and_any_policies():
    administrator = make_user(UserRole.ADMINISTRATOR.value)
    reviewer = make_user(UserRole.REVIEWER.value)

    assert has_permission(administrator, Permission.USER_READ)
    assert not has_permission(reviewer, Permission.USER_READ)
    assert permissions_for_role(UserRole.REVIEWER) == effective_permissions_for_user(
        reviewer
    )

    require_all = require_permissions(
        Permission.USER_READ,
        Permission.ROLE_READ,
    )
    assert require_all(administrator) is administrator

    with pytest.raises(HTTPException) as error:
        require_all(reviewer)
    assert error.value.status_code == 403

    require_any = require_any_permissions(
        Permission.USER_READ,
        Permission.NARRATIVE_READ_OWN,
    )
    assert require_any(reviewer) is reviewer


def test_permission_dependencies_reject_inactive_accounts():
    inactive_administrator = make_user(
        UserRole.ADMINISTRATOR.value,
        status=AccountStatus.SUSPENDED.value,
        is_active=False,
    )

    with pytest.raises(HTTPException) as error:
        require_permissions(Permission.USER_READ)(inactive_administrator)

    assert error.value.status_code == 401


def test_administrator_can_inspect_permission_catalogue(admin_api_client):
    response = admin_api_client[0].get("/api/v1/admin/permissions")

    assert response.status_code == 200
    items = {item["name"]: item for item in response.json()["items"]}
    assert items[Permission.USER_READ.value]["implemented"] is True
    assert items[Permission.NARRATIVE_ASSIGN.value]["implemented"] is True
    assert items[Permission.NARRATIVE_READ_ASSIGNED.value]["implemented"] is True
    assert items[Permission.NARRATIVE_REVIEW.value] == {
        "name": Permission.NARRATIVE_REVIEW.value,
        "description": "Perform an authorized narrative review.",
        "implemented": True,
        "assignable": True,
    }


def test_administrator_can_inspect_role_assignments(admin_api_client):
    response = admin_api_client[0].get("/api/v1/admin/roles")

    assert response.status_code == 200
    roles = {item["role"]: item["permissions"] for item in response.json()["items"]}
    assert set(roles) == {role.value for role in UserRole}
    assert roles[UserRole.ADMINISTRATOR.value] == sorted(
        ROLE_PERMISSIONS[UserRole.ADMINISTRATOR.value]
    )
    assert not set(roles[UserRole.ADMINISTRATOR.value]) & FUTURE_PERMISSIONS


def test_administrator_can_inspect_one_role(admin_api_client):
    response = admin_api_client[0].get("/api/v1/admin/roles/reviewer")

    assert response.status_code == 200
    assert response.json() == {
        "role": UserRole.REVIEWER.value,
        "permissions": sorted(ROLE_PERMISSIONS[UserRole.REVIEWER.value]),
    }


def test_administrator_can_inspect_active_user_permissions(admin_api_client):
    client_instance, mock_db, _admin = admin_api_client
    target = make_user(UserRole.REVIEWER.value)
    mock_db.get.return_value = target

    response = client_instance.get(f"/api/v1/admin/users/{target.id}/permissions")

    assert response.status_code == 200
    assert response.json() == {
        "id": str(target.id),
        "role": UserRole.REVIEWER.value,
        "status": AccountStatus.ACTIVE.value,
        "permissions": sorted(ROLE_PERMISSIONS[UserRole.REVIEWER.value]),
    }


def test_inactive_user_has_no_effective_permissions(admin_api_client):
    client_instance, mock_db, _admin = admin_api_client
    target = make_user(
        UserRole.ADMINISTRATOR.value,
        status=AccountStatus.SUSPENDED.value,
        is_active=False,
    )
    mock_db.get.return_value = target

    response = client_instance.get(f"/api/v1/admin/users/{target.id}/permissions")

    assert response.status_code == 200
    assert response.json()["permissions"] == []


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/admin/permissions",
        "/api/v1/admin/roles",
        "/api/v1/admin/roles/reviewer",
        f"/api/v1/admin/users/{uuid4()}/permissions",
    ],
)
def test_non_administrator_cannot_inspect_permissions(admin_api_client, path):
    app.dependency_overrides[get_current_user] = lambda: make_user(
        UserRole.REVIEWER.value
    )

    response = admin_api_client[0].get(path)

    assert response.status_code == 403


def test_unauthenticated_permission_inspection_is_rejected(admin_api_client):
    app.dependency_overrides.pop(get_current_user)

    response = admin_api_client[0].get("/api/v1/admin/permissions")

    assert response.status_code == 401


def test_role_update_rejects_permission_injection(admin_api_client):
    client_instance, _mock_db, admin = admin_api_client

    response = client_instance.patch(
        f"/api/v1/auth/admin/users/{admin.id}/role",
        json={
            "role": UserRole.CHW.value,
            "permissions": [Permission.USER_MANAGE.value],
        },
    )

    assert response.status_code == 422


def test_invitation_creation_rejects_permission_injection(admin_api_client):
    response = admin_api_client[0].post(
        "/api/v1/auth/invitations",
        json={
            "email": "invitee@example.com",
            "role": UserRole.CHW.value,
            "permissions": [Permission.USER_MANAGE.value],
        },
    )

    assert response.status_code == 422
