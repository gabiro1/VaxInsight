import threading
from unittest.mock import patch
from uuid import UUID, uuid4

import pytest
from app.api.dependencies import get_current_user
from app.core.config import settings
from app.core.security import hash_password
from app.core.tokens import create_access_token
from app.database.database import SessionLocal
from app.database.dependencies import get_db
from app.main import app
from app.models.auth import AuditEvent, RateLimitBucket
from app.models.narrative import (
    Narrative,
    NarrativeRevision,
    NarrativeRevisionAction,
)
from app.models.user import AccountStatus, User, UserRole
from app.services import narratives as narrative_service
from app.services.narratives import NarrativePersistenceError
from fastapi.testclient import TestClient
from sqlalchemy import delete, or_, select, text, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

pytestmark = pytest.mark.integration


@pytest.fixture
def narrative_api_context():
    setup_db = SessionLocal()
    user_ids: list = []

    def create_user(role: str) -> User:
        user_id = uuid4()
        user = User(
            id=user_id,
            email=f"narrative-test-{user_id}@example.com",
            hashed_password=hash_password("StrongPassword123!"),
            is_active=True,
            status=AccountStatus.ACTIVE.value,
            role=role,
        )
        setup_db.add(user)
        setup_db.commit()
        setup_db.refresh(user)
        user_ids.append(user_id)
        return user

    owner = create_user(UserRole.CHW.value)
    other_user = create_user(UserRole.REVIEWER.value)

    def override_get_db():
        request_db = SessionLocal()
        try:
            yield request_db
        finally:
            request_db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: owner
    client = TestClient(app)

    try:
        yield client, owner, other_user
    finally:
        app.dependency_overrides.clear()
        setup_db.rollback()

        narrative_ids = list(
            setup_db.scalars(
                select(Narrative.id).where(Narrative.submitted_by_id.in_(user_ids))
            )
        )
        if narrative_ids:
            setup_db.execute(
                delete(NarrativeRevision).where(
                    NarrativeRevision.narrative_id.in_(narrative_ids)
                )
            )
            setup_db.execute(delete(Narrative).where(Narrative.id.in_(narrative_ids)))

        setup_db.execute(
            delete(AuditEvent).where(
                or_(
                    AuditEvent.actor_user_id.in_(user_ids),
                    AuditEvent.target_user_id.in_(user_ids),
                )
            )
        )
        setup_db.execute(
            delete(RateLimitBucket).where(
                RateLimitBucket.bucket_key.like("auth:narrative_write:%")
            )
        )
        setup_db.execute(delete(User).where(User.id.in_(user_ids)))
        setup_db.commit()
        setup_db.close()


def test_owner_can_create_update_and_view_narrative_history(narrative_api_context):
    client, owner, _other_user = narrative_api_context

    create_response = client.post(
        "/api/v1/narratives",
        json={"content": "A community member asked about vaccine safety."},
    )

    assert create_response.status_code == 201
    created = create_response.json()
    narrative_id = created["id"]
    assert created["submitted_by_id"] == str(owner.id)
    assert created["status"] == "submitted"
    assert created["version"] == 1

    detail_response = client.get(f"/api/v1/narratives/{narrative_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["content"] == (
        "A community member asked about vaccine safety."
    )

    update_response = client.patch(
        f"/api/v1/narratives/{narrative_id}",
        json={"content": "The community member asked for vaccine safety information."},
    )

    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["version"] == 2
    assert updated["status"] == "submitted"

    history_response = client.get(f"/api/v1/narratives/{narrative_id}/history")

    assert history_response.status_code == 200
    history = history_response.json()
    assert history["total"] == 2
    assert [item["version"] for item in history["items"]] == [1, 2]
    assert [item["action"] for item in history["items"]] == ["created", "updated"]
    assert history["items"][0]["content"] == (
        "A community member asked about vaccine safety."
    )


