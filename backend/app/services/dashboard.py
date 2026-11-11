from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.models.auth import Invitation, RefreshSession
from app.models.narrative import Narrative
from app.models.review import (
    AssignmentStatus,
    NarrativeAssignment,
    NarrativeReview,
    ReviewOutcome,
    ReviewStatus,
)
from app.models.user import AccountStatus, User, UserRole


def _user_statistics(db: Session) -> dict[str, Any]:
    total = db.scalar(select(func.count(User.id))) or 0

    status_counts = {status.value: 0 for status in AccountStatus}
    for status, count in db.execute(
        select(User.status, func.count(User.id)).group_by(User.status)
    ):
        if status in status_counts:
            status_counts[status] = count

    role_counts = {role.value: 0 for role in UserRole}
    role_counts["unassigned"] = 0
    for role, count in db.execute(
        select(User.role, func.count(User.id)).group_by(User.role)
    ):
        role_key = role if role in role_counts else "unassigned"
        role_counts[role_key] += count

    return {
        "total": total,
        "active": status_counts[AccountStatus.ACTIVE.value],
        "pending": status_counts[AccountStatus.PENDING.value],
        "suspended": status_counts[AccountStatus.SUSPENDED.value],
        "deactivated": status_counts[AccountStatus.DEACTIVATED.value],
        "deleted": status_counts[AccountStatus.DELETED.value],
        "by_role": role_counts,
    }


def _invitation_statistics(db: Session, now: datetime) -> dict[str, int]:
    pending = and_(
        Invitation.accepted_at.is_(None),
        Invitation.revoked_at.is_(None),
        Invitation.expires_at > now,
    )
    expired = and_(
        Invitation.accepted_at.is_(None),
        Invitation.revoked_at.is_(None),
        Invitation.expires_at <= now,
    )
    revoked = and_(
        Invitation.accepted_at.is_(None),
        Invitation.revoked_at.is_not(None),
    )

    row = db.execute(
        select(
            func.count(Invitation.id).label("total"),
            func.count(Invitation.id)
            .filter(Invitation.accepted_at.is_not(None))
            .label("accepted"),
            func.count(Invitation.id).filter(pending).label("pending"),
            func.count(Invitation.id).filter(expired).label("expired"),
            func.count(Invitation.id).filter(revoked).label("revoked"),
        )
    ).one()

    return {
        "total": row.total,
        "pending": row.pending,
        "accepted": row.accepted,
        "expired": row.expired,
        "revoked": row.revoked,
    }


def _session_statistics(db: Session, now: datetime) -> dict[str, int]:
    active_account = and_(
        User.is_active.is_(True),
        or_(
            User.status.is_(None),
            User.status == AccountStatus.ACTIVE.value,
        ),
    )
    active = and_(
        RefreshSession.revoked_at.is_(None),
        RefreshSession.expires_at > now,
        active_account,
    )
    expired = and_(
        RefreshSession.revoked_at.is_(None),
        RefreshSession.expires_at <= now,
    )

    row = db.execute(
        select(
            func.count(RefreshSession.id).filter(active).label("active"),
            func.count(RefreshSession.id)
            .filter(RefreshSession.revoked_at.is_not(None))
            .label("revoked"),
            func.count(RefreshSession.id).filter(expired).label("expired"),
        )
        .select_from(RefreshSession)
        .outerjoin(User, User.id == RefreshSession.user_id)
    ).one()

    return {
        "active": row.active,
        "revoked": row.revoked,
        "expired": row.expired,
    }


def _percentage(numerator: int, denominator: int) -> int:
    if not denominator:
        return 0
    return round((numerator / denominator) * 100)


