from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.questions import (
    ProfessionalResponse,
    ProfessionalResponseStatus,
    QuestionAnalysis,
    QuestionAnalysisStatus,
    QuestionStatus,
    VaccineQuestion,
)
from app.models.user import User
from app.services.audit import add_audit_event

NO_ANALYSIS_PROVIDER_LIMITATIONS = (
    "An approved Phase 1 model/dataset is not configured; no AI or medical output "
    "was generated."
)
ANALYSIS_PROVIDER_FAILURE_LIMITATIONS = (
    "The configured analysis provider was unavailable; no AI or medical output was "
    "generated."
)


class QuestionPersistenceError(Exception):
    """Raised when question workflow storage cannot complete safely."""


class QuestionAnalysisProvider(Protocol):
    """Explicit boundary for a future approved analysis implementation."""

    def analyze(self, question: VaccineQuestion) -> "AnalysisResult":
        ...


@dataclass(frozen=True)
class AnalysisResult:
    """Provider output accepted only from an explicitly configured provider."""

    provider: str
    model: str
    dataset_version: str
    category: str | None
    answer: str
    explanation: str
    explanation_method: str
    confidence: float | None
    limitations: str | None = None


def get_analysis_provider() -> QuestionAnalysisProvider | None:
    """Return the configured approved provider, or none until one is approved."""

    return None


@dataclass(frozen=True)
class QuestionDetail:
    question: VaccineQuestion
    latest_analysis: QuestionAnalysis | None
    latest_professional_response: ProfessionalResponse | None


def _analysis_from_provider(question: VaccineQuestion) -> QuestionAnalysis:
    provider = get_analysis_provider()
    if provider is None:
        return QuestionAnalysis(
            question_id=question.id,
            status=QuestionAnalysisStatus.UNAVAILABLE.value,
            limitations=NO_ANALYSIS_PROVIDER_LIMITATIONS,
        )

    try:
        result = provider.analyze(question)
    except Exception:  # noqa: BLE001 - provider failures become explicit failed runs
        return QuestionAnalysis(
            question_id=question.id,
            status=QuestionAnalysisStatus.FAILED.value,
            limitations=ANALYSIS_PROVIDER_FAILURE_LIMITATIONS,
        )

    return QuestionAnalysis(
        question_id=question.id,
        status=QuestionAnalysisStatus.READY.value,
        provider=result.provider,
        model=result.model,
        dataset_version=result.dataset_version,
        category=result.category,
        answer=result.answer,
        explanation=result.explanation,
        explanation_method=result.explanation_method,
        confidence=result.confidence,
        limitations=result.limitations,
    )


def _latest_analysis(db: Session, question_id: UUID) -> QuestionAnalysis | None:
    return db.scalar(
        select(QuestionAnalysis)
        .where(QuestionAnalysis.question_id == question_id)
        .order_by(QuestionAnalysis.created_at.desc(), QuestionAnalysis.id.desc())
        .limit(1)
    )


def _latest_published_response(
    db: Session,
    question_id: UUID,
) -> ProfessionalResponse | None:
    return db.scalar(
        select(ProfessionalResponse)
        .where(
            ProfessionalResponse.question_id == question_id,
            ProfessionalResponse.status == ProfessionalResponseStatus.PUBLISHED.value,
        )
        .order_by(ProfessionalResponse.created_at.desc(), ProfessionalResponse.id.desc())
        .limit(1)
    )


def _question_detail(db: Session, question: VaccineQuestion) -> QuestionDetail:
    return QuestionDetail(
        question=question,
        latest_analysis=_latest_analysis(db, question.id),
        latest_professional_response=_latest_published_response(db, question.id),
    )


def create_question(
    db: Session,
    *,
    actor: User,
    content: str,
    language: str,
    topic: str | None,
) -> QuestionDetail:
    """Store a question and one provider-bound analysis run atomically."""

    try:
        question = VaccineQuestion(
            asked_by_user_id=actor.id,
            content=content,
            language=language,
            topic=topic,
            status=QuestionStatus.PENDING.value,
        )
        db.add(question)
        db.flush()
        db.add(_analysis_from_provider(question))
        question.status = QuestionStatus.AWAITING_REVIEW.value
        add_audit_event(
            db,
            action="question_created",
            outcome="success",
            actor_user_id=actor.id,
            target_user_id=actor.id,
            details={"status": question.status},
        )
        db.commit()
        db.refresh(question)
        return _question_detail(db, question)
    except SQLAlchemyError as error:
        db.rollback()
        raise QuestionPersistenceError from error


