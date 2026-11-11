import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


class ContentLanguage(str, Enum):
    """Languages supported by the initial content registry contract."""

    RW = "rw"
    EN = "en"


class VaccineContentStatus(str, Enum):
    """Publication states for official vaccine content."""

    DRAFT = "draft"
    PUBLISHED = "published"


class VaccineSource(Base):
    __tablename__ = "vaccine_sources"
    __table_args__ = (
        UniqueConstraint(
            "authority",
            "name",
            "url",
            "jurisdiction",
            name="uq_vaccine_sources_identity",
        ),
        CheckConstraint(
            "length(trim(authority)) > 0",
            name="ck_vaccine_sources_authority_valid",
        ),
        CheckConstraint(
            "length(trim(name)) > 0",
            name="ck_vaccine_sources_name_valid",
        ),
        CheckConstraint(
            "length(trim(jurisdiction)) > 0",
            name="ck_vaccine_sources_jurisdiction_valid",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    authority: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    jurisdiction: Mapped[str] = mapped_column(String(128), nullable=False)
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    contents: Mapped[list["VaccineContent"]] = relationship(
        back_populates="source",
    )


class VaccineContent(Base):
    __tablename__ = "vaccine_contents"
    __table_args__ = (
        UniqueConstraint(
            "source_id",
            "language",
            "category",
            "version",
            name="uq_vaccine_contents_source_language_category_version",
        ),
        CheckConstraint(
            "language IN ('rw', 'en')",
            name="ck_vaccine_contents_language",
        ),
        CheckConstraint(
            "status IN ('draft', 'published')",
            name="ck_vaccine_contents_status",
        ),
        CheckConstraint(
            "version >= 1",
            name="ck_vaccine_contents_version_positive",
        ),
        CheckConstraint(
            "length(trim(title)) > 0",
            name="ck_vaccine_contents_title_valid",
        ),
        Index(
            "ix_vaccine_contents_published_language_category",
            "status",
            "language",
            "category",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("vaccine_sources.id"),
        nullable=False,
    )
    language: Mapped[str] = mapped_column(String(8), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(
        Integer,
        default=1,
        server_default="1",
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default=VaccineContentStatus.DRAFT.value,
        server_default=VaccineContentStatus.DRAFT.value,
        nullable=False,
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    approved_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    source: Mapped[VaccineSource] = relationship(
        back_populates="contents",
    )
