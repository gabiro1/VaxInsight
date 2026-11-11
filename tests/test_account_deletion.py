from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from app.core.opaque_tokens import hash_opaque_token
from app.core.security import hash_password
from app.database.database import SessionLocal
from app.models.auth import (
    AuditEvent,
    EmailVerificationToken,
    Invitation,
    PasswordResetToken,
    RefreshSession,
)
from app.models.narrative import Narrative, NarrativeRevision
from app.models.review import (
    NarrativeAssignment,
    NarrativeReview,
    ReviewEvidenceReference,
)
from app.models.user import AccountStatus, User, UserRole
from app.schemas.auth import UserRegister
from app.services.auth import (
    LastActiveAdministratorError,
    delete_account,
    register_user,
)
from sqlalchemy import delete, select

pytestmark = pytest.mark.integration


def test_hard_delete_removes_dependents_and_frees_email_for_registration():
    db = SessionLocal()
    user_id = uuid4()
    email = f"delete-account-{user_id}@example.com"
    new_user_id = None

    try:
        user = User(
            id=user_id,
            email=email,
            hashed_password=hash_password("StrongPassword123!"),
            is_active=True,
            status=AccountStatus.ACTIVE.value,
            role=UserRole.CHW.value,
            email_verified_at=datetime.now(UTC),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        narrative = Narrative(
            submitted_by_id=user.id,
            content="A narrative that should be removed with its account.",
        )
        db.add(narrative)
        db.flush()

        db.add(
            NarrativeRevision(
                narrative_id=narrative.id,
                changed_by_user_id=user.id,
                version=1,
                action="created",
                content=narrative.content,
            )
        )
        assignment = NarrativeAssignment(
            narrative_id=narrative.id,
            reviewer_id=user.id,
            assigned_by_user_id=user.id,
        )
        db.add(assignment)
        db.flush()

        review = NarrativeReview(
            assignment_id=assignment.id,
            narrative_id=narrative.id,
            reviewer_id=user.id,
            outcome="insufficient_evidence",
        )
        db.add(review)
        db.flush()

        db.add_all(
            [
                ReviewEvidenceReference(
                    review_id=review.id,
                    source_title="Account deletion test source",
                    publisher="Test publisher",
                    accessed_at=datetime.now(UTC),
                    relevance="Test evidence should be removed.",
                ),
                Invitation(
                    email=email,
                    role=UserRole.CHW.value,
                    token_hash=hash_opaque_token(f"invitation-{user_id}"),
                    invited_by_id=user.id,
                    expires_at=datetime.now(UTC) + timedelta(hours=1),
                ),
                RefreshSession(
                    user_id=user.id,
                    family_id=uuid4(),
                    token_hash=hash_opaque_token(f"refresh-{user_id}"),
                    expires_at=datetime.now(UTC) + timedelta(days=1),
                ),
                PasswordResetToken(
                    user_id=user.id,
                    token_hash=hash_opaque_token(f"reset-{user_id}"),
                    expires_at=datetime.now(UTC) + timedelta(hours=1),
                ),
                EmailVerificationToken(
                    user_id=user.id,
                    token_hash=hash_opaque_token(f"verification-{user_id}"),
                    expires_at=datetime.now(UTC) + timedelta(hours=1),
                ),
                AuditEvent(
                    actor_user_id=user.id,
                    target_user_id=user.id,
                    action="account_test",
                    outcome="success",
                ),
            ]
        )
        db.commit()

        delete_account(db, user)
        db.expire_all()

        assert db.get(User, user_id) is None
        assert db.scalar(
            select(Narrative).where(Narrative.submitted_by_id == user_id)
        ) is None
        assert db.scalar(
            select(NarrativeRevision).where(
                NarrativeRevision.changed_by_user_id == user_id
            )
        ) is None
        assert db.scalar(
            select(NarrativeAssignment).where(
                NarrativeAssignment.reviewer_id == user_id
            )
        ) is None
        assert db.scalar(
            select(NarrativeReview).where(NarrativeReview.reviewer_id == user_id)
        ) is None
        assert db.scalar(
            select(Invitation).where(Invitation.email == email)
        ) is None
        assert db.scalar(
            select(RefreshSession).where(RefreshSession.user_id == user_id)
        ) is None
        assert db.scalar(
            select(PasswordResetToken).where(PasswordResetToken.user_id == user_id)
        ) is None
        assert db.scalar(
            select(EmailVerificationToken).where(
                EmailVerificationToken.user_id == user_id
            )
        ) is None
        assert db.scalar(
            select(AuditEvent).where(
                (AuditEvent.actor_user_id == user_id)
                | (AuditEvent.target_user_id == user_id)
            )
        ) is None

        new_user = register_user(
            db,
            UserRegister(
                full_name="Re-registered user",
                email=email,
                password="AnotherStrongPassword123!",
                confirm_password="AnotherStrongPassword123!",
            ),
        )
        new_user_id = new_user.id
        assert new_user.email == email
        assert new_user.status == AccountStatus.PENDING.value
    finally:
        db.rollback()
        for candidate_id in (new_user_id, user_id):
            if candidate_id is None:
                continue
            candidate = db.get(User, candidate_id)
            if candidate is not None:
                delete_account(db, candidate)
        db.close()


def test_hard_delete_rejects_the_last_active_administrator():
    db = SessionLocal()
    user_id = uuid4()

    try:
        admin = User(
            id=user_id,
            email=f"last-admin-delete-{user_id}@example.com",
            hashed_password=hash_password("StrongPassword123!"),
            is_active=True,
            status=AccountStatus.ACTIVE.value,
            role=UserRole.ADMINISTRATOR.value,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

        with pytest.raises(LastActiveAdministratorError):
            delete_account(db, admin)

        assert db.get(User, user_id) is not None
    finally:
        db.rollback()
        db.execute(delete(User).where(User.id == user_id))
        db.commit()
        db.close()