def list_owned_questions(db: Session, *, owner_id: UUID) -> list[VaccineQuestion]:
    """List only questions asked by the authenticated account."""

    try:
        return list(
            db.scalars(
                select(VaccineQuestion)
                .where(VaccineQuestion.asked_by_user_id == owner_id)
                .order_by(VaccineQuestion.created_at.desc(), VaccineQuestion.id.desc())
            )
        )
    except SQLAlchemyError as error:
        db.rollback()
        raise QuestionPersistenceError from error


def get_owned_question_detail(
    db: Session,
    *,
    question_id: UUID,
    owner_id: UUID,
) -> QuestionDetail | None:
    """Return a question detail only after applying the owner predicate."""

    try:
        question = db.scalar(
            select(VaccineQuestion).where(
                VaccineQuestion.id == question_id,
                VaccineQuestion.asked_by_user_id == owner_id,
            )
        )
        return _question_detail(db, question) if question is not None else None
    except SQLAlchemyError as error:
        db.rollback()
        raise QuestionPersistenceError from error


def request_question_analysis(
    db: Session,
    *,
    actor: User,
    question_id: UUID,
) -> QuestionAnalysis | None:
    """Append another immutable provider-bound analysis run for an owned question."""

    try:
        question = db.scalar(
            select(VaccineQuestion)
            .where(
                VaccineQuestion.id == question_id,
                VaccineQuestion.asked_by_user_id == actor.id,
            )
            .with_for_update()
        )
        if question is None:
            return None

        analysis = _analysis_from_provider(question)
        db.add(analysis)
        if question.status != QuestionStatus.RESPONDED.value:
            question.status = QuestionStatus.AWAITING_REVIEW.value
        add_audit_event(
            db,
            action="question_analysis_requested",
            outcome="success",
            actor_user_id=actor.id,
            target_user_id=actor.id,
            details={"status": analysis.status},
        )
        db.commit()
        db.refresh(analysis)
        return analysis
    except SQLAlchemyError as error:
        db.rollback()
        raise QuestionPersistenceError from error


def list_review_questions(db: Session) -> list[QuestionDetail]:
    """Return the unassigned queue of questions awaiting a public response."""

    try:
        questions = list(
            db.scalars(
                select(VaccineQuestion)
                .where(
                    VaccineQuestion.status.in_(
                        (
                            QuestionStatus.PENDING.value,
                            QuestionStatus.AWAITING_REVIEW.value,
                        )
                    )
                )
                .order_by(VaccineQuestion.created_at.asc(), VaccineQuestion.id.asc())
            )
        )
        return [_question_detail(db, question) for question in questions]
    except SQLAlchemyError as error:
        db.rollback()
        raise QuestionPersistenceError from error


def get_review_question_detail(
    db: Session,
    *,
    question_id: UUID,
) -> QuestionDetail | None:
    """Return only questions still requiring a professional response."""

    try:
        question = db.scalar(
            select(VaccineQuestion).where(
                VaccineQuestion.id == question_id,
                VaccineQuestion.status.in_(
                    (
                        QuestionStatus.PENDING.value,
                        QuestionStatus.AWAITING_REVIEW.value,
                    )
                ),
            )
        )
        return _question_detail(db, question) if question is not None else None
    except SQLAlchemyError as error:
        db.rollback()
        raise QuestionPersistenceError from error


def publish_professional_response(
    db: Session,
    *,
    actor: User,
    question_id: UUID,
    response_text: str,
) -> ProfessionalResponse | None:
    """Publish a new answer while retaining every previous response row."""

    try:
        question = db.scalar(
            select(VaccineQuestion)
            .where(VaccineQuestion.id == question_id)
            .with_for_update()
        )
        if question is None:
            return None

        db.execute(
            update(ProfessionalResponse)
            .where(
                ProfessionalResponse.question_id == question_id,
                ProfessionalResponse.status
                == ProfessionalResponseStatus.PUBLISHED.value,
            )
            .values(status=ProfessionalResponseStatus.SUPERSEDED.value)
        )
        response = ProfessionalResponse(
            question_id=question_id,
            professional_user_id=actor.id,
            response=response_text,
            status=ProfessionalResponseStatus.PUBLISHED.value,
        )
        db.add(response)
        question.status = QuestionStatus.RESPONDED.value
        add_audit_event(
            db,
            action="question_professional_response_published",
            outcome="success",
            actor_user_id=actor.id,
            target_user_id=question.asked_by_user_id,
            details={"status": ProfessionalResponseStatus.PUBLISHED.value},
        )
        db.commit()
        db.refresh(response)
        return response
    except SQLAlchemyError as error:
        db.rollback()
        raise QuestionPersistenceError from error
