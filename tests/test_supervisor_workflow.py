from uuid import UUID, uuid4

import pytest
from app.api.dependencies import get_current_user
from app.core.config import settings
from app.core.permissions import (
    FUTURE_PERMISSIONS,
    IMPLEMENTED_PERMISSIONS,
    ROLE_PERMISSIONS,
    Permission,
)
from app.core.security import hash_password
from app.database.database import SessionLocal
from app.database.dependencies import get_db
from app.main import app
from app.models.auth import AuditEvent
from app.models.questions import (
    ProfessionalResponse,
    QuestionAnalysis,
    VaccineQuestion,
)
from app.models.user import AccountStatus, User, UserRole
from app.models.vaccine_content import VaccineContent, VaccineSource
from app.services.auth import delete_account
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

pytestmark = pytest.mark.integration


@pytest.fixture
def supervisor_api_context():
    setup_db = SessionLocal()
    user_ids: list[UUID] = []

    def create_user(role: str) -> User:
        user_id = uuid4()
        user = User(
            id=user_id,
            email=f"supervisor-test-{user_id}@example.com",
            full_name="Supervisor Test User"
            if role == UserRole.COMMUNITY_MEMBER.value
            else None,
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

    owner = create_user(UserRole.COMMUNITY_MEMBER.value)
    other_owner = create_user(UserRole.CHW.value)
    reviewer = create_user(UserRole.REVIEWER.value)
    administrator = create_user(UserRole.ADMINISTRATOR.value)

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
        yield client, act_as, owner, other_owner, reviewer, administrator
    finally:
        app.dependency_overrides.clear()
        setup_db.rollback()

        question_ids = list(
            setup_db.scalars(
                select(VaccineQuestion.id).where(
                    VaccineQuestion.asked_by_user_id.in_(user_ids)
                )
            )
        )
        if question_ids:
            setup_db.execute(
                delete(ProfessionalResponse).where(
                    ProfessionalResponse.question_id.in_(question_ids)
                )
            )
            setup_db.execute(
                delete(QuestionAnalysis).where(
                    QuestionAnalysis.question_id.in_(question_ids)
                )
            )
            setup_db.execute(
                delete(VaccineQuestion).where(VaccineQuestion.id.in_(question_ids))
            )

        content_ids = list(
            setup_db.scalars(
                select(VaccineContent.id).where(
                    VaccineContent.created_by_user_id.in_(user_ids)
                )
            )
        )
        if content_ids:
            source_ids = list(
                setup_db.scalars(
                    select(VaccineContent.source_id).where(
                        VaccineContent.id.in_(content_ids)
                    )
                )
            )
            setup_db.execute(
                delete(VaccineContent).where(VaccineContent.id.in_(content_ids))
            )
            setup_db.execute(
                delete(VaccineSource).where(VaccineSource.id.in_(source_ids))
            )

        setup_db.execute(
            delete(AuditEvent).where(
                AuditEvent.actor_user_id.in_(user_ids)
                | AuditEvent.target_user_id.in_(user_ids)
            )
        )
        setup_db.execute(delete(User).where(User.id.in_(user_ids)))
        setup_db.commit()
        setup_db.close()


def test_supervisor_permissions_are_implemented_without_promoting_reserved_analysis(
):
    expected = {
        Permission.VACCINE_CONTENT_READ.value,
        Permission.VACCINE_CONTENT_MANAGE.value,
        Permission.QUESTION_CREATE.value,
        Permission.QUESTION_READ_OWN.value,
        Permission.QUESTION_REVIEW.value,
        Permission.VACCINE_ANALYSIS_REQUEST.value,
        Permission.VACCINE_ANALYSIS_READ.value,
    }
    assert expected <= IMPLEMENTED_PERMISSIONS
    assert Permission.ANALYSIS_REQUEST.value in FUTURE_PERMISSIONS
    assert Permission.ANALYSIS_READ.value in FUTURE_PERMISSIONS
    assert Permission.VACCINE_CONTENT_READ.value in ROLE_PERMISSIONS[
        UserRole.COMMUNITY_MEMBER.value
    ]
    assert Permission.VACCINE_CONTENT_READ.value in ROLE_PERMISSIONS[
        UserRole.CHW.value
    ]
    assert Permission.VACCINE_CONTENT_READ.value in ROLE_PERMISSIONS[
        UserRole.REVIEWER.value
    ]
    assert Permission.VACCINE_CONTENT_READ.value in ROLE_PERMISSIONS[
        UserRole.ADMINISTRATOR.value
    ]
    assert Permission.VACCINE_CONTENT_MANAGE.value in ROLE_PERMISSIONS[
        UserRole.ADMINISTRATOR.value
    ]
    assert Permission.QUESTION_REVIEW.value in ROLE_PERMISSIONS[
        UserRole.REVIEWER.value
    ]
    assert Permission.QUESTION_REVIEW.value not in ROLE_PERMISSIONS[
        UserRole.CHW.value
    ]
    assert ROLE_PERMISSIONS[UserRole.CHW.value] == {
        Permission.VACCINE_CONTENT_READ.value,
        Permission.NARRATIVE_CREATE.value,
        Permission.NARRATIVE_READ_OWN.value,
        Permission.NARRATIVE_UPDATE_OWN.value,
        Permission.QUESTION_CREATE.value,
        Permission.QUESTION_READ_OWN.value,
        Permission.VACCINE_ANALYSIS_REQUEST.value,
        Permission.VACCINE_ANALYSIS_READ.value,
    }


def test_published_content_is_readable_by_role_and_drafts_are_hidden(
    supervisor_api_context,
):
    client, act_as, owner, other_owner, _reviewer, administrator = (
        supervisor_api_context
    )
    source = {
        "authority": "Approved Authority",
        "name": "Official vaccine source",
        "url": "https://authority.example/source",
        "jurisdiction": "global",
    }

    act_as(administrator)
    draft = client.post(
        "/api/v1/admin/vaccine-content",
        json={
            "source": source,
            "language": "en",
            "category": "general",
            "title": "Draft title",
            "summary": "Draft summary",
            "body": "Draft body",
            "version": 1,
            "status": "draft",
        },
    )
    assert draft.status_code == 201
    assert draft.json()["status"] == "draft"

    published = client.post(
        "/api/v1/admin/vaccine-content",
        json={
            "source": source,
            "language": "en",
            "category": "general",
            "title": "Published title",
            "summary": "Published summary",
            "body": "Published body",
            "version": 2,
            "status": "published",
        },
    )
    assert published.status_code == 201
    published_body = published.json()
    assert published_body["approved_by_user_id"] == str(administrator.id)
    assert published_body["approved_at"] is not None
    assert published_body["source"]["id"] == draft.json()["source"]["id"]

    act_as(owner)
    filtered = client.get(
        "/api/v1/vaccine-content",
        params={"language": "en", "category": "general"},
    )
    assert filtered.status_code == 200
    assert [item["title"] for item in filtered.json()] == ["Published title"]
    assert (
        client.get(f"/api/v1/vaccine-content/{draft.json()['id']}").status_code == 404
    )

    act_as(other_owner)
    assert (
        client.get(
            "/api/v1/vaccine-content",
            params={"language": "en", "category": "general"},
        ).json()[0]["title"]
        == "Published title"
    )
    assert (
        client.post(
            "/api/v1/admin/vaccine-content",
            json={
                "source": source,
                "language": "en",
                "category": "general",
                "title": "CHW must not publish",
                "summary": "No",
                "body": "No",
                "version": 3,
                "status": "draft",
            },
        ).status_code
        == 403
    )


def test_question_owner_isolation_and_unavailable_analysis(supervisor_api_context):
    client, act_as, owner, other_owner, _reviewer, _administrator = (
        supervisor_api_context
    )
    act_as(owner)
    created = client.post(
        "/api/v1/questions",
        json={
            "content": "What should I know before a vaccine visit?",
            "language": "en",
            "topic": "visit",
        },
    )
    assert created.status_code == 201
    payload = created.json()
    question_id = UUID(payload["question"]["id"])
    assert payload["question"]["status"] == "awaiting_review"
    assert payload["latest_analysis"]["status"] == "unavailable"
    assert payload["latest_analysis"]["answer"] is None
    assert "Phase 1 model/dataset" in payload["latest_analysis"]["limitations"]

    assert len(client.get("/api/v1/questions").json()) == 1
    assert client.get(f"/api/v1/questions/{question_id}").status_code == 200

    act_as(other_owner)
    assert client.get("/api/v1/questions").json() == []
    assert client.get(f"/api/v1/questions/{question_id}").status_code == 404
    assert client.post(f"/api/v1/questions/{question_id}/analysis").status_code == 404

    chw_created = client.post(
        "/api/v1/questions",
        json={
            "content": "A CHW question should remain owner-scoped.",
            "language": "rw",
        },
    )
    assert chw_created.status_code == 201
    chw_question_id = chw_created.json()["question"]["id"]
    assert client.get("/api/v1/questions").json()[0]["id"] == chw_question_id


def test_chw_cannot_access_question_review_queue(supervisor_api_context):
    client, act_as, _owner, other_owner, _reviewer, _administrator = (
        supervisor_api_context
    )
    act_as(other_owner)

    assert client.get("/api/v1/review/questions").status_code == 403


def test_question_writes_use_rate_limit_infrastructure(
    supervisor_api_context,
    monkeypatch,
):
    client, act_as, owner, _other_owner, _reviewer, _administrator = (
        supervisor_api_context
    )
    act_as(owner)
    monkeypatch.setattr(settings, "QUESTION_RATE_LIMIT", 1)

    first = client.post(
        "/api/v1/questions",
        json={"content": "The first question is allowed.", "language": "en"},
    )
    second = client.post(
        "/api/v1/questions",
        json={"content": "The second question is rate limited.", "language": "en"},
    )

    assert first.status_code == 201
    assert second.status_code == 429


def test_reviewer_response_is_public_and_supersedes_prior_response(
    supervisor_api_context,
):
    client, act_as, owner, _other_owner, reviewer, _administrator = (
        supervisor_api_context
    )
    act_as(owner)
    created = client.post(
        "/api/v1/questions",
        json={"content": "Can a reviewer answer this?", "language": "rw"},
    )
    question_id = UUID(created.json()["question"]["id"])

    act_as(reviewer)
    queue = client.get("/api/v1/review/questions")
    assert queue.status_code == 200
    assert queue.json()[0]["question"]["id"] == str(question_id)
    assert client.get(f"/api/v1/questions/{question_id}").status_code == 404

    first = client.post(
        f"/api/v1/review/questions/{question_id}/response",
        json={"response": "First professional answer."},
    )
    second = client.post(
        f"/api/v1/review/questions/{question_id}/response",
        json={"response": "Updated professional answer."},
    )
    assert first.status_code == 201
    assert second.status_code == 201
    assert second.json()["status"] == "published"

    db = SessionLocal()
    try:
        responses = list(
            db.scalars(
                select(ProfessionalResponse)
                .where(ProfessionalResponse.question_id == question_id)
                .order_by(ProfessionalResponse.created_at.asc())
            )
        )
        question = db.get(VaccineQuestion, question_id)
    finally:
        db.close()
    assert len(responses) == 2
    assert [item.status for item in responses] == ["superseded", "published"]
    assert question.status == "responded"

    act_as(owner)
    detail = client.get(f"/api/v1/questions/{question_id}")
    assert detail.status_code == 200
    assert detail.json()["latest_professional_response"]["response"] == (
        "Updated professional answer."
    )


def test_hard_delete_removes_owned_questions_and_analysis_runs(supervisor_api_context):
    client, act_as, owner, _other_owner, reviewer, _administrator = (
        supervisor_api_context
    )
    act_as(owner)
    created = client.post(
        "/api/v1/questions",
        json={"content": "This question should be deleted.", "language": "en"},
    )
    question_id = UUID(created.json()["question"]["id"])

    act_as(reviewer)
    response = client.post(
        f"/api/v1/review/questions/{question_id}/response",
        json={"response": "A response retained after professional deletion."},
    )
    assert response.status_code == 201
    response_id = UUID(response.json()["id"])

    db = SessionLocal()
    try:
        delete_account(db, reviewer)
        retained_response = db.get(ProfessionalResponse, response_id)
        assert retained_response is not None
        assert retained_response.professional_user_id is None

        delete_account(db, owner)
        assert db.get(User, owner.id) is None
        assert db.get(VaccineQuestion, question_id) is None
        assert db.scalar(
            select(QuestionAnalysis).where(QuestionAnalysis.question_id == question_id)
        ) is None
        assert db.scalar(
            select(ProfessionalResponse).where(
                ProfessionalResponse.question_id == question_id
            )
        ) is None
    finally:
        db.close()
