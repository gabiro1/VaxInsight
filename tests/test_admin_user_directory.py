from datetime import UTC, datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from app.api.dependencies import get_current_user
from app.database.database import Base
from app.database.dependencies import get_db
from app.main import app
from app.models.user import AccountStatus, User, UserRole
from app.services.admin_users import (
    AdminUserPage,
    AdminUserRecord,
    get_admin_user,
    list_admin_users,
)
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


def make_user(
    *,
    email: str,
    role: str | None = UserRole.CHW.value,
    status: str = AccountStatus.ACTIVE.value,
    email_verified: bool = True,
    created_at: datetime | None = None,
) -> User:
    now = created_at or datetime.now(UTC)
    return User(
        id=uuid4(),
        email=email,
        hashed_password="argon2-hash-that-must-not-be-returned",
        is_active=status == AccountStatus.ACTIVE.value,
        status=status,
        role=role,
        email_verified_at=now if email_verified else None,
        last_login_at=now,
        created_at=now,
        updated_at=now,
    )


def record_from_user(user: User) -> AdminUserRecord:
    return AdminUserRecord(
        id=user.id,
        email=user.email,
        role=user.role,
        status=user.status,
        email_verified_at=user.email_verified_at,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
        updated_at=user.updated_at,
    )


def override_dependencies(mock_db: Session, role: str) -> None:
    current_user = make_user(
        email=f"{role}-{uuid4()}@example.com",
        role=role,
    )

    def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: current_user


def test_administrator_can_retrieve_user_directory():
    mock_db = MagicMock(spec=Session)
    override_dependencies(mock_db, UserRole.ADMINISTRATOR.value)
    user = make_user(email="chw@example.com")
    record = record_from_user(user)

    with patch(
        "app.api.routes.admin.list_admin_users",
        return_value=AdminUserPage(users=[record], total=1),
    ):
        response = client.get("/api/v1/admin/users")

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    body = response.json()
    assert body["page"] == 1
    assert body["page_size"] == 20
    assert body["total"] == 1
    assert body["total_pages"] == 1
    assert body["items"] == [
        {
            "id": str(user.id),
            "email": "chw@example.com",
            "role": "chw",
            "status": "active",
            "email_verified": True,
            "created_at": user.created_at.isoformat().replace("+00:00", "Z"),
            "last_login_at": user.last_login_at.isoformat().replace("+00:00", "Z"),
            "updated_at": user.updated_at.isoformat().replace("+00:00", "Z"),
        }
    ]


@pytest.mark.parametrize("role", [UserRole.CHW.value, UserRole.REVIEWER.value])
def test_non_administrator_cannot_retrieve_user_directory(role):
    mock_db = MagicMock(spec=Session)
    override_dependencies(mock_db, role)

    response = client.get("/api/v1/admin/users")

    assert response.status_code == 403


def test_unauthenticated_user_directory_request_is_rejected():
    response = client.get("/api/v1/admin/users")

    assert response.status_code == 401


def test_directory_pagination_and_filters_are_forwarded():
    mock_db = MagicMock(spec=Session)
    override_dependencies(mock_db, UserRole.ADMINISTRATOR.value)

    with patch(
        "app.api.routes.admin.list_admin_users",
        return_value=AdminUserPage(users=[], total=5),
    ) as list_users:
        response = client.get(
            "/api/v1/admin/users",
            params={
                "page": 2,
                "page_size": 2,
                "search": "  alice@example.com ",
                "role": "reviewer",
                "status": "suspended",
                "email_verified": "false",
                "sort_by": "email",
                "sort_order": "asc",
            },
        )

    assert response.status_code == 200
    list_users.assert_called_once_with(
        mock_db,
        page=2,
        page_size=2,
        search="alice@example.com",
        role="reviewer",
        status="suspended",
        email_verified=False,
        sort_by="email",
        sort_order="asc",
    )
    assert response.json()["total_pages"] == 3


@pytest.mark.parametrize(
    "params",
    [
        {"page": "0"},
        {"page_size": "101"},
        {"role": "unknown"},
        {"status": "unknown"},
        {"email_verified": "maybe"},
        {"sort_by": "password"},
        {"sort_order": "sideways"},
        {"search": "   "},
    ],
)
def test_invalid_directory_filters_are_rejected(params):
    mock_db = MagicMock(spec=Session)
    override_dependencies(mock_db, UserRole.ADMINISTRATOR.value)

    with patch("app.api.routes.admin.list_admin_users") as list_users:
        response = client.get("/api/v1/admin/users", params=params)

    assert response.status_code == 422
    list_users.assert_not_called()


def test_directory_query_filters_searches_sorts_and_paginates_in_sql():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    users = [
        make_user(
            email="alice@example.com",
            role=UserRole.CHW.value,
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        ),
        make_user(
            email="bob@example.com",
            role=UserRole.REVIEWER.value,
            status=AccountStatus.PENDING.value,
            email_verified=False,
            created_at=datetime(2026, 1, 2, tzinfo=UTC),
        ),
        make_user(
            email="admin@example.com",
            role=UserRole.ADMINISTRATOR.value,
            created_at=datetime(2026, 1, 3, tzinfo=UTC),
        ),
    ]

    with Session(engine) as db:
        db.add_all(users)
        db.commit()

        page = list_admin_users(
            db,
            page=1,
            page_size=2,
            sort_by="email",
            sort_order="asc",
        )
        search_result = list_admin_users(
            db,
            page=1,
            page_size=20,
            search="alice",
        )
        role_result = list_admin_users(
            db,
            page=1,
            page_size=20,
            role=UserRole.REVIEWER.value,
        )
        status_result = list_admin_users(
            db,
            page=1,
            page_size=20,
            status=AccountStatus.PENDING.value,
        )
        verified_result = list_admin_users(
            db,
            page=1,
            page_size=20,
            email_verified=False,
        )

    assert page.total == 3
    assert [user.email for user in page.users] == [
        "admin@example.com",
        "alice@example.com",
    ]
    assert search_result.total == 1
    assert search_result.users[0].email == "alice@example.com"
    assert role_result.total == 1
    assert role_result.users[0].email == "bob@example.com"
    assert status_result.total == 1
    assert status_result.users[0].email == "bob@example.com"
    assert verified_result.total == 1
    assert verified_result.users[0].email == "bob@example.com"


def test_administrator_can_retrieve_user_details_without_sensitive_fields():
    mock_db = MagicMock(spec=Session)
    override_dependencies(mock_db, UserRole.ADMINISTRATOR.value)
    user = make_user(email="detail@example.com")

    with patch(
        "app.api.routes.admin.get_admin_user",
        return_value=record_from_user(user),
    ):
        response = client.get(f"/api/v1/admin/users/{user.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(user.id)
    assert body["email"] == user.email
    assert body["role"] == "chw"
    assert body["status"] == "active"
    assert body["email_verified"] is True
    assert "hashed_password" not in body
    assert "password_changed_at" not in body
    assert "token_hash" not in response.text
    assert "refresh_token" not in response.text


def test_unknown_user_detail_returns_404():
    mock_db = MagicMock(spec=Session)
    override_dependencies(mock_db, UserRole.ADMINISTRATOR.value)

    with patch("app.api.routes.admin.get_admin_user", return_value=None):
        response = client.get(f"/api/v1/admin/users/{uuid4()}")

    assert response.status_code == 404


def test_empty_directory_returns_empty_page_and_missing_detail():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        page = list_admin_users(db, page=1, page_size=20)
        missing = get_admin_user(db, uuid4())

    assert page.users == []
    assert page.total == 0
    assert missing is None
