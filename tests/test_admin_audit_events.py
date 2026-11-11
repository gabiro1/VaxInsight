from datetime import UTC, datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from app.api.dependencies import get_current_user
from app.database.database import Base
from app.database.dependencies import get_db
from app.main import app
from app.models.auth import AuditEvent
from app.models.user import AccountStatus, User, UserRole
from app.services.audit import AuditEventPage, list_audit_events
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


def make_user(role: str) -> User:
    now = datetime.now(UTC)
    return User(
        id=uuid4(),
        email=f"{role}-{uuid4()}@example.com",
        hashed_password="argon2-hash",
        is_active=True,
        status=AccountStatus.ACTIVE.value,
        role=role,
        created_at=now,
        updated_at=now,
    )


def make_event(
    *,
    details: dict | None = None,
    created_at: datetime | None = None,
) -> AuditEvent:
    return AuditEvent(
        id=uuid4(),
        actor_user_id=uuid4(),
        target_user_id=uuid4(),
        action="account_role_changed",
        outcome="success",
        ip_address="192.0.2.10",
        user_agent="test-agent",
        details=details,
        created_at=created_at or datetime.now(UTC),
    )


def override_dependencies(mock_db: Session, role: str) -> None:
    user = make_user(role)

    def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: user


def test_administrator_can_retrieve_audit_events():
    mock_db = MagicMock(spec=Session)
    override_dependencies(mock_db, UserRole.ADMINISTRATOR.value)
    event = make_event(details={"role": "reviewer"})

    with patch(
        "app.api.routes.admin.list_audit_events",
        return_value=AuditEventPage(events=[event], total=1),
    ):
        response = client.get("/api/v1/admin/audit-events")

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.json() == {
        "items": [
            {
                "id": str(event.id),
                "actor_user_id": str(event.actor_user_id),
                "target_user_id": str(event.target_user_id),
                "action": "account_role_changed",
                "outcome": "success",
                "ip_address": "192.0.2.10",
                "user_agent": "test-agent",
                "created_at": event.created_at.isoformat().replace("+00:00", "Z"),
                "details": {"role": "reviewer"},
            }
        ],
        "page": 1,
        "page_size": 50,
        "total": 1,
        "total_pages": 1,
    }


@pytest.mark.parametrize("role", [UserRole.CHW.value, UserRole.REVIEWER.value])
def test_non_administrator_cannot_retrieve_audit_events(role):
    mock_db = MagicMock(spec=Session)
    override_dependencies(mock_db, role)

    response = client.get("/api/v1/admin/audit-events")

    assert response.status_code == 403


def test_unauthenticated_request_is_rejected():
    response = client.get("/api/v1/admin/audit-events")

    assert response.status_code == 401


