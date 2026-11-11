from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.account import is_active_account
from app.models.narrative import Narrative, NarrativeStatus
from app.models.review import (
    AssignmentStatus,
    NarrativeAssignment,
    NarrativeReview,
    ReviewEvidenceReference,
    ReviewOutcome,
    ReviewStatus,
)
from app.models.user import User, UserRole
from app.schemas.review import ReviewEvidenceCreate
from app.services.audit import add_audit_event


class ReviewPersistenceError(Exception):
    """Raised when review workflow storage cannot complete safely."""


class ReviewerNotEligible(Exception):
    """Raised when an assignment target is not an active Health Expert."""


class AssignmentStateConflict(Exception):
    """Raised when an assignment lifecycle operation is not valid."""


class ReviewStateConflict(Exception):
    """Raised when a review lifecycle operation is not valid."""


@dataclass(frozen=True)
class AssignmentPage:
    assignments: list[NarrativeAssignment]
    narratives: dict[UUID, Narrative]
    total: int


@dataclass(frozen=True)
class ReviewHistoryPage:
    reviews: list[NarrativeReview]
    evidence: dict[UUID, list[ReviewEvidenceReference]]
    total: int


@dataclass(frozen=True)
class ReviewWithEvidence:
    review: NarrativeReview
    evidence: list[ReviewEvidenceReference]


def _is_eligible_reviewer(user: User | None) -> bool:
    return bool(
        user is not None
        and is_active_account(user)
        and user.role == UserRole.REVIEWER.value
    )


def _permission_value(value) -> str:
    return value.value if hasattr(value, "value") else value


def create_assignment(
    db: Session,
    *,
    actor: User,
    narrative_id: UUID,
    reviewer_id: UUID,
) -> NarrativeAssignment | None:
    """Create one active Health Expert assignment while locking the narrative row."""

    try:
        narrative = db.scalar(
            select(Narrative).where(Narrative.id == narrative_id).with_for_update()
        )
        if narrative is None:
            return None
        if narrative.status != NarrativeStatus.SUBMITTED.value:
            raise AssignmentStateConflict(
                "Only submitted narratives can be assigned for review"
            )

        reviewer = db.scalar(select(User).where(User.id == reviewer_id))
        if not _is_eligible_reviewer(reviewer):
            raise ReviewerNotEligible

        active_assignment = db.scalar(
            select(NarrativeAssignment)
            .where(
                NarrativeAssignment.narrative_id == narrative_id,
                NarrativeAssignment.status == AssignmentStatus.ACTIVE.value,
            )
            .with_for_update()
        )
        if active_assignment is not None:
            raise AssignmentStateConflict("Narrative already has an active assignment")

        assignment = NarrativeAssignment(
            narrative_id=narrative_id,
            reviewer_id=reviewer_id,
            assigned_by_user_id=actor.id,
            status=AssignmentStatus.ACTIVE.value,
            review_status=ReviewStatus.PENDING.value,
        )
        db.add(assignment)
        db.flush()
        add_audit_event(
            db,
            action="narrative_assignment_created",
            outcome="success",
            actor_user_id=actor.id,
            target_user_id=reviewer_id,
            details={
                "assignment_status": AssignmentStatus.ACTIVE.value,
                "review_status": ReviewStatus.PENDING.value,
            },
        )
        db.commit()
        db.refresh(assignment)
        return assignment
    except (AssignmentStateConflict, ReviewerNotEligible):
        db.rollback()
        raise
    except SQLAlchemyError as error:
        db.rollback()
        raise ReviewPersistenceError from error


def reassign_assignment(
    db: Session,
    *,
    actor: User,
    narrative_id: UUID,
    reviewer_id: UUID,
    reason: str,
) -> NarrativeAssignment | None:
    """Revoke the active assignment and create a new active assignment atomically."""

    try:
        narrative = db.scalar(
            select(Narrative).where(Narrative.id == narrative_id).with_for_update()
        )
        if narrative is None:
            return None

        active_assignment = db.scalar(
            select(NarrativeAssignment)
            .where(
                NarrativeAssignment.narrative_id == narrative_id,
                NarrativeAssignment.status == AssignmentStatus.ACTIVE.value,
            )
            .with_for_update()
        )
        if active_assignment is None:
            return None
        if active_assignment.reviewer_id == reviewer_id:
            raise AssignmentStateConflict(
                "Narrative is already assigned to this Health Expert"
            )

        reviewer = db.scalar(select(User).where(User.id == reviewer_id))
        if not _is_eligible_reviewer(reviewer):
            raise ReviewerNotEligible

        now = datetime.now(UTC)
        active_assignment.status = AssignmentStatus.REVOKED.value
        active_assignment.revoked_at = now
        active_assignment.revoked_by_user_id = actor.id
        active_assignment.revoked_reason = reason

        replacement = NarrativeAssignment(
            narrative_id=narrative_id,
            reviewer_id=reviewer_id,
            assigned_by_user_id=actor.id,
            status=AssignmentStatus.ACTIVE.value,
            review_status=ReviewStatus.PENDING.value,
        )
        db.add(replacement)
        db.flush()
        add_audit_event(
            db,
            action="narrative_assignment_changed",
            outcome="success",
            actor_user_id=actor.id,
            target_user_id=reviewer_id,
            details={
                "assignment_status": AssignmentStatus.ACTIVE.value,
                "review_status": ReviewStatus.PENDING.value,
            },
        )
        db.commit()
        db.refresh(replacement)
        return replacement
    except (AssignmentStateConflict, ReviewerNotEligible):
        db.rollback()
        raise
    except SQLAlchemyError as error:
        db.rollback()
        raise ReviewPersistenceError from error


