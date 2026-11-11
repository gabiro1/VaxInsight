from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.dependencies import require_permissions
from app.api.docs import documented_responses
from app.core.config import settings
from app.core.permissions import Permission
from app.database.dependencies import get_db
from app.models.user import User
from app.schemas.questions import (
    ProfessionalResponseCreate,
    ProfessionalResponseResponse,
    QuestionAnalysisResponse,
    QuestionCreate,
    QuestionDetailResponse,
    VaccineQuestionResponse,
)
from app.services.questions import (
    create_question,
    get_owned_question_detail,
    get_review_question_detail,
    list_owned_questions,
    list_review_questions,
    publish_professional_response,
    request_question_analysis,
)
from app.services.rate_limit import enforce_rate_limit

router = APIRouter()
question_create_dependency = require_permissions(Permission.QUESTION_CREATE)
question_read_dependency = require_permissions(Permission.QUESTION_READ_OWN)
question_detail_dependency = require_permissions(
    Permission.QUESTION_READ_OWN,
    Permission.VACCINE_ANALYSIS_READ,
)
question_analysis_dependency = require_permissions(
    Permission.QUESTION_READ_OWN,
    Permission.VACCINE_ANALYSIS_REQUEST,
)
question_review_dependency = require_permissions(Permission.QUESTION_REVIEW)


def _question_detail_response(detail) -> QuestionDetailResponse:
    return QuestionDetailResponse(
        question=VaccineQuestionResponse.model_validate(detail.question),
        latest_analysis=(
            QuestionAnalysisResponse.model_validate(detail.latest_analysis)
            if detail.latest_analysis is not None
            else None
        ),
        latest_professional_response=(
            ProfessionalResponseResponse.model_validate(
                detail.latest_professional_response
            )
            if detail.latest_professional_response is not None
            else None
        ),
    )


@router.post(
    "/questions",
    response_model=QuestionDetailResponse,
    status_code=status.HTTP_201_CREATED,
    response_description="The created question and its first analysis run.",
    summary="Ask a vaccine question",
    description=(
        "Create an owner-scoped question and append one immutable analysis run through "
        "the configured provider boundary. If no approved provider is configured, the "
        "run is recorded as unavailable and the question awaits professional review."
    ),
    responses=documented_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        status.HTTP_429_TOO_MANY_REQUESTS,
        status.HTTP_503_SERVICE_UNAVAILABLE,
    ),
    tags=["Questions"],
)
def ask_question(
    request: Request,
    question_data: QuestionCreate,
    current_user: User = Depends(question_create_dependency),
    db: Session = Depends(get_db),
):
    enforce_rate_limit(
        db,
        request,
        scope="question_write",
        limit=settings.QUESTION_RATE_LIMIT,
        identity=str(current_user.id),
    )
    detail = create_question(
        db,
        actor=current_user,
        content=question_data.content,
        language=question_data.language.value,
        topic=question_data.topic,
    )
    return _question_detail_response(detail)


@router.get(
    "/questions",
    response_model=list[VaccineQuestionResponse],
    status_code=status.HTTP_200_OK,
    response_description="Questions owned by the authenticated account.",
    summary="List owned questions",
    description="Return only questions asked by the authenticated account.",
    responses=documented_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_503_SERVICE_UNAVAILABLE,
    ),
    tags=["Questions"],
)
def list_questions(
    current_user: User = Depends(question_read_dependency),
    db: Session = Depends(get_db),
):
    return list_owned_questions(db, owner_id=current_user.id)


@router.get(
    "/questions/{question_id}",
    response_model=QuestionDetailResponse,
    status_code=status.HTTP_200_OK,
    response_description="The owner-safe question detail.",
    summary="Get an owned question",
    description=(
        "Return the question, latest analysis run, and latest published professional "
        "response only when the authenticated account owns the question."
    ),
    responses=documented_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
        status.HTTP_503_SERVICE_UNAVAILABLE,
    ),
    tags=["Questions"],
)
def get_question(
    question_id: UUID,
    current_user: User = Depends(question_detail_dependency),
    db: Session = Depends(get_db),
):
    detail = get_owned_question_detail(
        db,
        question_id=question_id,
        owner_id=current_user.id,
    )
    if detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found",
        )
    return _question_detail_response(detail)


@router.post(
    "/questions/{question_id}/analysis",
    response_model=QuestionAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    response_description="The newly created immutable analysis run.",
    summary="Request another question analysis",
    description=(
        "Append another analysis run through the same explicit provider boundary. An "
        "unavailable provider never creates fabricated AI or medical output."
    ),
    responses=documented_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
        status.HTTP_429_TOO_MANY_REQUESTS,
        status.HTTP_503_SERVICE_UNAVAILABLE,
    ),
    tags=["Questions"],
)
def request_analysis(
    question_id: UUID,
    request: Request,
    current_user: User = Depends(question_analysis_dependency),
    db: Session = Depends(get_db),
):
    enforce_rate_limit(
        db,
        request,
        scope="question_analysis",
        limit=settings.QUESTION_RATE_LIMIT,
        identity=str(current_user.id),
    )
    analysis = request_question_analysis(
        db,
        actor=current_user,
        question_id=question_id,
    )
    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found",
        )
    return analysis


@router.get(
    "/review/questions",
    response_model=list[QuestionDetailResponse],
    status_code=status.HTTP_200_OK,
    response_description="Questions awaiting professional response.",
    summary="List questions for professional review",
    description=(
        "Return the unassigned Health Expert queue. The question, latest analysis, and "
        "latest published response are available only to Health Experts."
    ),
    responses=documented_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_503_SERVICE_UNAVAILABLE,
    ),
    tags=["Question Reviews"],
)
def list_questions_for_review(
    _current_user: User = Depends(question_review_dependency),
    db: Session = Depends(get_db),
):
    return [_question_detail_response(item) for item in list_review_questions(db)]


@router.get(
    "/review/questions/{question_id}",
    response_model=QuestionDetailResponse,
    status_code=status.HTTP_200_OK,
    response_description="One question awaiting professional response.",
    summary="Get a question for professional review",
    description="Return one queue item and its separate analysis output to a Health Expert.",
    responses=documented_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
        status.HTTP_503_SERVICE_UNAVAILABLE,
    ),
    tags=["Question Reviews"],
)
def get_question_for_review(
    question_id: UUID,
    _current_user: User = Depends(question_review_dependency),
    db: Session = Depends(get_db),
):
    detail = get_review_question_detail(db, question_id=question_id)
    if detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question is not awaiting professional review",
        )
    return _question_detail_response(detail)


@router.post(
    "/review/questions/{question_id}/response",
    response_model=ProfessionalResponseResponse,
    status_code=status.HTTP_201_CREATED,
    response_description="The newly published professional response.",
    summary="Publish a professional response",
    description=(
        "Publish a public professional answer, mark prior published answers as "
        "superseded, preserve the prior rows, and mark the question responded."
    ),
    responses=documented_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        status.HTTP_503_SERVICE_UNAVAILABLE,
    ),
    tags=["Question Reviews"],
)
def publish_response(
    question_id: UUID,
    response_data: ProfessionalResponseCreate,
    current_user: User = Depends(question_review_dependency),
    db: Session = Depends(get_db),
):
    response = publish_professional_response(
        db,
        actor=current_user,
        question_id=question_id,
        response_text=response_data.response,
    )
    if response is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found",
        )
    return response
