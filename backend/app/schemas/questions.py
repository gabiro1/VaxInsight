import unicodedata
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.questions import (
    ProfessionalResponseStatus,
    QuestionAnalysisStatus,
    QuestionStatus,
)
from app.models.vaccine_content import ContentLanguage

MAX_QUESTION_CONTENT_LENGTH = 10_000


def _question_text(value: str, *, max_length: int) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError("text must contain non-whitespace characters")
    if any(
        unicodedata.category(character) == "Cc" and character not in "\t\n\r"
        for character in normalized
    ):
        raise ValueError("text contains unsupported control characters")
    if len(normalized) > max_length:
        raise ValueError(f"text must be at most {max_length} characters")
    return normalized


class QuestionCreate(BaseModel):
    content: str = Field(
        min_length=1,
        max_length=MAX_QUESTION_CONTENT_LENGTH,
    )
    language: ContentLanguage
    topic: str | None = Field(default=None, min_length=1, max_length=255)

    model_config = ConfigDict(extra="forbid")

    @field_validator("content")
    @classmethod
    def normalize_content(cls, value: str) -> str:
        return _question_text(value, max_length=MAX_QUESTION_CONTENT_LENGTH)

    @field_validator("topic")
    @classmethod
    def normalize_topic(cls, value: str | None) -> str | None:
        return _question_text(value, max_length=255) if value is not None else None


class VaccineQuestionResponse(BaseModel):
    id: UUID
    asked_by_user_id: UUID
    content: str
    language: Literal["rw", "en"]
    topic: str | None
    status: QuestionStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuestionAnalysisResponse(BaseModel):
    id: UUID
    question_id: UUID
    status: QuestionAnalysisStatus
    provider: str | None
    model: str | None
    dataset_version: str | None
    category: str | None
    answer: str | None
    explanation: str | None
    explanation_method: str | None
    confidence: float | None = Field(default=None, ge=0, le=1)
    limitations: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProfessionalResponseCreate(BaseModel):
    response: str = Field(min_length=1, max_length=10_000)

    model_config = ConfigDict(extra="forbid")

    @field_validator("response")
    @classmethod
    def normalize_response(cls, value: str) -> str:
        return _question_text(value, max_length=10_000)


class ProfessionalResponseResponse(BaseModel):
    id: UUID
    question_id: UUID
    professional_user_id: UUID | None
    response: str
    status: ProfessionalResponseStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuestionDetailResponse(BaseModel):
    question: VaccineQuestionResponse
    latest_analysis: QuestionAnalysisResponse | None
    latest_professional_response: ProfessionalResponseResponse | None
