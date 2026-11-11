from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.user import User


@dataclass(frozen=True)
class AdminUserRecord:
    id: UUID
    email: str
    role: str | None
    status: str
    email_verified_at: datetime | None
    created_at: datetime
    last_login_at: datetime | None
    updated_at: datetime


@dataclass(frozen=True)
class AdminUserPage:
    users: list[AdminUserRecord]
    total: int


USER_COLUMNS = (
    User.id,
    User.email,
    User.role,
    User.status,
    User.email_verified_at,
    User.created_at,
    User.last_login_at,
    User.updated_at,
)

SORT_COLUMNS = {
    "created_at": User.created_at,
    "updated_at": User.updated_at,
    "email": User.email,
    "last_login_at": User.last_login_at,
    "status": User.status,
    "role": User.role,
}


def _record_from_row(row) -> AdminUserRecord:
    return AdminUserRecord(
        id=row.id,
        email=row.email,
        role=row.role,
        status=row.status,
        email_verified_at=row.email_verified_at,
        created_at=row.created_at,
        last_login_at=row.last_login_at,
        updated_at=row.updated_at,
    )


def _user_filters(
    *,
    search: str | None,
    role: str | None,
    status: str | None,
    email_verified: bool | None,
):
    filters = []
    if search is not None:
        filters.append(User.email.ilike(f"%{search}%"))
    if role is not None:
        filters.append(User.role == role)
    if status is not None:
        filters.append(User.status == status)
    if email_verified is not None:
        filters.append(
            User.email_verified_at.is_not(None)
            if email_verified
            else User.email_verified_at.is_(None)
        )
    return filters


def list_admin_users(
    db: Session,
    *,
    page: int,
    page_size: int,
    search: str | None = None,
    role: str | None = None,
    status: str | None = None,
    email_verified: bool | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> AdminUserPage:
    """List approved user fields using database-side filtering and paging."""

    filters = _user_filters(
        search=search,
        role=role,
        status=status,
        email_verified=email_verified,
    )
    sort_column = SORT_COLUMNS[sort_by]
    primary_order = sort_column.asc() if sort_order == "asc" else sort_column.desc()
    if sort_by in {"last_login_at", "role"}:
        primary_order = primary_order.nulls_last()
    tie_order = User.id.asc() if sort_order == "asc" else User.id.desc()

    total = db.scalar(select(func.count(User.id)).where(*filters)) or 0
    rows = db.execute(
        select(*USER_COLUMNS)
        .where(*filters)
        .order_by(primary_order, tie_order)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    return AdminUserPage(
        users=[_record_from_row(row) for row in rows],
        total=total,
    )


def get_admin_user(db: Session, user_id: UUID) -> AdminUserRecord | None:
    """Retrieve one user without selecting authentication secrets."""

    row = db.execute(select(*USER_COLUMNS).where(User.id == user_id)).one_or_none()
    return _record_from_row(row) if row is not None else None
