from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.auth import AuditEvent


@dataclass(frozen=True)
class AuditEventPage:
    events: list[AuditEvent]
    total: int


SAFE_DETAIL_VALUES = {
    "role": {"community_member", "chw", "reviewer", "administrator"},
    "status": {"pending", "active", "suspended", "deactivated", "deleted"},
    "assignment_status": {"active", "revoked"},
    "review_status": {"pending", "in_review", "reviewed", "requires_escalation"},
    "outcome": {
        "needs_further_review",
        "evidence_supports_claim",
        "evidence_does_not_support_claim",
        "insufficient_evidence",
    },
}


def add_audit_event(
    db: Session,
    *,
    action: str,
    outcome: str,
    actor_user_id: UUID | None = None,
    target_user_id: UUID | None = None,
    request: Request | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    """Stage an audit event without storing credentials or raw tokens."""

    ip_address = None
    user_agent = None

    if request is not None:
        if request.client is not None:
            ip_address = request.client.host
        user_agent = request.headers.get("user-agent")

    db.add(
        AuditEvent(
            actor_user_id=actor_user_id,
            target_user_id=target_user_id,
            action=action,
            outcome=outcome,
            ip_address=ip_address,
            user_agent=user_agent[:512] if user_agent else None,
            details=details,
        )
    )


def sanitize_audit_details(details: Any) -> dict[str, str]:
    """Return only known, non-secret audit detail values."""

    if not isinstance(details, dict):
        return {}

    safe_details: dict[str, str] = {}
    for key, allowed_values in SAFE_DETAIL_VALUES.items():
        value = details.get(key)
        if isinstance(value, str) and value in allowed_values:
            safe_details[key] = value
    return safe_details


def list_audit_events(
    db: Session,
    *,
    page: int,
    page_size: int,
    action: str | None = None,
    outcome: str | None = None,
    actor_user_id: UUID | None = None,
    target_user_id: UUID | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> AuditEventPage:
    """Query audit events with stable newest-first pagination."""

    filters = []
    if action is not None:
        filters.append(AuditEvent.action == action)
    if outcome is not None:
        filters.append(AuditEvent.outcome == outcome)
    if actor_user_id is not None:
        filters.append(AuditEvent.actor_user_id == actor_user_id)
    if target_user_id is not None:
        filters.append(AuditEvent.target_user_id == target_user_id)
    if start_date is not None:
        filters.append(AuditEvent.created_at >= start_date)
    if end_date is not None:
        filters.append(AuditEvent.created_at <= end_date)

    total = db.scalar(select(func.count()).select_from(AuditEvent).where(*filters)) or 0

    events = list(
        db.scalars(
            select(AuditEvent)
            .where(*filters)
            .order_by(
                AuditEvent.created_at.desc(),
                AuditEvent.id.desc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )

    return AuditEventPage(events=events, total=total)