def test_owner_list_supports_pagination_and_filters(narrative_api_context):
    client, _owner, _other_user = narrative_api_context

    for index in range(3):
        response = client.post(
            "/api/v1/narratives",
            json={"content": f"Narrative record {index}"},
        )
        assert response.status_code == 201

    response = client.get(
        "/api/v1/narratives",
        params={"page": 2, "page_size": 2, "status": "submitted"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["page"] == 2
    assert body["page_size"] == 2
    assert body["total"] == 3
    assert body["total_pages"] == 2
    assert len(body["items"]) == 1


def test_cross_user_and_administrator_access_is_not_granted_implicitly(
    narrative_api_context,
):
    client, owner, other_user = narrative_api_context
    create_response = client.post(
        "/api/v1/narratives",
        json={"content": "Owner-only narrative content."},
    )
    narrative_id = create_response.json()["id"]

    app.dependency_overrides[get_current_user] = lambda: other_user

    assert client.get(f"/api/v1/narratives/{narrative_id}").status_code == 404
    assert client.get(f"/api/v1/narratives/{narrative_id}/history").status_code == 404
    assert (
        client.patch(
            f"/api/v1/narratives/{narrative_id}",
            json={"content": "Unauthorized update."},
        ).status_code
        == 404
    )
    assert client.get("/api/v1/narratives").json()["total"] == 0

    unassigned_chw = User(
        id=uuid4(),
        email=f"narrative-unassigned-chw-{uuid4()}@example.com",
        hashed_password=hash_password("StrongPassword123!"),
        is_active=True,
        status=AccountStatus.ACTIVE.value,
        role=UserRole.CHW.value,
    )
    app.dependency_overrides[get_current_user] = lambda: unassigned_chw
    assert client.get(f"/api/v1/narratives/{narrative_id}").status_code == 404

    administrator = User(
        id=uuid4(),
        email=f"narrative-admin-{uuid4()}@example.com",
        hashed_password=hash_password("StrongPassword123!"),
        is_active=True,
        status=AccountStatus.ACTIVE.value,
        role=UserRole.ADMINISTRATOR.value,
    )
    admin_db = SessionLocal()
    try:
        admin_db.add(administrator)
        admin_db.commit()
        admin_db.refresh(administrator)
        app.dependency_overrides[get_current_user] = lambda: administrator
        assert client.get(f"/api/v1/narratives/{narrative_id}").status_code == 404
    finally:
        app.dependency_overrides[get_current_user] = lambda: owner
        admin_db.execute(
            delete(AuditEvent).where(
                or_(
                    AuditEvent.actor_user_id == administrator.id,
                    AuditEvent.target_user_id == administrator.id,
                )
            )
        )
        admin_db.execute(delete(User).where(User.id == administrator.id))
        admin_db.commit()
        admin_db.close()


def test_invalid_content_and_lifecycle_fields_are_rejected(narrative_api_context):
    client, _owner, _other_user = narrative_api_context

    assert client.post("/api/v1/narratives", json={"content": "   "}).status_code == 422
    assert (
        client.post(
            "/api/v1/narratives",
            json={"content": "valid", "prediction": "false"},
        ).status_code
        == 422
    )

    create_response = client.post(
        "/api/v1/narratives",
        json={"content": "Lifecycle fields are server controlled."},
    )
    narrative_id = create_response.json()["id"]

    assert (
        client.patch(
            f"/api/v1/narratives/{narrative_id}",
            json={"content": "Updated", "status": "reviewed"},
        ).status_code
        == 422
    )
    assert (
        client.get(
            "/api/v1/narratives",
            params={
                "submitted_after": "2026-11-06T00:00:00Z",
                "submitted_before": "2026-11-05T00:00:00Z",
            },
        ).status_code
        == 422
    )


def test_unauthenticated_narrative_request_is_rejected(narrative_api_context):
    client, _owner, _other_user = narrative_api_context
    app.dependency_overrides.pop(get_current_user)

    response = client.get("/api/v1/narratives")

    assert response.status_code == 401


def test_user_without_narrative_permission_is_rejected(narrative_api_context):
    client, _owner, _other_user = narrative_api_context
    unassigned_user = User(
        id=uuid4(),
        email=f"narrative-no-role-{uuid4()}@example.com",
        hashed_password=hash_password("StrongPassword123!"),
        is_active=True,
        status=AccountStatus.ACTIVE.value,
        role=None,
    )
    app.dependency_overrides[get_current_user] = lambda: unassigned_user

    assert client.get("/api/v1/narratives").status_code == 403
    assert (
        client.post(
            "/api/v1/narratives",
            json={"content": "This request lacks the create permission."},
        ).status_code
        == 403
    )


def test_narrative_audit_events_are_recorded(narrative_api_context):
    client, owner, _other_user = narrative_api_context
    create_response = client.post(
        "/api/v1/narratives",
        json={"content": "An auditable narrative record."},
    )
    narrative_id = create_response.json()["id"]
    client.patch(
        f"/api/v1/narratives/{narrative_id}",
        json={"content": "An updated auditable narrative record."},
    )

    db = SessionLocal()
    try:
        actions = list(
            db.scalars(
                select(AuditEvent.action).where(
                    AuditEvent.actor_user_id == owner.id,
                    AuditEvent.action.in_(("narrative_created", "narrative_updated")),
                )
            )
        )
    finally:
        db.close()

    assert actions.count("narrative_created") == 1
    assert actions.count("narrative_updated") == 1


def test_narrative_revision_versions_are_unique_in_postgresql(narrative_api_context):
    client, owner, _other_user = narrative_api_context
    response = client.post(
        "/api/v1/narratives",
        json={"content": "A revision constraint test record."},
    )
    narrative_id = UUID(response.json()["id"])

    db = SessionLocal()
    try:
        db.add(
            NarrativeRevision(
                narrative_id=narrative_id,
                changed_by_user_id=owner.id,
                version=1,
                action=NarrativeRevisionAction.UPDATED.value,
                content="Duplicate version must fail.",
            )
        )
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()
    finally:
        db.close()


def test_concurrent_updates_are_serialized_and_history_remains_sequential(
    narrative_api_context,
    monkeypatch,
):
    client, owner, _other_user = narrative_api_context
    create_response = client.post(
        "/api/v1/narratives",
        json={"content": "Initial concurrent narrative content."},
    )
    narrative_id = UUID(create_response.json()["id"])

    ready = threading.Barrier(2)
    first_update_entered = threading.Event()
    lock_wait_observed = threading.Event()
    release_first_update = threading.Event()
    stop_monitor = threading.Event()
    holder_claimed = threading.Lock()
    first_holder = False
    results: list[Exception | None] = []
    original_add_audit_event = narrative_service.add_audit_event

    def hold_first_update(db, **kwargs):
        nonlocal first_holder
        if kwargs.get("action") == "narrative_updated":
            with holder_claimed:
                should_hold = not first_holder
                first_holder = True
            if should_hold:
                first_update_entered.set()
                if not release_first_update.wait(timeout=30):
                    raise RuntimeError("Timed out releasing the first narrative update")
        original_add_audit_event(db, **kwargs)

    monkeypatch.setattr(
        narrative_service,
        "add_audit_event",
        hold_first_update,
    )

    def monitor_row_lock_wait() -> None:
        db = SessionLocal()
        try:
            while not stop_monitor.is_set():
                waiting_count = db.scalar(
                    text(
                        """
                        SELECT count(*)
                        FROM pg_stat_activity
                        WHERE wait_event_type = 'Lock'
                          AND query ILIKE '%FOR UPDATE%'
                          AND query ILIKE '%narratives%'
                        """
                    )
                )
                db.rollback()
                if waiting_count:
                    lock_wait_observed.set()
                    return
                stop_monitor.wait(0.01)
        finally:
            db.close()

    def worker(content: str) -> None:
        db = SessionLocal()
        try:
            actor = db.get(User, owner.id)
            ready.wait(timeout=30)
            narrative_service.update_owned_narrative(
                db,
                actor=actor,
                narrative_id=narrative_id,
                content=content,
            )
            results.append(None)
        except Exception as error:  # noqa: BLE001 - report worker failures
            db.rollback()
            results.append(error)
        finally:
            db.close()

    monitor_thread = threading.Thread(target=monitor_row_lock_wait)
    workers = [
        threading.Thread(
            target=worker,
            args=(f"Concurrent update {index}.",),
        )
        for index in (1, 2)
    ]
    monitor_thread.start()
    for thread in workers:
        thread.start()

    assert first_update_entered.wait(timeout=30)
    assert lock_wait_observed.wait(timeout=30)
    release_first_update.set()

    for thread in workers:
        thread.join(timeout=30)
    stop_monitor.set()
    monitor_thread.join(timeout=30)

    assert all(not thread.is_alive() for thread in workers)
    assert not monitor_thread.is_alive()
    assert results == [None, None]

    db = SessionLocal()
    try:
        narrative = db.get(Narrative, narrative_id)
        revisions = list(
            db.scalars(
                select(NarrativeRevision)
                .where(NarrativeRevision.narrative_id == narrative_id)
                .order_by(NarrativeRevision.version.asc())
            )
        )
        audit_events = list(
            db.scalars(
                select(AuditEvent).where(
                    AuditEvent.actor_user_id == owner.id,
                    AuditEvent.action == "narrative_updated",
                )
            )
        )
    finally:
        db.close()

    assert narrative.version == 3
    assert [revision.version for revision in revisions] == [1, 2, 3]
    assert [revision.action for revision in revisions] == [
        "created",
        "updated",
        "updated",
    ]
    assert {revision.content for revision in revisions[1:]} == {
        "Concurrent update 1.",
        "Concurrent update 2.",
    }
    assert len(audit_events) == 2
    assert all(event.details is None for event in audit_events)


def test_failed_update_rolls_back_narrative_revision_and_audit(
    narrative_api_context,
    monkeypatch,
):
    client, owner, _other_user = narrative_api_context
    create_response = client.post(
        "/api/v1/narratives",
        json={"content": "Content that must survive a failed update."},
    )
    narrative_id = UUID(create_response.json()["id"])

    db = SessionLocal()
    original_commit = Session.commit

    def fail_commit(_session):
        raise IntegrityError("forced narrative commit failure", {}, Exception("forced"))

    monkeypatch.setattr(Session, "commit", fail_commit)
    try:
        actor = db.get(User, owner.id)
        with pytest.raises(NarrativePersistenceError):
            narrative_service.update_owned_narrative(
                db,
                actor=actor,
                narrative_id=narrative_id,
                content="This update must roll back.",
            )
    finally:
        monkeypatch.setattr(Session, "commit", original_commit)
        db.close()

    verify_db = SessionLocal()
    try:
        narrative = verify_db.get(Narrative, narrative_id)
        revisions = list(
            verify_db.scalars(
                select(NarrativeRevision)
                .where(NarrativeRevision.narrative_id == narrative_id)
                .order_by(NarrativeRevision.version.asc())
            )
        )
        audit_events = list(
            verify_db.scalars(
                select(AuditEvent).where(
                    AuditEvent.actor_user_id == owner.id,
                    AuditEvent.action == "narrative_updated",
                )
            )
        )
    finally:
        verify_db.close()

    assert narrative.content == "Content that must survive a failed update."
    assert narrative.version == 1
    assert [revision.version for revision in revisions] == [1]
    assert audit_events == []


def test_narrative_storage_failure_returns_safe_service_unavailable(
    narrative_api_context,
):
    client, _owner, _other_user = narrative_api_context

    with patch(
        "app.api.routes.narratives.update_owned_narrative",
        side_effect=NarrativePersistenceError,
    ):
        response = client.patch(
            f"/api/v1/narratives/{uuid4()}",
            json={"content": "Storage failure response."},
        )

    assert response.status_code == 503
    assert response.json() == {"detail": "Narrative storage is temporarily unavailable"}
    assert "forced" not in response.text
    assert "sql" not in response.text.lower()


def test_narrative_writes_use_existing_rate_limit_infrastructure(
    narrative_api_context,
    monkeypatch,
):
    client, _owner, _other_user = narrative_api_context
    monkeypatch.setattr(settings, "NARRATIVE_RATE_LIMIT", 2)

    first_response = client.post(
        "/api/v1/narratives",
        json={"content": "The first write is allowed."},
    )
    narrative_id = first_response.json()["id"]
    second_response = client.patch(
        f"/api/v1/narratives/{narrative_id}",
        json={"content": "The second write is allowed."},
    )
    third_response = client.patch(
        f"/api/v1/narratives/{narrative_id}",
        json={"content": "The third write is rate limited."},
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 200
    assert third_response.status_code == 429
    assert int(third_response.headers["Retry-After"]) >= 1


def test_inactive_account_cannot_access_narratives(narrative_api_context):
    client, owner, _other_user = narrative_api_context
    db = SessionLocal()
    try:
        db.execute(
            update(User)
            .where(User.id == owner.id)
            .values(status=AccountStatus.SUSPENDED.value, is_active=False)
        )
        db.commit()
    finally:
        db.close()

    app.dependency_overrides.pop(get_current_user)
    token = create_access_token(subject=str(owner.id))
    response = client.get(
        "/api/v1/narratives",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401


@pytest.mark.parametrize(
    "params",
    [
        {"page": "0"},
        {"page_size": "101"},
        {"status": "reviewed"},
    ],
)
def test_invalid_narrative_filters_are_rejected(narrative_api_context, params):
    client, _owner, _other_user = narrative_api_context

    response = client.get("/api/v1/narratives", params=params)

    assert response.status_code == 422


def test_narrative_validation_rejects_large_and_control_content(narrative_api_context):
    client, _owner, _other_user = narrative_api_context

    too_large = client.post(
        "/api/v1/narratives",
        json={"content": "x" * 10_001},
    )
    control_character = client.post(
        "/api/v1/narratives",
        json={"content": "Narrative with a null\x00 character."},
    )
    malformed_id = client.get("/api/v1/narratives/not-a-uuid")

    assert too_large.status_code == 422
    assert control_character.status_code == 422
    assert malformed_id.status_code == 422


def test_revision_history_is_read_only_through_narrative_api(narrative_api_context):
    client, _owner, _other_user = narrative_api_context
    create_response = client.post(
        "/api/v1/narratives",
        json={"content": "History is immutable through the API."},
    )
    narrative_id = create_response.json()["id"]

    response = client.patch(
        f"/api/v1/narratives/{narrative_id}/history",
        json={"content": "Tampered history"},
    )

    assert response.status_code == 405


def test_database_constraints_reject_invalid_narrative_content(narrative_api_context):
    _client, owner, _other_user = narrative_api_context
    db = SessionLocal()
    try:
        db.add(
            Narrative(
                submitted_by_id=owner.id,
                content="   ",
                status="submitted",
                version=1,
            )
        )
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()
    finally:
        db.close()
