from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import require_permissions
from app.api.docs import documented_responses
from app.core.permissions import Permission
from app.database.dependencies import get_db
from app.models.user import User
from app.models.vaccine_content import ContentLanguage
from app.schemas.vaccine_content import (
    VaccineContentCreate,
    VaccineContentResponse,
)
from app.services.vaccine_content import (
    VaccineContentConflict,
    create_vaccine_content,
    get_published_content,
    list_published_content,
)

router = APIRouter()
content_read_dependency = require_permissions(Permission.VACCINE_CONTENT_READ)
content_manage_dependency = require_permissions(Permission.VACCINE_CONTENT_MANAGE)


@router.get(
    "/vaccine-content",
    response_model=list[VaccineContentResponse],
    status_code=status.HTTP_200_OK,
    response_description="Published official vaccine content.",
    summary="List published vaccine content",
    description=(
        "Return only administrator-approved published content. Results may be "
        "filtered by the supported language and content category."
    ),
    responses=documented_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        status.HTTP_503_SERVICE_UNAVAILABLE,
    ),
    tags=["Vaccine Content"],
)
def list_vaccine_content(
    language: ContentLanguage | None = Query(
        default=None,
        description="Filter by supported content language: rw or en.",
    ),
    category: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
        description="Filter by the exact content category.",
    ),
    _current_user: User = Depends(content_read_dependency),
    db: Session = Depends(get_db),
):
    return list_published_content(db, language=language, category=category)


@router.get(
    "/vaccine-content/{content_id}",
    response_model=VaccineContentResponse,
    status_code=status.HTTP_200_OK,
    response_description="One published official vaccine content record.",
    summary="Get published vaccine content",
    description="Return one administrator-approved published registry record.",
    responses=documented_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        status.HTTP_503_SERVICE_UNAVAILABLE,
    ),
    tags=["Vaccine Content"],
)
def get_vaccine_content(
    content_id: UUID,
    _current_user: User = Depends(content_read_dependency),
    db: Session = Depends(get_db),
):
    content = get_published_content(db, content_id=content_id)
    if content is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vaccine content not found",
        )
    return content


@router.post(
    "/admin/vaccine-content",
    response_model=VaccineContentResponse,
    status_code=status.HTTP_201_CREATED,
    response_description="The created draft or published vaccine content record.",
    summary="Create vaccine content",
    description=(
        "Create administrator-managed content and reuse an identical source. Draft "
        "records remain hidden from the published read endpoints; publishing records "
        "the authenticated administrator and approval timestamp."
    ),
    responses=documented_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_409_CONFLICT,
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        status.HTTP_503_SERVICE_UNAVAILABLE,
    ),
    tags=["Vaccine Content"],
)
def create_content(
    content_data: VaccineContentCreate,
    current_user: User = Depends(content_manage_dependency),
    db: Session = Depends(get_db),
):
    source = content_data.source
    # VaccineContentCreate guarantees a normalized source in its model validator.
    try:
        return create_vaccine_content(
            db,
            actor=current_user,
            source_authority=source.authority,
            source_name=source.name,
            source_url=str(source.url),
            source_jurisdiction=source.jurisdiction,
            language=content_data.language,
            category=content_data.category,
            title=content_data.title,
            summary=content_data.summary,
            body=content_data.body,
            version=content_data.version,
            status=content_data.status,
        )
    except VaccineContentConflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This vaccine content version already exists",
        ) from None
