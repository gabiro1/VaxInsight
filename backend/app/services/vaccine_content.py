from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.models.user import User
from app.models.vaccine_content import (
    ContentLanguage,
    VaccineContent,
    VaccineContentStatus,
    VaccineSource,
)
from app.services.audit import add_audit_event


class VaccineContentPersistenceError(Exception):
    """Raised when registry content cannot be stored or read safely."""


class VaccineContentConflict(Exception):
    """Raised when a content version already exists for a source and locale."""


def create_vaccine_content(
    db: Session,
    *,
    actor: User,
    source_authority: str,
    source_name: str,
    source_url: str,
    source_jurisdiction: str,
    language: ContentLanguage,
    category: str,
    title: str,
    summary: str,
    body: str,
    version: int,
    status: VaccineContentStatus,
) -> VaccineContent:
    """Create content and reuse an identical source in one transaction."""

    try:
        source = db.scalar(
            select(VaccineSource)
            .where(
                VaccineSource.authority == source_authority,
                VaccineSource.name == source_name,
                VaccineSource.url == source_url,
                VaccineSource.jurisdiction == source_jurisdiction,
            )
            .with_for_update()
        )
        if source is None:
            source = VaccineSource(
                authority=source_authority,
                name=source_name,
                url=source_url,
                jurisdiction=source_jurisdiction,
                created_by_user_id=actor.id,
            )
            db.add(source)
            db.flush()

        now = datetime.now(UTC)
        published = status == VaccineContentStatus.PUBLISHED
        content = VaccineContent(
            source_id=source.id,
            language=language.value,
            category=category,
            title=title,
            summary=summary,
            body=body,
            version=version,
            status=status.value,
            published_at=now if published else None,
            created_by_user_id=actor.id,
            approved_by_user_id=actor.id if published else None,
            approved_at=now if published else None,
        )
        db.add(content)
        db.flush()
        add_audit_event(
            db,
            action="vaccine_content_created",
            outcome="success",
            actor_user_id=actor.id,
            details={"status": status.value},
        )
        db.commit()
        db.refresh(content)
        return content
    except IntegrityError as error:
        db.rollback()
        raise VaccineContentConflict from error
    except SQLAlchemyError as error:
        db.rollback()
        raise VaccineContentPersistenceError from error


def list_published_content(
    db: Session,
    *,
    language: ContentLanguage | None = None,
    category: str | None = None,
) -> list[VaccineContent]:
    """Return only published registry rows with optional safe filters."""

    filters = [VaccineContent.status == VaccineContentStatus.PUBLISHED.value]
    if language is not None:
        filters.append(VaccineContent.language == language.value)
    if category is not None:
        filters.append(VaccineContent.category == category)

    try:
        return list(
            db.scalars(
                select(VaccineContent)
                .options(selectinload(VaccineContent.source))
                .where(*filters)
                .order_by(
                    VaccineContent.published_at.desc(),
                    VaccineContent.created_at.desc(),
                    VaccineContent.id.desc(),
                )
            )
        )
    except SQLAlchemyError as error:
        db.rollback()
        raise VaccineContentPersistenceError from error


def get_published_content(
    db: Session,
    *,
    content_id: UUID,
) -> VaccineContent | None:
    """Return a registry row only when its current state is published."""

    try:
        return db.scalar(
            select(VaccineContent)
            .options(selectinload(VaccineContent.source))
            .where(
                VaccineContent.id == content_id,
                VaccineContent.status == VaccineContentStatus.PUBLISHED.value,
            )
        )
    except SQLAlchemyError as error:
        db.rollback()
        raise VaccineContentPersistenceError from error
