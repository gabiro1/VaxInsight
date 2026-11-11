from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from sqlalchemy import case, func, literal, select
from sqlalchemy.orm import Session

from app.models.auth import Invitation
from app.models.user import User
from app.services.audit import add_audit_event

InvitationStatusValue = Literal["pending", "accepted", "revoked", "expired"]


class InvitationNotDeletable(Exception):
    """Raised when an invitation is not in the revoked state."""


@dataclass(frozen=True)
class AdminInvitationRecord:
    id: UUID
    email: str
    role: str
    status: InvitationStatusValue
    created_at: datetime
    expires_at: datetime
    accepted_at: datetime | None
    revoked_at: datetime | None


@dataclass(frozen=True)
class AdminInvitationPage:
    invitations: list[AdminInvitationRecord]
    total: int


INVITATION_COLUMNS = (
    Invitation.id,
    Invitation.email,
    Invitation.role,
    Invitation.created_at,
    Invitation.expires_at,
    Invitation.accepted_at,
    Invitation.revoked_at,
)


def invitation_status(
    *,
    accepted_at: datetime | None,
    revoked_at: datetime | None,
    expires_at: datetime,
    now: datetime,
) -> InvitationStatusValue:
    if expires_at.tzinfo is None or expires_at.utcoffset() is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if accepted_at is not None:
        return "accepted"
    if revoked_at is not None:
        return "revoked"
    if expires_at <= now:
        return "expired"
    return "pending"


def _status_conditions(now: datetime):
    return {
        "pending": (
            Invitation.accepted_at.is_(None),
            Invitation.revoked_at.is_(None),
            Invitation.expires_at > now,
        ),
        "accepted": (Invitation.accepted_at.is_not(None),),
        "revoked": (
            Invitation.accepted_at.is_(None),
            Invitation.revoked_at.is_not(None),
        ),
        "expired": (
            Invitation.accepted_at.is_(None),
            Invitation.revoked_at.is_(None),
            Invitation.expires_at <= now,
        ),
    }


def _status_expression(now: datetime):
    return case(
        (Invitation.accepted_at.is_not(None), literal("accepted")),
        (Invitation.revoked_at.is_not(None), literal("revoked")),
        (Invitation.expires_at <= now, literal("expired")),
        else_=literal("pending"),
    )


def _record_from_row(row, now: datetime) -> AdminInvitationRecord:
    return AdminInvitationRecord(
        id=row.id,
        email=row.email,
        role=row.role,
        status=invitation_status(
            accepted_at=row.accepted_at,
            revoked_at=row.revoked_at,
            expires_at=row.expires_at,
            now=now,
        ),
        created_at=row.created_at,
        expires_at=row.expires_at,
        accepted_at=row.accepted_at,
        revoked_at=row.revoked_at,
    )


def list_admin_invitations(
    db: Session,
    *,
    page: int,
    page_size: int,
    search: str | None = None,
    role: str | None = None,
    status: InvitationStatusValue | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> AdminInvitationPage:
    """List invitation metadata with SQL-side lifecycle filtering and paging."""

    now = datetime.now(UTC)
    filters = []
    if search is not None:
        filters.append(Invitation.email.ilike(f"%{search}%"))
    if role is not None:
        filters.append(Invitation.role == role)
    if status is not None:
        filters.extend(_status_conditions(now)[status])

    sort_columns = {
        "created_at": Invitation.created_at,
        "expires_at": Invitation.expires_at,
        "email": Invitation.email,
        "status": _status_expression(now),
    }
    sort_column = sort_columns[sort_by]
    primary_order = sort_column.asc() if sort_order == "asc" else sort_column.desc()
    tie_order = Invitation.id.asc() if sort_order == "asc" else Invitation.id.desc()

    total = db.scalar(select(func.count(Invitation.id)).where(*filters)) or 0
    rows = db.execute(
        select(*INVITATION_COLUMNS)
        .where(*filters)
        .order_by(primary_order, tie_order)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    return AdminInvitationPage(
        invitations=[_record_from_row(row, now) for row in rows],
        total=total,
    )


def get_admin_invitation(
    db: Session,
    invitation_id: UUID,
) -> AdminInvitationRecord | None:
    """Retrieve one invitation without selecting its token hash."""

    now = datetime.now(UTC)
    row = db.execute(
        select(*INVITATION_COLUMNS).where(Invitation.id == invitation_id)
    ).one_or_none()
    return _record_from_row(row, now) if row is not None else None


def delete_revoked_invitation(
    db: Session,
    *,
    invitation_id: UUID,
    deleted_by: User,
) -> bool:
    """Permanently delete one revoked invitation and retain an audit event."""

    invitation = db.scalar(
        select(Invitation).where(Invitation.id == invitation_id).with_for_update()
    )
    if invitation is None:
        return False
    if invitation.revoked_at is None or invitation.accepted_at is not None:
        raise InvitationNotDeletable

    add_audit_event(
        db,
        action="invitation_deleted",
        outcome="success",
        actor_user_id=deleted_by.id,
        details={"role": invitation.role},
    )
    db.delete(invitation)
    db.commit()
    return True
