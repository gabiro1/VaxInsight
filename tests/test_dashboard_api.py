from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from app.api.dependencies import get_current_user
from app.database.database import Base
from app.database.dependencies import get_db
from app.main import app
from app.models.auth import Invitation, RefreshSession
from app.models.narrative import Narrative
from app.models.review import AssignmentStatus, NarrativeAssignment, ReviewStatus
from app.models.user import AccountStatus, User, UserRole
from app.services.dashboard import (
    get_dashboard_summary,
    get_personal_dashboard_summary,
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


def make_user(role: str | None, status: str, *, is_active: bool) -> User:
    user_id = uuid4()
    now = datetime.now(UTC)
    return User(
        id=user_id,
        email=f"{user_id}@example.com",
        hashed_password="argon2-hash",
        is_active=is_active,
        status=status,
        role=role,
        created_at=now,
        updated_at=now,
    )


def override_dependencies(mock_db: Session, role: str) -> None:
    user = make_user(
        role,
        AccountStatus.ACTIVE.value,
        is_active=True,
    )

    def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: user


def test_administrator_can_retrieve_dashboard_summary():
    mock_db = MagicMock(spec=Session)
    override_dependencies(mock_db, UserRole.ADMINISTRATOR.value)
    summary = {
        "users": {
            "total": 6,
            "active": 2,
            "pending": 1,
            "suspended": 1,
            "deactivated": 1,
            "deleted": 1,
            "by_role": {
                "community_member": 0,
                "chw": 2,
                "reviewer": 2,
                "administrator": 1,
                "unassigned": 1,
            },
        },
        "invitations": {
            "total": 4,
            "pending": 1,
            "accepted": 1,
            "expired": 1,
            "revoked": 1,
        },
        "sessions": {
            "active": 1,
            "revoked": 1,
            "expired": 1,
        },
        "platform": {
            "period_days": 30,
            "total_narratives": 0,
            "active_users": 2,
            "review_completion_rate": 0,
            "trusted_info_rate": 0,
        },
    }

    with patch(
        "app.api.routes.admin.get_dashboard_summary",
        return_value=summary,
    ) as get_summary:
        response = client.get("/api/v1/admin/dashboard/summary")

    assert response.status_code == 200
    assert response.json() == summary
    assert response.headers["Cache-Control"] == "no-store"
    get_summary.assert_called_once_with(mock_db)


@pytest.mark.parametrize("role", [UserRole.CHW.value, UserRole.REVIEWER.value])
def test_non_administrator_cannot_retrieve_dashboard_summary(role):
    mock_db = MagicMock(spec=Session)
    override_dependencies(mock_db, role)

    response = client.get("/api/v1/admin/dashboard/summary")

    assert response.status_code == 403


def test_chw_can_retrieve_owner_scoped_personal_dashboard_summary():
    mock_db = MagicMock(spec=Session)
    override_dependencies(mock_db, UserRole.CHW.value)
    summary = {
        "activity": {"submitted": 2, "under_review": 1, "reviewed": 1},
        "recent_narratives": [],
    }

    with patch(
        "app.api.routes.dashboard.get_personal_dashboard_summary",
        return_value=summary,
    ) as get_summary:
        response = client.get("/api/v1/dashboard/summary")

    assert response.status_code == 200
    assert response.json() == summary
    assert get_summary.call_args.args == (mock_db,)
    assert get_summary.call_args.kwargs["owner_id"]


def test_personal_dashboard_summary_only_counts_owned_records():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    now = datetime.now(UTC)
    owner = make_user(UserRole.CHW.value, AccountStatus.ACTIVE.value, is_active=True)
    reviewer = make_user(
        UserRole.REVIEWER.value,
        AccountStatus.ACTIVE.value,
        is_active=True,
    )
    first = Narrative(
        submitted_by_id=owner.id,
        content="First owned narrative",
        submitted_at=now - timedelta(minutes=2),
        updated_at=now - timedelta(minutes=2),
    )
    second = Narrative(
        submitted_by_id=owner.id,
        content="Second owned narrative",
        submitted_at=now - timedelta(minutes=1),
        updated_at=now - timedelta(minutes=1),
    )
    other = Narrative(
        submitted_by_id=uuid4(),
        content="Other account narrative",
        submitted_at=now,
        updated_at=now,
    )

    with Session(engine) as db:
        db.add_all([owner, reviewer, first, second, other])
        db.flush()
        db.add_all(
            [
                NarrativeAssignment(
                    narrative_id=first.id,
                    reviewer_id=reviewer.id,
                    assigned_by_user_id=reviewer.id,
                    status=AssignmentStatus.ACTIVE.value,
                    review_status=ReviewStatus.IN_REVIEW.value,
                ),
                NarrativeAssignment(
                    narrative_id=second.id,
                    reviewer_id=reviewer.id,
                    assigned_by_user_id=reviewer.id,
                    status=AssignmentStatus.ACTIVE.value,
                    review_status=ReviewStatus.REVIEWED.value,
                ),
            ]
        )
        db.commit()

        summary = get_personal_dashboard_summary(db, owner_id=owner.id)

    assert summary["activity"] == {
        "submitted": 2,
        "under_review": 1,
        "reviewed": 1,
    }
    assert [item["content"] for item in summary["recent_narratives"]] == [
        "Second owned narrative",
        "First owned narrative",
    ]
    assert [item["review_status"] for item in summary["recent_narratives"]] == [
        ReviewStatus.REVIEWED.value,
        ReviewStatus.IN_REVIEW.value,
    ]


def test_unauthenticated_dashboard_request_is_rejected():
    response = client.get("/api/v1/admin/dashboard/summary")

    assert response.status_code == 401


def test_dashboard_summary_counts_users_invitations_and_sessions():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    now = datetime.now(UTC)

    users = [
        make_user(UserRole.CHW.value, AccountStatus.ACTIVE.value, is_active=True),
        make_user(
            UserRole.ADMINISTRATOR.value, AccountStatus.ACTIVE.value, is_active=True
        ),
        make_user(
            UserRole.REVIEWER.value, AccountStatus.PENDING.value, is_active=False
        ),
        make_user(None, AccountStatus.SUSPENDED.value, is_active=False),
        make_user(UserRole.CHW.value, AccountStatus.DEACTIVATED.value, is_active=False),
        make_user(
            UserRole.REVIEWER.value, AccountStatus.DELETED.value, is_active=False
        ),
    ]
    admin_id = users[1].id

    invitations = [
        Invitation(
            email="pending@example.com",
            role=UserRole.CHW.value,
            token_hash="pending-hash",
            invited_by_id=admin_id,
            expires_at=now + timedelta(hours=1),
        ),
        Invitation(
            email="accepted@example.com",
            role=UserRole.REVIEWER.value,
            token_hash="accepted-hash",
            invited_by_id=admin_id,
            expires_at=now + timedelta(hours=1),
            accepted_at=now,
        ),
        Invitation(
            email="expired@example.com",
            role=UserRole.CHW.value,
            token_hash="expired-hash",
            invited_by_id=admin_id,
            expires_at=now - timedelta(hours=1),
        ),
        Invitation(
            email="revoked@example.com",
            role=UserRole.ADMINISTRATOR.value,
            token_hash="revoked-hash",
            invited_by_id=admin_id,
            expires_at=now + timedelta(hours=1),
            revoked_at=now,
        ),
    ]

    sessions = [
        RefreshSession(
            user_id=users[0].id,
            token_hash="active-session-hash",
            expires_at=now + timedelta(hours=1),
        ),
        RefreshSession(
            user_id=users[0].id,
            token_hash="revoked-session-hash",
            expires_at=now + timedelta(hours=1),
            revoked_at=now,
        ),
        RefreshSession(
            user_id=users[0].id,
            token_hash="expired-session-hash",
            expires_at=now - timedelta(hours=1),
        ),
    ]

    with Session(engine) as db:
        db.add_all([*users, *invitations, *sessions])
        db.commit()
        summary = get_dashboard_summary(db)

    assert summary == {
        "users": {
            "total": 6,
            "active": 2,
            "pending": 1,
            "suspended": 1,
            "deactivated": 1,
            "deleted": 1,
            "by_role": {
                "community_member": 0,
                "chw": 2,
                "reviewer": 2,
                "administrator": 1,
                "unassigned": 1,
            },
        },
        "invitations": {
            "total": 4,
            "pending": 1,
            "accepted": 1,
            "expired": 1,
            "revoked": 1,
        },
        "sessions": {
            "active": 1,
            "revoked": 1,
            "expired": 1,
        },
        "platform": {
            "period_days": 30,
            "total_narratives": 0,
            "active_users": 2,
            "review_completion_rate": 0,
            "trusted_info_rate": 0,
        },
    }


def test_empty_dashboard_tables_return_zero_counts():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        summary = get_dashboard_summary(db)

    assert summary == {
        "users": {
            "total": 0,
            "active": 0,
            "pending": 0,
            "suspended": 0,
            "deactivated": 0,
            "deleted": 0,
            "by_role": {
                "community_member": 0,
                "chw": 0,
                "reviewer": 0,
                "administrator": 0,
                "unassigned": 0,
            },
        },
        "invitations": {
            "total": 0,
            "pending": 0,
            "accepted": 0,
            "expired": 0,
            "revoked": 0,
        },
        "sessions": {
            "active": 0,
            "revoked": 0,
            "expired": 0,
        },
        "platform": {
            "period_days": 30,
            "total_narratives": 0,
            "active_users": 0,
            "review_completion_rate": 0,
            "trusted_info_rate": 0,
        },
    }


def test_dashboard_summary_contains_no_sensitive_fields():
    mock_db = MagicMock(spec=Session)
    override_dependencies(mock_db, UserRole.ADMINISTRATOR.value)

    with patch(
        "app.api.routes.admin.get_dashboard_summary",
        return_value={
            "users": {
                "total": 0,
                "active": 0,
                "pending": 0,
                "suspended": 0,
                "deactivated": 0,
                "deleted": 0,
                "by_role": {
                    "community_member": 0,
                    "chw": 0,
                    "reviewer": 0,
                    "administrator": 0,
                    "unassigned": 0,
                },
            },
            "invitations": {
                "total": 0,
                "pending": 0,
                "accepted": 0,
                "expired": 0,
                "revoked": 0,
            },
            "sessions": {"active": 0, "revoked": 0, "expired": 0},
            "platform": {
                "period_days": 30,
                "total_narratives": 0,
                "active_users": 0,
                "review_completion_rate": 0,
                "trusted_info_rate": 0,
            },
        },
    ):
        response = client.get("/api/v1/admin/dashboard/summary")

    body = response.json()
    assert response.status_code == 200
    assert "email" not in body
    assert "password" not in body
    assert "token" not in response.text
    assert "hash" not in response.text
