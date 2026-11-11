from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from app.api.dependencies import get_current_user
from app.database.database import Base
from app.database.dependencies import get_db
from app.main import app
from app.models.auth import AuditEvent, Invitation
from app.models.user import AccountStatus, User, UserRole
from app.services.admin_invitations import (
    AdminInvitationPage,
    AdminInvitationRecord,
    InvitationNotDeletable,
    delete_revoked_invitation,
    get_admin_invitation,
    list_admin_invitations,
)
from app.services.auth import InvitationNotRevocable, revoke_invitation
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
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


def make_invitation(
    invited_by_id,
    *,
    email: str = "invitee@example.com",
    role: str = UserRole.CHW.value,
    created_at: datetime | None = None,
    expires_at: datetime | None = None,
    accepted_at: datetime | None = None,
    revoked_at: datetime | None = None,
) -> Invitation:
    return Invitation(
        id=uuid4(),
        email=email,
        role=role,
        token_hash=f"{uuid4().hex}{uuid4().hex}",
        invited_by_id=invited_by_id,
        expires_at=expires_at or datetime.now(UTC) + timedelta(hours=1),
        accepted_at=accepted_at,
        revoked_at=revoked_at,
        created_at=created_at or datetime.now(UTC),
    )


def make_record(invitation: Invitation, status: str) -> AdminInvitationRecord:
    return AdminInvitationRecord(
        id=invitation.id,
        email=invitation.email,
        role=invitation.role,
        status=status,
        created_at=invitation.created_at,
        expires_at=invitation.expires_at,
        accepted_at=invitation.accepted_at,
        revoked_at=invitation.revoked_at,
    )


def override_dependencies(mock_db: Session, role: str) -> User:
    current_user = make_user(role)

    def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: current_user
    return current_user


def test_administrator_can_list_invitations():
    mock_db = MagicMock(spec=Session)
    override_dependencies(mock_db, UserRole.ADMINISTRATOR.value)
    invitation = make_invitation(uuid4())
    record = make_record(invitation, "pending")

    with patch(
        "app.api.routes.admin.list_admin_invitations",
        return_value=AdminInvitationPage(invitations=[record], total=1),
    ):
        response = client.get("/api/v1/admin/invitations")

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    body = response.json()
    assert body["page"] == 1
    assert body["page_size"] == 20
    assert body["total"] == 1
    assert body["total_pages"] == 1
    assert body["items"][0]["email"] == invitation.email
    assert body["items"][0]["status"] == "pending"
    assert "token_hash" not in response.text


@pytest.mark.parametrize("role", [UserRole.CHW.value, UserRole.REVIEWER.value])
def test_non_administrator_cannot_list_invitations(role):
    mock_db = MagicMock(spec=Session)
    override_dependencies(mock_db, role)

    response = client.get("/api/v1/admin/invitations")

    assert response.status_code == 403


def test_unauthenticated_invitation_list_is_rejected():
    response = client.get("/api/v1/admin/invitations")

    assert response.status_code == 401


def test_invitation_filters_pagination_and_sorting_are_forwarded():
    mock_db = MagicMock(spec=Session)
    override_dependencies(mock_db, UserRole.ADMINISTRATOR.value)

    with patch(
        "app.api.routes.admin.list_admin_invitations",
        return_value=AdminInvitationPage(invitations=[], total=5),
    ) as list_invitations:
        response = client.get(
            "/api/v1/admin/invitations",
            params={
                "page": 2,
                "page_size": 2,
                "search": "  invitee@example.com ",
                "role": "reviewer",
                "status": "expired",
                "sort_by": "status",
                "sort_order": "asc",
            },
        )

    assert response.status_code == 200
    list_invitations.assert_called_once_with(
        mock_db,
        page=2,
        page_size=2,
        search="invitee@example.com",
        role="reviewer",
        status="expired",
        sort_by="status",
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
        {"sort_by": "email_address"},
        {"sort_order": "sideways"},
        {"search": "   "},
    ],
)
def test_invalid_invitation_filters_return_422(params):
    mock_db = MagicMock(spec=Session)
    override_dependencies(mock_db, UserRole.ADMINISTRATOR.value)

    with patch("app.api.routes.admin.list_admin_invitations") as list_invitations:
        response = client.get("/api/v1/admin/invitations", params=params)

    assert response.status_code == 422
    list_invitations.assert_not_called()


