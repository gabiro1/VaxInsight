from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.narrative import (
    Narrative,
    NarrativeRevision,
    NarrativeRevisionAction,
    NarrativeStatus,
)
from app.models.review import AssignmentStatus, NarrativeAssignment
from app.models.user import User
from app.services.audit import add_audit_event


class NarrativeNotEditable(Exception):
    """Raised when a future lifecycle state does not allow owner updates."""


class NarrativePersistenceError(Exception):
    """Raised when narrative storage cannot complete safely."""


@dataclass(frozen=True)
class NarrativePage:
    narratives: list[Narrative]
    total: int


@dataclass(frozen=True)
class NarrativeRevisionPage:
    revisions: list[NarrativeRevision]
    total: int


def create_narrative(db: Session, *, actor: User, content: str) -> Narrative:
    """Create an owner-scoped narrative and its first immutable revision."""

    try:
        narrative = Narrative(
            submitted_by_id=actor.id,
            content=content,
            status=NarrativeStatus.SUBMITTED.value,
            version=1,
        )
        db.add(narrative)
        db.flush()

        db.add(
            NarrativeRevision(
                narrative_id=narrative.id,
                changed_by_user_id=actor.id,
                version=narrative.version,
                action=NarrativeRevisionAction.CREATED.value,
                content=content,
            )
        )
        add_audit_event(
            db,
            action="narrative_created",
            outcome="success",
            actor_user_id=actor.id,
            target_user_id=actor.id,
        )
        db.commit()
        db.refresh(narrative)
        return narrative
    except SQLAlchemyError as error:
        db.rollback()
        raise NarrativePersistenceError from error


def get_owned_narrative(
    db: Session,
    *,
    narrative_id: UUID,
    owner_id: UUID,
) -> Narrative | None:
    """Return a narrative only when the caller is its submitter."""

    try:
        narrative = db.scalar(
            select(Narrative).where(
                Narrative.id == narrative_id,
                Narrative.submitted_by_id == owner_id,
            )
        )
        if narrative is not None:
            _attach_active_review_status(db, [narrative])
        return narrative
    except SQLAlchemyError as error:
        db.rollback()
        raise NarrativePersistenceError from error


def list_owned_narratives(
    db: Session,
    *,
    owner_id: UUID,
    page: int,
    page_size: int,
    status: str | None = None,
    submitted_after: datetime | None = None,
    submitted_before: datetime | None = None,
) -> NarrativePage:
    """List only the caller's narratives with database-side filtering and paging."""

    filters = [Narrative.submitted_by_id == owner_id]
    if status is not None:
        filters.append(Narrative.status == status)
    if submitted_after is not None:
        filters.append(Narrative.submitted_at >= submitted_after)
    if submitted_before is not None:
        filters.append(Narrative.submitted_at <= submitted_before)

    try:
        total = db.scalar(select(func.count(Narrative.id)).where(*filters)) or 0
        narratives = list(
            db.scalars(
                select(Narrative)
                .where(*filters)
                .order_by(Narrative.submitted_at.desc(), Narrative.id.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        _attach_active_review_status(db, narratives)
        return NarrativePage(narratives=narratives, total=total)
    except SQLAlchemyError as error:
        db.rollback()
        raise NarrativePersistenceError from error


def _attach_active_review_status(
    db: Session,
    narratives: list[Narrative],
) -> None:
    """Attach only status metadata for active owner review assignments."""

    narrative_ids = [narrative.id for narrative in narratives]
    if not narrative_ids:
        return

    statuses = dict(
        db.execute(
            select(
                NarrativeAssignment.narrative_id,
                NarrativeAssignment.review_status,
            ).where(
                NarrativeAssignment.narrative_id.in_(narrative_ids),
                NarrativeAssignment.status == AssignmentStatus.ACTIVE.value,
            )
        ).all()
    )
    for narrative in narratives:
        narrative.review_status = statuses.get(narrative.id)


def update_owned_narrative(
    db: Session,
    *,
    actor: User,
    narrative_id: UUID,
    content: str,
) -> Narrative | None:
    """Update owner content and append a revision without changing lifecycle state."""

    try:
        narrative = db.scalar(
            select(Narrative)
            .where(
                Narrative.id == narrative_id,
                Narrative.submitted_by_id == actor.id,
            )
            .with_for_update()
        )
        if narrative is None:
            return None
        if narrative.status != NarrativeStatus.SUBMITTED.value:
            db.rollback()
            raise NarrativeNotEditable
        active_assignment = db.scalar(
            select(NarrativeAssignment.id).where(
                NarrativeAssignment.narrative_id == narrative.id,
                NarrativeAssignment.status == AssignmentStatus.ACTIVE.value,
            )
        )
        if active_assignment is not None:
            db.rollback()
            raise NarrativeNotEditable
        if narrative.content == content:
            db.rollback()
            return narrative

        narrative.version += 1
        narrative.content = content
        db.add(
            NarrativeRevision(
                narrative_id=narrative.id,
                changed_by_user_id=actor.id,
                version=narrative.version,
                action=NarrativeRevisionAction.UPDATED.value,
                content=content,
            )
        )
        add_audit_event(
            db,
            action="narrative_updated",
            outcome="success",
            actor_user_id=actor.id,
            target_user_id=actor.id,
        )
        db.commit()
        db.refresh(narrative)
        return narrative
    except NarrativeNotEditable:
        raise
    except SQLAlchemyError as error:
        db.rollback()
        raise NarrativePersistenceError from error


def list_owned_narrative_revisions(
    db: Session,
    *,
    owner_id: UUID,
    narrative_id: UUID,
    page: int,
    page_size: int,
) -> NarrativeRevisionPage | None:
    """List revisions only after confirming owner access to the narrative."""

    try:
        if (
            get_owned_narrative(db, narrative_id=narrative_id, owner_id=owner_id)
            is None
        ):
            return None

        filters = [NarrativeRevision.narrative_id == narrative_id]
        total = db.scalar(select(func.count(NarrativeRevision.id)).where(*filters)) or 0
        revisions = list(
            db.scalars(
                select(NarrativeRevision)
                .where(*filters)
                .order_by(NarrativeRevision.version.asc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        return NarrativeRevisionPage(revisions=revisions, total=total)
    except SQLAlchemyError as error:
        db.rollback()
        raise NarrativePersistenceError from error