def test_pagination_and_filters_are_validated_and_forwarded():
    mock_db = MagicMock(spec=Session)
    override_dependencies(mock_db, UserRole.ADMINISTRATOR.value)
    actor_id = uuid4()
    target_id = uuid4()
    start_date = datetime(2026, 1, 1, tzinfo=UTC)
    end_date = datetime(2026, 1, 31, 23, 59, tzinfo=UTC)

    with patch(
        "app.api.routes.admin.list_audit_events",
        return_value=AuditEventPage(events=[], total=5),
    ) as list_events:
        response = client.get(
            "/api/v1/admin/audit-events",
            params={
                "page": 2,
                "page_size": 2,
                "action": " login ",
                "outcome": "failure",
                "actor_user_id": str(actor_id),
                "target_user_id": str(target_id),
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
        )

    assert response.status_code == 200
    list_events.assert_called_once_with(
        mock_db,
        page=2,
        page_size=2,
        action="login",
        outcome="failure",
        actor_user_id=actor_id,
        target_user_id=target_id,
        start_date=start_date,
        end_date=end_date,
    )
    assert response.json()["total_pages"] == 3


@pytest.mark.parametrize(
    "params",
    [
        {"page": "0"},
        {"page_size": "101"},
        {
            "start_date": "2026-02-01T00:00:00Z",
            "end_date": "2026-01-01T00:00:00Z",
        },
    ],
)
def test_invalid_pagination_or_date_range_is_rejected(params):
    mock_db = MagicMock(spec=Session)
    override_dependencies(mock_db, UserRole.ADMINISTRATOR.value)

    with patch("app.api.routes.admin.list_audit_events") as list_events:
        response = client.get(
            "/api/v1/admin/audit-events",
            params=params,
        )

    assert response.status_code == 422
    list_events.assert_not_called()


def test_sensitive_details_are_not_exposed():
    mock_db = MagicMock(spec=Session)
    override_dependencies(mock_db, UserRole.ADMINISTRATOR.value)
    event = make_event(
        details={
            "role": "chw",
            "status": "active",
            "password": "plain-text-password",
            "hashed_password": "argon2-hash",
            "access_token": "access-secret",
            "refresh_token": "refresh-secret",
            "invitation_token": "invitation-secret",
            "password_reset_token": "reset-secret",
            "email_verification_token": "verification-secret",
            "nested": {"secret": "nested-secret"},
        }
    )

    with patch(
        "app.api.routes.admin.list_audit_events",
        return_value=AuditEventPage(events=[event], total=1),
    ):
        response = client.get("/api/v1/admin/audit-events")

    assert response.status_code == 200
    body = response.json()
    assert body["items"][0]["details"] == {
        "role": "chw",
        "status": "active",
    }
    for secret in (
        "plain-text-password",
        "argon2-hash",
        "access-secret",
        "refresh-secret",
        "invitation-secret",
        "reset-secret",
        "verification-secret",
        "nested-secret",
    ):
        assert secret not in response.text
    assert "password" not in body["items"][0]["details"]
    assert "access_token" not in body["items"][0]["details"]


def test_empty_audit_log_returns_empty_page():
    mock_db = MagicMock(spec=Session)
    override_dependencies(mock_db, UserRole.ADMINISTRATOR.value)

    with patch(
        "app.api.routes.admin.list_audit_events",
        return_value=AuditEventPage(events=[], total=0),
    ):
        response = client.get("/api/v1/admin/audit-events")

    assert response.status_code == 200
    assert response.json() == {
        "items": [],
        "page": 1,
        "page_size": 50,
        "total": 0,
        "total_pages": 0,
    }


def test_audit_query_filters_paginates_and_orders_newest_first():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    actor_id = uuid4()
    target_id = uuid4()

    with Session(engine) as db:
        oldest = make_event(
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        oldest.actor_user_id = actor_id
        oldest.target_user_id = target_id

        newest = make_event(
            created_at=datetime(2026, 1, 2, tzinfo=UTC),
        )
        newest.actor_user_id = actor_id
        newest.target_user_id = target_id

        wrong_action = make_event(
            created_at=datetime(2026, 1, 1, 12, tzinfo=UTC),
        )
        wrong_action.actor_user_id = actor_id
        wrong_action.target_user_id = target_id
        wrong_action.action = "login"

        wrong_outcome = make_event(
            created_at=datetime(2026, 1, 1, 13, tzinfo=UTC),
        )
        wrong_outcome.actor_user_id = actor_id
        wrong_outcome.target_user_id = target_id
        wrong_outcome.outcome = "failure"

        wrong_actor = make_event(
            created_at=datetime(2026, 1, 1, 14, tzinfo=UTC),
        )
        wrong_actor.target_user_id = target_id

        wrong_target = make_event(
            created_at=datetime(2026, 1, 1, 15, tzinfo=UTC),
        )
        wrong_target.actor_user_id = actor_id

        outside_date = make_event(
            created_at=datetime(2026, 1, 3, tzinfo=UTC),
        )
        outside_date.actor_user_id = actor_id
        outside_date.target_user_id = target_id

        db.add_all(
            [
                oldest,
                newest,
                wrong_action,
                wrong_outcome,
                wrong_actor,
                wrong_target,
                outside_date,
            ]
        )
        db.commit()

        first_page = list_audit_events(
            db,
            page=1,
            page_size=1,
            action="account_role_changed",
            outcome="success",
            actor_user_id=actor_id,
            target_user_id=target_id,
            start_date=datetime(2026, 1, 1, tzinfo=UTC),
            end_date=datetime(2026, 1, 2, 23, 59, tzinfo=UTC),
        )
        second_page = list_audit_events(
            db,
            page=2,
            page_size=1,
            action="account_role_changed",
            outcome="success",
            actor_user_id=actor_id,
            target_user_id=target_id,
            start_date=datetime(2026, 1, 1, tzinfo=UTC),
            end_date=datetime(2026, 1, 2, 23, 59, tzinfo=UTC),
        )

    assert first_page.total == 2
    assert [event.id for event in first_page.events] == [newest.id]
    assert [event.id for event in second_page.events] == [oldest.id]