def test_invitation_query_derives_status_filters_and_sorts_in_sql():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    admin = make_user(UserRole.ADMINISTRATOR.value)
    now = datetime.now(UTC)

    pending = make_invitation(
        admin.id,
        email="pending@example.com",
        created_at=now - timedelta(days=4),
        expires_at=now + timedelta(hours=1),
    )
    accepted = make_invitation(
        admin.id,
        email="accepted@example.com",
        created_at=now - timedelta(days=3),
        expires_at=now + timedelta(hours=1),
        accepted_at=now - timedelta(days=2),
    )
    revoked = make_invitation(
        admin.id,
        email="revoked@example.com",
        created_at=now - timedelta(days=2),
        expires_at=now + timedelta(hours=1),
        revoked_at=now - timedelta(days=1),
    )
    expired = make_invitation(
        admin.id,
        email="expired@example.com",
        created_at=now - timedelta(days=1),
        expires_at=now - timedelta(hours=1),
    )

    with Session(engine) as db:
        db.add(admin)
        db.add_all([pending, accepted, revoked, expired])
        db.commit()

        page = list_admin_invitations(
            db,
            page=1,
            page_size=2,
            sort_by="created_at",
            sort_order="desc",
        )
        search_result = list_admin_invitations(
            db,
            page=1,
            page_size=20,
            search="accepted",
        )
        role_result = list_admin_invitations(
            db,
            page=1,
            page_size=20,
            role=UserRole.CHW.value,
        )
        status_result = list_admin_invitations(
            db,
            page=1,
            page_size=20,
            status="expired",
        )
        email_result = list_admin_invitations(
            db,
            page=1,
            page_size=20,
            sort_by="email",
            sort_order="asc",
        )

    assert page.total == 4
    assert [invitation.email for invitation in page.invitations] == [
        "expired@example.com",
        "revoked@example.com",
    ]
    assert [invitation.status for invitation in page.invitations] == [
        "expired",
        "revoked",
    ]
    assert search_result.total == 1
    assert search_result.invitations[0].status == "accepted"
    assert role_result.total == 4
    assert status_result.total == 1
    assert status_result.invitations[0].email == "expired@example.com"
    assert [invitation.email for invitation in email_result.invitations] == [
        "accepted@example.com",
        "expired@example.com",
        "pending@example.com",
        "revoked@example.com",
    ]


