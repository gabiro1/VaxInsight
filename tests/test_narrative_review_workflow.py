from uuid import UUID, uuid4

import pytest
from app.api.dependencies import get_current_user
from app.core.security import hash_password
from app.database.database import SessionLocal
from app.database.dependencies import get_db
from app.main import app
from app.models.auth import AuditEvent
from app.models.narrative import Narrative, NarrativeRevision
from app.models.review import (
    NarrativeAssignment,
    NarrativeReview,
    ReviewEvidenceReference,
)
from app.models.user import AccountStatus, User, UserRole
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

pytestmark = pytest.mark.integration


@pytest.fixture
def review_api_context():
    setup_db = SessionLocal()
    user_ids: list[UUID] = []

    def create_user(role: str) -> User:
        user_id = uuid4()
        user = User(
            id=user_id,
            email=f"review-test-{user_id}@example.com",
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
    admin = create_user(UserRole.ADMINISTRATOR.value)
    reviewer = create_user(UserRole.REVIEWER.value)
    other_reviewer = create_user(UserRole.REVIEWER.value)
    ineligible_user = create_user(UserRole.CHW.value)

    def override_get_db():
        request_db = SessionLocal()
        try:
            yield request_db
        finally:
            request_db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: owner
    client = TestClient(app)

    def act_as(user: User) -> None:
        app.dependency_overrides[get_current_user] = lambda: user

    try:
        yield client, act_as, owner, admin, reviewer, other_reviewer, ineligible_user
    finally:
        app.dependency_overrides.clear()
        setup_db.rollback()

        narrative_ids = list(
            setup_db.scalars(
                select(Narrative.id).where(Narrative.submitted_by_id.in_(user_ids))
            )
        )
        if narrative_ids:
            assignment_ids = list(
                setup_db.scalars(
                    select(NarrativeAssignment.id).where(
                        NarrativeAssignment.narrative_id.in_(narrative_ids)
                    )
                )
            )
            if assignment_ids:
                review_ids = list(
                    setup_db.scalars(
                        select(NarrativeReview.id).where(
                            NarrativeReview.assignment_id.in_(assignment_ids)
                        )
                    )
                )
                if review_ids:
                    setup_db.execute(
                        delete(ReviewEvidenceReference).where(
                            ReviewEvidenceReference.review_id.in_(review_ids)
                        )
                    )
                    setup_db.execute(
                        delete(NarrativeReview).where(
                            NarrativeReview.id.in_(review_ids)
                        )
                    )
                setup_db.execute(
                    delete(NarrativeAssignment).where(
                        NarrativeAssignment.id.in_(assignment_ids)
                    )
                )
            setup_db.execute(
                delete(NarrativeRevision).where(
                    NarrativeRevision.narrative_id.in_(narrative_ids)
                )
            )
            setup_db.execute(delete(Narrative).where(Narrative.id.in_(narrative_ids)))

        setup_db.execute(
            delete(AuditEvent).where(
                AuditEvent.actor_user_id.in_(user_ids)
                | AuditEvent.target_user_id.in_(user_ids)
            )
        )
        setup_db.execute(delete(User).where(User.id.in_(user_ids)))
        setup_db.commit()
        setup_db.close()


def _create_narrative(client: TestClient, act_as, owner: User) -> UUID:
    act_as(owner)
    response = client.post(
        "/api/v1/narratives",
        json={"content": "A submitted narrative for human review."},
    )
    assert response.status_code == 201
    return UUID(response.json()["id"])


def _assign(
    client: TestClient, act_as, admin: User, narrative_id: UUID, reviewer: User
):
    act_as(admin)
    response = client.post(
        f"/api/v1/narratives/{narrative_id}/assignment",
        json={"reviewer_id": str(reviewer.id)},
    )
    assert response.status_code == 201
    return response.json()


def test_assignment_scope_hides_content_from_managers_and_unassigned_reviewers(
    review_api_context,
):
    client, act_as, owner, admin, reviewer, other_reviewer, _ineligible_user = (
        review_api_context
    )
    narrative_id = _create_narrative(client, act_as, owner)
    assignment = _assign(client, act_as, admin, narrative_id, reviewer)
    assignment_id = assignment["id"]

    assert assignment["narrative"] is None
    assert assignment["review_status"] == "pending"

    act_as(reviewer)
    reviewer_list = client.get("/api/v1/reviews/assignments")
    assert reviewer_list.status_code == 200
    assert reviewer_list.json()["total"] == 1
    assert reviewer_list.json()["items"][0]["narrative"]["content"] == (
        "A submitted narrative for human review."
    )
    assert client.get(f"/api/v1/reviews/assignments/{assignment_id}").status_code == 200

    act_as(other_reviewer)
    assert client.get("/api/v1/reviews/assignments").json()["total"] == 0
    assert client.get(f"/api/v1/reviews/assignments/{assignment_id}").status_code == 404

    act_as(owner)
    assert client.get(f"/api/v1/reviews/assignments/{assignment_id}").status_code == 403
    assert (
        client.get(f"/api/v1/reviews/assignments/{assignment_id}/history").status_code
        == 403
    )

    act_as(admin)
    manager_detail = client.get(f"/api/v1/reviews/assignments/{assignment_id}")
    assert manager_detail.status_code == 200
    assert manager_detail.json()["narrative"] is None


def test_owner_cannot_edit_a_narrative_with_an_active_review_assignment(
    review_api_context,
):
    client, act_as, owner, admin, reviewer, _other_reviewer, _ineligible_user = (
        review_api_context
    )
    narrative_id = _create_narrative(client, act_as, owner)
    _assign(client, act_as, admin, narrative_id, reviewer)

    act_as(owner)
    detail = client.get(f"/api/v1/narratives/{narrative_id}")
    assert detail.status_code == 200
    assert detail.json()["review_status"] == "pending"
    assert "notes" not in detail.json()
    assert "evidence" not in detail.json()

    response = client.patch(
        f"/api/v1/narratives/{narrative_id}",
        json={"content": "This update must be rejected after assignment."},
    )

    assert response.status_code == 409
    assert client.get(f"/api/v1/narratives/{narrative_id}").json()["content"] == (
        "A submitted narrative for human review."
    )


def test_review_lifecycle_records_immutable_history_evidence_and_audit(
    review_api_context,
):
    client, act_as, owner, admin, reviewer, _other_reviewer, _ineligible_user = (
        review_api_context
    )
    narrative_id = _create_narrative(client, act_as, owner)
    assignment = _assign(client, act_as, admin, narrative_id, reviewer)
    assignment_id = assignment["id"]

    act_as(reviewer)
    in_review = client.post(
        f"/api/v1/reviews/assignments/{assignment_id}/status",
        json={"status": "in_review"},
    )
    assert in_review.status_code == 200
    assert in_review.json()["review_status"] == "in_review"

    review = client.post(
        f"/api/v1/reviews/assignments/{assignment_id}/review",
        json={
            "outcome": "evidence_supports_claim",
            "notes": "Internal reviewer note.",
            "evidence": [
                {
                    "source_title": "Approved source",
                    "publisher": "Public Health Authority",
                    "url": "https://example.org/source",
                    "publication_date": "2026-01-01",
                    "accessed_at": "2026-11-09T12:00:00Z",
                    "relevance": "The source addresses the submitted claim.",
                }
            ],
        },
    )
    assert review.status_code == 201
    assert review.json()["outcome"] == "evidence_supports_claim"
    assert review.json()["evidence"][0]["publisher"] == "Public Health Authority"

    status_response = client.get(f"/api/v1/reviews/assignments/{assignment_id}/status")
    assert status_response.status_code == 200
    assert status_response.json()["review_status"] == "reviewed"

    history = client.get(f"/api/v1/reviews/assignments/{assignment_id}/history")
    assert history.status_code == 200
    assert history.json()["total"] == 1
    assert history.json()["items"][0]["notes"] == "Internal reviewer note."

    assert (
        client.post(
            f"/api/v1/reviews/assignments/{assignment_id}/review",
            json={"outcome": "insufficient_evidence"},
        ).status_code
        == 409
    )

    act_as(owner)
    assert (
        client.get(f"/api/v1/reviews/assignments/{assignment_id}/history").status_code
        == 403
    )

    act_as(admin)
    manager_history = client.get(f"/api/v1/reviews/assignments/{assignment_id}/history")
    assert manager_history.status_code == 200
    assert manager_history.json()["items"][0]["notes"] == "Internal reviewer note."

    db = SessionLocal()
    try:
        actions = list(
            db.scalars(
                select(AuditEvent.action).where(
                    AuditEvent.actor_user_id == reviewer.id,
                    AuditEvent.action.in_(
                        (
                            "narrative_review_status_changed",
                            "narrative_review_submitted",
                        )
                    ),
                )
            )
        )
    finally:
        db.close()
    assert actions.count("narrative_review_status_changed") == 1
    assert actions.count("narrative_review_submitted") == 1


def test_reassignment_and_revocation_preserve_history_and_remove_reviewer_access(
    review_api_context,
):
    client, act_as, owner, admin, reviewer, other_reviewer, _ineligible_user = (
        review_api_context
    )
    narrative_id = _create_narrative(client, act_as, owner)
    initial_assignment = _assign(client, act_as, admin, narrative_id, reviewer)
    initial_id = initial_assignment["id"]

    act_as(reviewer)
    assert (
        client.post(
            f"/api/v1/reviews/assignments/{initial_id}/status",
            json={"status": "in_review"},
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/api/v1/reviews/assignments/{initial_id}/review",
            json={
                "outcome": "needs_further_review",
                "notes": "Prior reviewer history is retained.",
            },
        ).status_code
        == 201
    )

    act_as(admin)
    reassigned = client.post(
        f"/api/v1/narratives/{narrative_id}/assignment/reassign",
        json={
            "reviewer_id": str(other_reviewer.id),
            "reason": "Workload balancing requires a different reviewer.",
        },
    )
    assert reassigned.status_code == 200
    replacement_id = reassigned.json()["id"]
    assert replacement_id != initial_id
    assert reassigned.json()["review_status"] == "pending"

    old_assignment = client.get(f"/api/v1/reviews/assignments/{initial_id}")
    assert old_assignment.status_code == 200
    assert old_assignment.json()["status"] == "revoked"
    assert old_assignment.json()["narrative"] is None
    assert old_assignment.json()["revoked_reason"] == (
        "Workload balancing requires a different reviewer."
    )

    act_as(reviewer)
    assert client.get(f"/api/v1/reviews/assignments/{initial_id}").status_code == 404
    assert client.get("/api/v1/reviews/assignments").json()["total"] == 0

    act_as(other_reviewer)
    assert (
        client.get(f"/api/v1/reviews/assignments/{replacement_id}").status_code == 200
    )
    replacement_history = client.get(
        f"/api/v1/reviews/assignments/{replacement_id}/history"
    )
    assert replacement_history.status_code == 200
    assert replacement_history.json()["total"] == 1
    assert replacement_history.json()["items"][0]["notes"] == (
        "Prior reviewer history is retained."
    )

    act_as(admin)
    revoked = client.post(
        f"/api/v1/narratives/{narrative_id}/assignment/revoke",
        json={"reason": "Review is paused pending supervisor direction."},
    )
    assert revoked.status_code == 200
    assert revoked.json()["status"] == "revoked"

    act_as(other_reviewer)
    assert client.get("/api/v1/reviews/assignments").json()["total"] == 0

    db = SessionLocal()
    try:
        actions = list(
            db.scalars(
                select(AuditEvent.action).where(
                    AuditEvent.actor_user_id == admin.id,
                    AuditEvent.action.in_(
                        (
                            "narrative_assignment_created",
                            "narrative_assignment_changed",
                            "narrative_assignment_revoked",
                        )
                    ),
                )
            )
        )
    finally:
        db.close()
    assert actions.count("narrative_assignment_created") == 1
    assert actions.count("narrative_assignment_changed") == 1
    assert actions.count("narrative_assignment_revoked") == 1


def test_assignment_authorization_eligibility_and_duplicate_rules(review_api_context):
    client, act_as, owner, admin, reviewer, _other_reviewer, ineligible_user = (
        review_api_context
    )
    narrative_id = _create_narrative(client, act_as, owner)

    act_as(admin)
    ineligible = client.post(
        f"/api/v1/narratives/{narrative_id}/assignment",
        json={"reviewer_id": str(ineligible_user.id)},
    )
    assert ineligible.status_code == 422

    act_as(reviewer)
    assert (
        client.post(
            f"/api/v1/narratives/{narrative_id}/assignment",
            json={"reviewer_id": str(reviewer.id)},
        ).status_code
        == 403
    )

    _assign(client, act_as, admin, narrative_id, reviewer)
    duplicate = client.post(
        f"/api/v1/narratives/{narrative_id}/assignment",
        json={"reviewer_id": str(reviewer.id)},
    )
    assert duplicate.status_code == 409

    missing_revoke_reason = client.post(
        f"/api/v1/narratives/{narrative_id}/assignment/revoke",
        json={},
    )
    assert missing_revoke_reason.status_code == 422


def test_escalation_is_explicit_and_has_no_automatic_resolution(review_api_context):
    client, act_as, owner, admin, reviewer, _other_reviewer, _ineligible_user = (
        review_api_context
    )
    narrative_id = _create_narrative(client, act_as, owner)
    assignment = _assign(client, act_as, admin, narrative_id, reviewer)
    assignment_id = assignment["id"]

    act_as(reviewer)
    missing_reason = client.post(
        f"/api/v1/reviews/assignments/{assignment_id}/status",
        json={"status": "requires_escalation"},
    )
    assert missing_reason.status_code == 422

    escalated = client.post(
        f"/api/v1/reviews/assignments/{assignment_id}/status",
        json={
            "status": "requires_escalation",
            "reason": "The source set needs authorized human review.",
        },
    )
    assert escalated.status_code == 200
    assert escalated.json()["review_status"] == "requires_escalation"

    cannot_auto_resolve = client.post(
        f"/api/v1/reviews/assignments/{assignment_id}/status",
        json={"status": "in_review"},
    )
    assert cannot_auto_resolve.status_code == 409

    cannot_submit = client.post(
        f"/api/v1/reviews/assignments/{assignment_id}/review",
        json={"outcome": "needs_further_review"},
    )
    assert cannot_submit.status_code == 409

    db = SessionLocal()
    try:
        escalation = db.scalar(
            select(AuditEvent).where(
                AuditEvent.actor_user_id == reviewer.id,
                AuditEvent.action == "narrative_review_escalated",
            )
        )
    finally:
        db.close()
    assert escalation is not None