def revoke_assignment(
    db: Session,
    *,
    actor: User,
    narrative_id: UUID,
    reason: str,
) -> NarrativeAssignment | None:
    """Revoke an active assignment without deleting its review history."""

    try:
        db.scalar(
            select(Narrative).where(Narrative.id == narrative_id).with_for_update()
        )
        assignment = db.scalar(
            select(NarrativeAssignment)
            .where(
                NarrativeAssignment.narrative_id == narrative_id,
                NarrativeAssignment.status == AssignmentStatus.ACTIVE.value,
            )
            .with_for_update()
        )
        if assignment is None:
            return None

        assignment.status = AssignmentStatus.REVOKED.value
        assignment.revoked_at = datetime.now(UTC)
        assignment.revoked_by_user_id = actor.id
        assignment.revoked_reason = reason
        add_audit_event(
            db,
            action="narrative_assignment_revoked",
            outcome="success",
            actor_user_id=actor.id,
            target_user_id=assignment.reviewer_id,
            details={
                "assignment_status": AssignmentStatus.REVOKED.value,
                "review_status": assignment.review_status,
            },
        )
        db.commit()
        db.refresh(assignment)
        return assignment
    except SQLAlchemyError as error:
        db.rollback()
        raise ReviewPersistenceError from error


def list_assignments(
    db: Session,
    *,
    reviewer_id: UUID | None,
    page: int,
    page_size: int,
    include_narratives: bool,
) -> AssignmentPage:
    """List active assignments with content only for the assigned Health Expert."""

    filters = [NarrativeAssignment.status == AssignmentStatus.ACTIVE.value]
    if reviewer_id is not None:
        filters.append(NarrativeAssignment.reviewer_id == reviewer_id)

    try:
        total = (
            db.scalar(select(func.count(NarrativeAssignment.id)).where(*filters)) or 0
        )
        assignments = list(
            db.scalars(
                select(NarrativeAssignment)
                .where(*filters)
                .order_by(
                    NarrativeAssignment.assigned_at.desc(),
                    NarrativeAssignment.id.desc(),
                )
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        narratives: dict[UUID, Narrative] = {}
        if include_narratives and assignments:
            narrative_ids = {assignment.narrative_id for assignment in assignments}
            narratives = {
                narrative.id: narrative
                for narrative in db.scalars(
                    select(Narrative).where(Narrative.id.in_(narrative_ids))
                )
            }
        return AssignmentPage(
            assignments=assignments,
            narratives=narratives,
            total=total,
        )
    except SQLAlchemyError as error:
        db.rollback()
        raise ReviewPersistenceError from error


def get_visible_assignment(
    db: Session,
    *,
    assignment_id: UUID,
    reviewer_id: UUID | None,
    can_manage_assignments: bool,
) -> tuple[NarrativeAssignment, Narrative | None] | None:
    """Return metadata to administrators and content only to the assigned Health Expert."""

    try:
        assignment = db.get(NarrativeAssignment, assignment_id)
        if assignment is None:
            return None
        if can_manage_assignments:
            return assignment, None
        if (
            reviewer_id is None
            or assignment.status != AssignmentStatus.ACTIVE.value
            or assignment.reviewer_id != reviewer_id
        ):
            return None
        narrative = db.get(Narrative, assignment.narrative_id)
        if narrative is None:
            return None
        return assignment, narrative
    except SQLAlchemyError as error:
        db.rollback()
        raise ReviewPersistenceError from error


def list_review_history(
    db: Session,
    *,
    assignment_id: UUID,
    reviewer_id: UUID | None,
    can_manage_assignments: bool,
    page: int,
    page_size: int,
) -> ReviewHistoryPage | None:
    """List immutable review records only to the assigned Health Expert or administrators."""

    try:
        assignment = db.get(NarrativeAssignment, assignment_id)
        if assignment is None:
            return None
        if not can_manage_assignments and (
            reviewer_id is None
            or assignment.status != AssignmentStatus.ACTIVE.value
            or assignment.reviewer_id != reviewer_id
        ):
            return None

        # A replacement Health Expert needs the narrative's prior review history, while
        # access is still gated by the currently active assignment above.
        review_filter = NarrativeReview.narrative_id == assignment.narrative_id
        total = (
            db.scalar(select(func.count(NarrativeReview.id)).where(review_filter)) or 0
        )
        reviews = list(
            db.scalars(
                select(NarrativeReview)
                .where(review_filter)
                .order_by(NarrativeReview.reviewed_at.asc(), NarrativeReview.id.asc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        evidence: dict[UUID, list[ReviewEvidenceReference]] = {}
        if reviews:
            review_ids = {review.id for review in reviews}
            evidence_rows = list(
                db.scalars(
                    select(ReviewEvidenceReference)
                    .where(ReviewEvidenceReference.review_id.in_(review_ids))
                    .order_by(
                        ReviewEvidenceReference.created_at.asc(),
                        ReviewEvidenceReference.id.asc(),
                    )
                )
            )
            for evidence_row in evidence_rows:
                evidence.setdefault(evidence_row.review_id, []).append(evidence_row)
        return ReviewHistoryPage(reviews=reviews, evidence=evidence, total=total)
    except SQLAlchemyError as error:
        db.rollback()
        raise ReviewPersistenceError from error


def update_review_status(
    db: Session,
    *,
    actor: User,
    assignment_id: UUID,
    status: ReviewStatus,
    reason: str | None,
    can_manage_assignments: bool,
) -> NarrativeAssignment | None:
    """Apply only explicit human status transitions; escalation never auto-resolves."""

    requested_status = _permission_value(status)
    try:
        assignment = db.scalar(
            select(NarrativeAssignment)
            .where(NarrativeAssignment.id == assignment_id)
            .with_for_update()
        )
        if assignment is None:
            return None
        if not can_manage_assignments and (
            assignment.status != AssignmentStatus.ACTIVE.value
            or assignment.reviewer_id != actor.id
        ):
            return None
        if assignment.status != AssignmentStatus.ACTIVE.value:
            raise AssignmentStateConflict("Revoked assignments cannot change status")
        if requested_status in {
            ReviewStatus.PENDING.value,
            ReviewStatus.REVIEWED.value,
        }:
            raise ReviewStateConflict(
                "Pending and reviewed statuses are controlled by assignment creation "
                "and review submission"
            )
        if requested_status == ReviewStatus.IN_REVIEW.value:
            if assignment.review_status != ReviewStatus.PENDING.value:
                raise ReviewStateConflict("Only pending assignments can enter review")
        elif requested_status == ReviewStatus.REQUIRES_ESCALATION.value:
            if assignment.review_status not in {
                ReviewStatus.PENDING.value,
                ReviewStatus.IN_REVIEW.value,
            }:
                raise ReviewStateConflict("This assignment cannot be escalated")
            if not reason:
                raise ReviewStateConflict("An escalation reason is required")
        else:
            raise ReviewStateConflict("Unsupported review status transition")

        assignment.review_status = requested_status
        add_audit_event(
            db,
            action=(
                "narrative_review_escalated"
                if requested_status == ReviewStatus.REQUIRES_ESCALATION.value
                else "narrative_review_status_changed"
            ),
            outcome="success",
            actor_user_id=actor.id,
            details={
                "assignment_status": assignment.status,
                "review_status": requested_status,
            },
        )
        db.commit()
        db.refresh(assignment)
        return assignment
    except (AssignmentStateConflict, ReviewStateConflict):
        db.rollback()
        raise
    except SQLAlchemyError as error:
        db.rollback()
        raise ReviewPersistenceError from error


def submit_review(
    db: Session,
    *,
    actor: User,
    assignment_id: UUID,
    outcome: ReviewOutcome,
    notes: str | None,
    evidence: list[ReviewEvidenceCreate],
) -> ReviewWithEvidence | None:
    """Append one immutable review record and mark the active assignment reviewed."""

    try:
        assignment = db.scalar(
            select(NarrativeAssignment)
            .where(NarrativeAssignment.id == assignment_id)
            .with_for_update()
        )
        if assignment is None:
            return None
        if (
            assignment.status != AssignmentStatus.ACTIVE.value
            or assignment.reviewer_id != actor.id
        ):
            return None
        if assignment.review_status != ReviewStatus.IN_REVIEW.value:
            raise ReviewStateConflict(
                "A review can only be submitted from the in_review status"
            )

        review = NarrativeReview(
            assignment_id=assignment.id,
            narrative_id=assignment.narrative_id,
            reviewer_id=actor.id,
            outcome=_permission_value(outcome),
            notes=notes,
        )
        db.add(review)
        db.flush()
        evidence_rows = [
            ReviewEvidenceReference(
                review_id=review.id,
                source_title=item.source_title,
                publisher=item.publisher,
                url=str(item.url) if item.url is not None else None,
                publication_date=item.publication_date,
                accessed_at=item.accessed_at,
                relevance=item.relevance,
            )
            for item in evidence
        ]
        db.add_all(evidence_rows)
        assignment.review_status = ReviewStatus.REVIEWED.value
        add_audit_event(
            db,
            action="narrative_review_submitted",
            outcome="success",
            actor_user_id=actor.id,
            details={
                "assignment_status": assignment.status,
                "review_status": ReviewStatus.REVIEWED.value,
                "outcome": _permission_value(outcome),
            },
        )
        db.commit()
        db.refresh(review)
        return ReviewWithEvidence(review=review, evidence=evidence_rows)
    except ReviewStateConflict:
        db.rollback()
        raise
    except SQLAlchemyError as error:
        db.rollback()
        raise ReviewPersistenceError from error