def test_administrator_can_retrieve_invitation_details_without_secrets():
    mock_db = MagicMock(spec=Session)
    override_dependencies(mock_db, UserRole.ADMINISTRATOR.value)
    invitation = make_invitation(uuid4())

    with patch(
        "app.api.routes.admin.get_admin_invitation",
        return_value=make_record(invitation, "pending"),
    ):
        response = client.get(f"/api/v1/admin/invitations/{invitation.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(invitation.id)
    assert body["email"] == invitation.email
    assert body["role"] == invitation.role
    assert body["status"] == "pending"
    assert "token_hash" not in body
    assert "token" not in response.text


def test_unknown_invitation_returns_404():
    mock_db = MagicMock(spec=Session)
    override_dependencies(mock_db, UserRole.ADMINISTRATOR.value)

    with patch("app.api.routes.admin.get_admin_invitation", return_value=None):
        response = client.get(f"/api/v1/admin/invitations/{uuid4()}")

    assert response.status_code == 404


def test_administrator_can_revoke_pending_invitation_and_audit_it():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    admin = make_user(UserRole.ADMINISTRATOR.value)
    invitation = make_invitation(admin.id)

    with Session(engine) as db:
        db.add_all([admin, invitation])
        db.commit()
        revoked = revoke_invitation(
            db,
            invitation_id=invitation.id,
            revoked_by=admin,
        )
        audit_event = db.scalar(
            select(AuditEvent).where(
                AuditEvent.action == "invitation_revoked",
                AuditEvent.actor_user_id == admin.id,
            )
        )

    assert revoked is not None
    assert revoked.revoked_at is not None
    assert audit_event is not None
    assert audit_event.details == {"role": invitation.role}


def test_revoke_endpoint_allows_administrator_to_revoke_pending_invitation():
    mock_db = MagicMock(spec=Session)
    admin = override_dependencies(mock_db, UserRole.ADMINISTRATOR.value)
    invitation = make_invitation(admin.id)
    invitation.revoked_at = datetime.now(UTC)

    with patch(
        "app.api.routes.admin.revoke_invitation_service",
        return_value=invitation,
    ) as revoke_service:
        response = client.post(f"/api/v1/admin/invitations/{invitation.id}/revoke")

    assert response.status_code == 200
    assert response.json()["status"] == "revoked"
    revoke_service.assert_called_once_with(
        mock_db,
        invitation_id=invitation.id,
        revoked_by=admin,
    )


def test_administrator_can_delete_revoked_invitation_and_audit_it():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    admin = make_user(UserRole.ADMINISTRATOR.value)
    invitation = make_invitation(admin.id, revoked_at=datetime.now(UTC))
    invitation_role = invitation.role

    with Session(engine) as db:
        db.add_all([admin, invitation])
        db.commit()

        assert delete_revoked_invitation(
            db,
            invitation_id=invitation.id,
            deleted_by=admin,
        ) is True
        assert db.get(Invitation, invitation.id) is None
        audit_event = db.scalar(
            select(AuditEvent).where(
                AuditEvent.action == "invitation_deleted",
                AuditEvent.actor_user_id == admin.id,
            )
        )

    assert audit_event is not None
    assert audit_event.details == {"role": invitation_role}


def test_delete_endpoint_allows_administrator_to_delete_revoked_invitation():
    mock_db = MagicMock(spec=Session)
    admin = override_dependencies(mock_db, UserRole.ADMINISTRATOR.value)
    invitation_id = uuid4()

    with patch(
        "app.api.routes.admin.delete_revoked_invitation",
        return_value=True,
    ) as delete_service:
        response = client.delete(f"/api/v1/admin/invitations/{invitation_id}")

    assert response.status_code == 200
    assert response.json() == {"message": "Invitation deleted successfully"}
    delete_service.assert_called_once_with(
        mock_db,
        invitation_id=invitation_id,
        deleted_by=admin,
    )


@pytest.mark.parametrize("role", [UserRole.CHW.value, UserRole.REVIEWER.value])
def test_non_administrator_cannot_delete_invitation(role):
    mock_db = MagicMock(spec=Session)
    override_dependencies(mock_db, role)

    response = client.delete(f"/api/v1/admin/invitations/{uuid4()}")

    assert response.status_code == 403


@pytest.mark.parametrize("lifecycle", ["pending", "accepted", "expired"])
def test_non_revoked_invitation_cannot_be_deleted(lifecycle):
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    admin = make_user(UserRole.ADMINISTRATOR.value)
    now = datetime.now(UTC)
    invitation = make_invitation(
        admin.id,
        expires_at=now - timedelta(hours=1)
        if lifecycle == "expired"
        else now + timedelta(hours=1),
        accepted_at=now if lifecycle == "accepted" else None,
    )

    with Session(engine) as db:
        db.add_all([admin, invitation])
        db.commit()

        with pytest.raises(InvitationNotDeletable):
            delete_revoked_invitation(
                db,
                invitation_id=invitation.id,
                deleted_by=admin,
            )

        assert db.get(Invitation, invitation.id) is not None


def test_delete_endpoint_returns_conflict_for_non_revoked_invitation():
    mock_db = MagicMock(spec=Session)
    override_dependencies(mock_db, UserRole.ADMINISTRATOR.value)

    with patch(
        "app.api.routes.admin.delete_revoked_invitation",
        side_effect=InvitationNotDeletable,
    ):
        response = client.delete(f"/api/v1/admin/invitations/{uuid4()}")

    assert response.status_code == 409
    assert response.json()["detail"] == "Only revoked invitations can be deleted"


@pytest.mark.parametrize("role", [UserRole.CHW.value, UserRole.REVIEWER.value])
def test_non_administrator_cannot_revoke_invitation(role):
    mock_db = MagicMock(spec=Session)
    override_dependencies(mock_db, role)

    response = client.post(f"/api/v1/admin/invitations/{uuid4()}/revoke")

    assert response.status_code == 403


@pytest.mark.parametrize("lifecycle", ["revoked", "accepted", "expired"])
def test_non_pending_invitation_cannot_be_revoked(lifecycle):
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    admin = make_user(UserRole.ADMINISTRATOR.value)
    now = datetime.now(UTC)
    invitation = make_invitation(
        admin.id,
        expires_at=now - timedelta(hours=1)
        if lifecycle == "expired"
        else now + timedelta(hours=1),
        accepted_at=now if lifecycle == "accepted" else None,
        revoked_at=now if lifecycle == "revoked" else None,
    )

    with Session(engine) as db:
        db.add_all([admin, invitation])
        db.commit()

        with pytest.raises(InvitationNotRevocable):
            revoke_invitation(
                db,
                invitation_id=invitation.id,
                revoked_by=admin,
            )

        persisted = db.get(Invitation, invitation.id)

    assert persisted.revoked_at == invitation.revoked_at


def test_revoke_endpoint_returns_conflict_for_non_pending_invitation():
    mock_db = MagicMock(spec=Session)
    override_dependencies(mock_db, UserRole.ADMINISTRATOR.value)

    with patch(
        "app.api.routes.admin.revoke_invitation_service",
        side_effect=InvitationNotRevocable,
    ):
        response = client.post(f"/api/v1/admin/invitations/{uuid4()}/revoke")

    assert response.status_code == 409
    assert response.json()["detail"] == "Only pending invitations can be revoked"


def test_empty_invitation_results_are_handled():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        page = list_admin_invitations(db, page=1, page_size=20)
        missing = get_admin_invitation(db, uuid4())

    assert page.invitations == []
    assert page.total == 0
    assert missing is None
