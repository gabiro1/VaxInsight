from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.api.dependencies import require_permissions
from app.api.docs import documented_responses
from app.core.config import settings
from app.core.permissions import Permission
from app.database.dependencies import get_db
from app.models.user import User
from app.schemas.narrative import (
    NarrativeCreate,
    NarrativeHistoryQuery,
    NarrativeListQuery,
    NarrativePageResponse,
    NarrativeResponse,
    NarrativeRevisionPageResponse,
    NarrativeUpdate,
)
from app.services.narratives import (
    NarrativeNotEditable,
    create_narrative,
    get_owned_narrative,
    list_owned_narrative_revisions,
    list_owned_narratives,
    update_owned_narrative,
)
from app.services.rate_limit import enforce_rate_limit

router = APIRouter()
narrative_create_dependency = require_permissions(Permission.NARRATIVE_CREATE)
narrative_read_own_dependency = require_permissions(Permission.NARRATIVE_READ_OWN)
narrative_update_own_dependency = require_permissions(Permission.NARRATIVE_UPDATE_OWN)


def get_narrative_list_query(
    page: int = Query(default=1, ge=1, le=10_000),
    page_size: int = Query(default=20, ge=1, le=100),
    narrative_status: str | None = Query(
        default=None,
        alias="status",
        description="Filter by the supported narrative lifecycle state.",
    ),
    submitted_after: datetime | None = Query(default=None),
    submitted_before: datetime | None = Query(default=None),
) -> NarrativeListQuery:
    try:
        return NarrativeListQuery(
            page=page,
            page_size=page_size,
            status=narrative_status,
            submitted_after=submitted_after,
            submitted_before=submitted_before,
        )
    except ValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Invalid narrative filters",
        ) from error


def get_narrative_history_query(
    page: int = Query(default=1, ge=1, le=10_000),
    page_size: int = Query(default=20, ge=1, le=100),
) -> NarrativeHistoryQuery:
    return NarrativeHistoryQuery(page=page, page_size=page_size)


@router.post(
    "/narratives",
    response_model=NarrativeResponse,
    status_code=status.HTTP_201_CREATED,
    response_description="The owner-scoped narrative record.",
    summary="Submit a narrative record",
    description=(
        "Store a validated narrative for the authenticated account. This neutral "
        "foundation does not classify, fact-check, or generate model output."
    ),
    responses=documented_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_422_UNPROCESSABLE_CONTENT,
    ),
    tags=["Narratives"],
)
def submit_narrative(
    request: Request,
    narrative_data: NarrativeCreate,
    current_user: User = Depends(narrative_create_dependency),
    db: Session = Depends(get_db),
):
    enforce_rate_limit(
        db,
        request,
        scope="narrative_write",
        limit=settings.NARRATIVE_RATE_LIMIT,
        identity=str(current_user.id),
    )
    return create_narrative(
        db,
        actor=current_user,
        content=narrative_data.content,
    )


@router.get(
    "/narratives",
    response_model=NarrativePageResponse,
    status_code=status.HTTP_200_OK,
    response_description="The authenticated user's narrative page.",
    summary="List owned narrative records",
    description=(
        "Return only narratives submitted by the authenticated account, with "
        "database-side pagination and neutral filters."
    ),
    responses=documented_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_422_UNPROCESSABLE_CONTENT,
    ),
    tags=["Narratives"],
)
def list_narratives(
    query: NarrativeListQuery = Depends(get_narrative_list_query),
    current_user: User = Depends(narrative_read_own_dependency),
    db: Session = Depends(get_db),
):
    result = list_owned_narratives(
        db,
        owner_id=current_user.id,
        page=query.page,
        page_size=query.page_size,
        status=query.status,
        submitted_after=query.submitted_after,
        submitted_before=query.submitted_before,
    )
    return NarrativePageResponse(
        items=result.narratives,
        page=query.page,
        page_size=query.page_size,
        total=result.total,
        total_pages=(result.total + query.page_size - 1) // query.page_size,
    )


@router.get(
    "/narratives/{narrative_id}/history",
    response_model=NarrativeRevisionPageResponse,
    status_code=status.HTTP_200_OK,
    response_description="The owner-visible narrative revision history.",
    summary="List narrative history",
    description=(
        "Return immutable content revisions for a narrative owned by the "
        "authenticated account. Health Expert and administrator access is not implied."
    ),
    responses=documented_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_404_NOT_FOUND,
        status.HTTP_422_UNPROCESSABLE_CONTENT,
    ),
    tags=["Narratives"],
)
def list_narrative_history(
    narrative_id: UUID,
    query: NarrativeHistoryQuery = Depends(get_narrative_history_query),
    current_user: User = Depends(narrative_read_own_dependency),
    db: Session = Depends(get_db),
):
    result = list_owned_narrative_revisions(
        db,
        owner_id=current_user.id,
        narrative_id=narrative_id,
        page=query.page,
        page_size=query.page_size,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Narrative not found",
        )
    return NarrativeRevisionPageResponse(
        items=result.revisions,
        page=query.page,
        page_size=query.page_size,
        total=result.total,
        total_pages=(result.total + query.page_size - 1) // query.page_size,
    )


@router.get(
    "/narratives/{narrative_id}",
    response_model=NarrativeResponse,
    status_code=status.HTTP_200_OK,
    response_description="The requested owner-scoped narrative record.",
    summary="Get an owned narrative",
    description=(
        "Return a narrative only when it belongs to the authenticated account. "
        "No model prediction or health conclusion is included."
    ),
    responses=documented_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_404_NOT_FOUND,
        status.HTTP_422_UNPROCESSABLE_CONTENT,
    ),
    tags=["Narratives"],
)
def get_narrative(
    narrative_id: UUID,
    current_user: User = Depends(narrative_read_own_dependency),
    db: Session = Depends(get_db),
):
    narrative = get_owned_narrative(
        db,
        narrative_id=narrative_id,
        owner_id=current_user.id,
    )
    if narrative is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Narrative not found",
        )
    return narrative


@router.patch(
    "/narratives/{narrative_id}",
    response_model=NarrativeResponse,
    status_code=status.HTTP_200_OK,
    response_description="The updated owner-scoped narrative record.",
    summary="Update an owned narrative",
    description=(
        "Update narrative content while retaining the neutral submitted state and "
        "appending an immutable revision. Lifecycle transitions are not exposed."
    ),
    responses=documented_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_404_NOT_FOUND,
        status.HTTP_409_CONFLICT,
        status.HTTP_422_UNPROCESSABLE_CONTENT,
    ),
    tags=["Narratives"],
)
def update_narrative(
    narrative_id: UUID,
    request: Request,
    narrative_data: NarrativeUpdate,
    current_user: User = Depends(narrative_update_own_dependency),
    db: Session = Depends(get_db),
):
    enforce_rate_limit(
        db,
        request,
        scope="narrative_write",
        limit=settings.NARRATIVE_RATE_LIMIT,
        identity=str(current_user.id),
    )
    try:
        narrative = update_owned_narrative(
            db,
            actor=current_user,
            narrative_id=narrative_id,
            content=narrative_data.content,
        )
    except NarrativeNotEditable:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Narrative cannot be updated in its current state",
        ) from None

    if narrative is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Narrative not found",
        )
    return narrative