def _platform_statistics(
    db: Session, now: datetime, active_users: int
) -> dict[str, int]:
    """Return the non-sensitive metrics shown on the administrator home screen."""

    period_start = now - timedelta(days=30)
    total_narratives = (
        db.scalar(
            select(func.count(Narrative.id)).where(
                Narrative.submitted_at >= period_start
            )
        )
        or 0
    )
    total_assignments = (
        db.scalar(
            select(func.count(NarrativeAssignment.id)).where(
                NarrativeAssignment.assigned_at >= period_start
            )
        )
        or 0
    )
    completed_assignments = (
        db.scalar(
            select(func.count(NarrativeAssignment.id)).where(
                NarrativeAssignment.assigned_at >= period_start,
                NarrativeAssignment.review_status == ReviewStatus.REVIEWED.value,
            )
        )
        or 0
    )
    completed_reviews = (
        db.scalar(
            select(func.count(NarrativeReview.id)).where(
                NarrativeReview.reviewed_at >= period_start
            )
        )
        or 0
    )
    evidence_supported_reviews = (
        db.scalar(
            select(func.count(NarrativeReview.id)).where(
                NarrativeReview.reviewed_at >= period_start,
                NarrativeReview.outcome == ReviewOutcome.EVIDENCE_SUPPORTS_CLAIM.value,
            )
        )
        or 0
    )

    return {
        "period_days": 30,
        "total_narratives": total_narratives,
        "active_users": active_users,
        "review_completion_rate": _percentage(completed_assignments, total_assignments),
        "trusted_info_rate": _percentage(evidence_supported_reviews, completed_reviews),
    }


def get_dashboard_summary(db: Session) -> dict[str, Any]:
    """Aggregate administrator dashboard statistics without loading entities."""

    now = datetime.now(UTC)
    users = _user_statistics(db)
    return {
        "users": users,
        "invitations": _invitation_statistics(db, now),
        "sessions": _session_statistics(db, now),
        "platform": _platform_statistics(db, now, users["active"]),
    }


def get_personal_dashboard_summary(
    db: Session,
    *,
    owner_id,
    recent_limit: int = 3,
) -> dict[str, Any]:
    """Return only activity and status data owned by one authenticated account."""

    owner_filter = Narrative.submitted_by_id == owner_id
    active_assignment = NarrativeAssignment.status == AssignmentStatus.ACTIVE.value
    review_in_progress = NarrativeAssignment.review_status.in_(
        (
            ReviewStatus.PENDING.value,
            ReviewStatus.IN_REVIEW.value,
            ReviewStatus.REQUIRES_ESCALATION.value,
        )
    )

    submitted = db.scalar(select(func.count(Narrative.id)).where(owner_filter)) or 0
    under_review = (
        db.scalar(
            select(func.count(Narrative.id))
            .select_from(Narrative)
            .join(
                NarrativeAssignment,
                and_(
                    NarrativeAssignment.narrative_id == Narrative.id,
                    active_assignment,
                    review_in_progress,
                ),
            )
            .where(owner_filter)
        )
        or 0
    )
    reviewed = (
        db.scalar(
            select(func.count(Narrative.id))
            .select_from(Narrative)
            .join(
                NarrativeAssignment,
                and_(
                    NarrativeAssignment.narrative_id == Narrative.id,
                    active_assignment,
                    NarrativeAssignment.review_status == ReviewStatus.REVIEWED.value,
                ),
            )
            .where(owner_filter)
        )
        or 0
    )

    recent_rows = db.execute(
        select(Narrative, NarrativeAssignment.review_status)
        .outerjoin(
            NarrativeAssignment,
            and_(
                NarrativeAssignment.narrative_id == Narrative.id,
                active_assignment,
            ),
        )
        .where(owner_filter)
        .order_by(Narrative.submitted_at.desc(), Narrative.id.desc())
        .limit(recent_limit)
    )

    return {
        "activity": {
            "submitted": submitted,
            "under_review": under_review,
            "reviewed": reviewed,
        },
        "recent_narratives": [
            {
                "id": narrative.id,
                "content": narrative.content,
                "status": narrative.status,
                "review_status": review_status,
                "version": narrative.version,
                "submitted_at": narrative.submitted_at,
                "updated_at": narrative.updated_at,
            }
            for narrative, review_status in recent_rows
        ],
    }
