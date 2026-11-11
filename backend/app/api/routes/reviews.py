from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import require_any_permissions, require_permissions
from app.api.docs import documented_responses
from app.core.permissions import Permission, has_permission
from app.database.dependencies import get_db
from app.models.narrative import NarrativeStatus
from app.models.review import AssignmentStatus, ReviewOutcome, ReviewStatus
from app.models.user import User
from app.schemas.review import (
    AssignedNarrativeResponse,
    NarrativeAssignmentCreate,
    NarrativeAssignmentPageResponse,
    NarrativeAssignmentReassign,
    NarrativeAssignmentResponse,
    NarrativeAssignmentRevoke,
    NarrativeReviewHistoryResponse,
    NarrativeReviewResponse,
    ReviewCreate,
    ReviewEvidenceResponse,
    ReviewPageQuery,
    ReviewStatusUpdate,
)
from app.services.reviews import (
    AssignmentStateConflict,
    ReviewerNotEligible,
    ReviewStateConflict,
    create_assignment,
    get_visible_assignment,
    list_assignments,
    list_review_history,
    reassign_assignment,
    revoke_assignment,
    submit_review,
    update_review_status,
)

router = APIRouter()
assignment_manage_dependency = require_permissions(Permission.NARRATIVE_ASSIGN)
reviewer_read_dependency = require_any_permissions(
    Permission.NARRATIVE_ASSIGN,
    Permission.NARRATIVE_READ_ASSIGNED,
)
review_status_dependency = require_any_permissions(
    Permission.NARRATIVE_ASSIGN,
    Permission.NARRATIVE_REVIEW,
)
review_submit_dependency = require_permissions(Permission.NARRATIVE_REVIEW)


def _assignment_response(
    assignment,
    *,
    narrative=None,
) -> NarrativeAssignmentResponse:
    narrative_response = None
    if narrative is not None:
        narrative_response = AssignedNarrativeResponse(
            id=narrative.id,
            content=narrative.content,
            status=NarrativeStatus(narrative.status),
            version=narrative.version,
            submitted_at=narrative.submitted_at,
            updated_at=narrative.updated_at,
        )
    return NarrativeAssignmentResponse(
        id=assignment.id,
        narrative_id=assignment.narrative_id,
        reviewer_id=assignment.reviewer_id,
        assigned_by_user_id=assignment.assigned_by_user_id,
        status=AssignmentStatus(assignment.status),
        review_status=ReviewStatus(assignment.review_status),
        assigned_at=assignment.assigned_at,
        updated_at=assignment.updated_at,
        revoked_at=assignment.revoked_at,
        revoked_by_user_id=assignment.revoked_by_user_id,
        revoked_reason=assignment.revoked_reason,
        narrative=narrative_response,
    )


def _review_response(review, evidence) -> NarrativeReviewResponse:
    return NarrativeReviewResponse(
        id=review.id,
        assignment_id=review.assignment_id,
        narrative_id=review.narrative_id,
        reviewer_id=review.reviewer_id,
        outcome=ReviewOutcome(review.outcome),
        notes=review.notes,
        reviewed_at=review.reviewed_at,
        evidence=[
            ReviewEvidenceResponse(
                id=item.id,
                source_title=item.source_title,
                publisher=item.publisher,
                url=item.url,
                publication_date=item.publication_date,
                accessed_at=item.accessed_at,
                relevance=item.relevance,
                created_at=item.created_at,
            )
            for item in evidence
        ],
    )


def _is_assignment_manager(user: User) -> bool:
    return has_permission(user, Permission.NARRATIVE_ASSIGN)


@router.post(
    "/narratives/{narrative_id}/assignment",
    response_model=NarrativeAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    response_description="The created narrative assignment without narrative content.",
    summary="Assign a narrative for review",
    description=(
        "Assign a submitted narrative to one active reviewer. Assignment managers "
        "receive metadata only; the reviewer receives content through the assigned "
        "review endpoint."
    ),
    responses=documented_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
        status.HTTP_409_CONFLICT,
        status.HTTP_422_UNPROCESSABLE_CONTENT,
    ),
    tags=["Narrative Reviews"],
)
def assign_narrative(
    narrative_id: UUID,
    assignment_data: NarrativeAssignmentCreate,
    current_user: User = Depends(assignment_manage_dependency),
    db: Session = Depends(get_db),
):
    try:
        assignment = create_assignment(
            db,
            actor=current_user,
            narrative_id=narrative_id,
            reviewer_id=assignment_data.reviewer_id,
        )
    except ReviewerNotEligible:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Reviewer is not eligible for assignment",
        ) from None
    except AssignmentStateConflict as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from None

    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Narrative not found",
        )
    return _assignment_response(assignment)


@router.post(
    "/narratives/{narrative_id}/assignment/reassign",
    response_model=NarrativeAssignmentResponse,
    status_code=status.HTTP_200_OK,
    response_description="The replacement assignment without narrative content.",
    summary="Reassign a narrative",
    description=(
        "Revoke the active assignment, preserve its history, and create a new "
        "pending assignment for an eligible reviewer."
    ),
    responses=documented_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
        status.HTTP_409_CONFLICT,
        status.HTTP_422_UNPROCESSABLE_CONTENT,
    ),
    tags=["Narrative Reviews"],
)
def reassign_narrative(
    narrative_id: UUID,
    assignment_data: NarrativeAssignmentReassign,
    current_user: User = Depends(assignment_manage_dependency),
    db: Session = Depends(get_db),
):
    try:
        assignment = reassign_assignment(
            db,
            actor=current_user,
            narrative_id=narrative_id,
            reviewer_id=assignment_data.reviewer_id,
            reason=assignment_data.reason,
        )
    except ReviewerNotEligible:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Reviewer is not eligible for assignment",
        ) from None
    except AssignmentStateConflict as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from None

    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active narrative assignment not found",
        )
    return _assignment_response(assignment)


@router.post(
    "/narratives/{narrative_id}/assignment/revoke",
    response_model=NarrativeAssignmentResponse,
    status_code=status.HTTP_200_OK,
    response_description="The revoked assignment without narrative content.",
    summary="Revoke a narrative assignment",
    description=(
        "Revoke the active reviewer assignment with a required reason. Existing "
        "assignment and review history remains available to authorized managers."
    ),
    responses=documented_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
    ),
    tags=["Narrative Reviews"],
)
def revoke_narrative_assignment(
    narrative_id: UUID,
    assignment_data: NarrativeAssignmentRevoke,
    current_user: User = Depends(assignment_manage_dependency),
    db: Session = Depends(get_db),
):
    assignment = revoke_assignment(
        db,
        actor=current_user,
        narrative_id=narrative_id,
        reason=assignment_data.reason,
    )
    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active narrative assignment not found",
        )
    return _assignment_response(assignment)


@router.get(
    "/reviews/assignments",
    response_model=NarrativeAssignmentPageResponse,
    status_code=status.HTTP_200_OK,
    response_description="A page of assignment metadata or assigned narratives.",
    summary="List review assignments",
    description=(
        "Reviewers receive only their active assignments with narrative content. "
        "Assignment managers receive active assignment metadata without content."
    ),
    responses=documented_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_422_UNPROCESSABLE_CONTENT,
    ),
    tags=["Narrative Reviews"],
)
def list_review_assignments(
    query: ReviewPageQuery = Depends(),
    current_user: User = Depends(reviewer_read_dependency),
    db: Session = Depends(get_db),
):
    can_manage = _is_assignment_manager(current_user)
    result = list_assignments(
        db,
        reviewer_id=None if can_manage else current_user.id,
        page=query.page,
        page_size=query.page_size,
        include_narratives=not can_manage,
    )
    return NarrativeAssignmentPageResponse(
        items=[
            _assignment_response(
                assignment,
                narrative=result.narratives.get(assignment.narrative_id),
            )
            for assignment in result.assignments
        ],
        page=query.page,
        page_size=query.page_size,
        total=result.total,
        total_pages=(result.total + query.page_size - 1) // query.page_size,
    )


@router.get(
    "/reviews/assignments/{assignment_id}",
    response_model=NarrativeAssignmentResponse,
    status_code=status.HTTP_200_OK,
    response_description="Assignment metadata and, for the reviewer, assigned content.",
    summary="Get a review assignment",
    description=(
        "Return assigned narrative content only to its active reviewer. Assignment "
        "managers receive assignment metadata without narrative content."
    ),
    responses=documented_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
        status.HTTP_422_UNPROCESSABLE_CONTENT,
    ),
    tags=["Narrative Reviews"],
)
def get_review_assignment(
    assignment_id: UUID,
    current_user: User = Depends(reviewer_read_dependency),
    db: Session = Depends(get_db),
):
    can_manage = _is_assignment_manager(current_user)
    result = get_visible_assignment(
        db,
        assignment_id=assignment_id,
        reviewer_id=None if can_manage else current_user.id,
        can_manage_assignments=can_manage,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review assignment not found",
        )
    assignment, narrative = result
    return _assignment_response(assignment, narrative=narrative)


@router.get(
    "/reviews/assignments/{assignment_id}/status",
    response_model=NarrativeAssignmentResponse,
    status_code=status.HTTP_200_OK,
    response_description="The current assignment and review status.",
    summary="Get review status",
    description=(
        "Return assignment and review status without exposing narrative content to "
        "assignment managers."
    ),
    responses=documented_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
        status.HTTP_422_UNPROCESSABLE_CONTENT,
    ),
    tags=["Narrative Reviews"],
)
def get_review_status(
    assignment_id: UUID,
    current_user: User = Depends(reviewer_read_dependency),
    db: Session = Depends(get_db),
):
    can_manage = _is_assignment_manager(current_user)
    result = get_visible_assignment(
        db,
        assignment_id=assignment_id,
        reviewer_id=None if can_manage else current_user.id,
        can_manage_assignments=can_manage,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review assignment not found",
        )
    assignment, _narrative = result
    return _assignment_response(assignment)


@router.post(
    "/reviews/assignments/{assignment_id}/status",
    response_model=NarrativeAssignmentResponse,
    status_code=status.HTTP_200_OK,
    response_description="The updated explicit review status.",
    summary="Change review status",
    description=(
        "Apply an explicit human status transition. Escalation is preserved and is "
        "never resolved automatically."
    ),
    responses=documented_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
        status.HTTP_409_CONFLICT,
        status.HTTP_422_UNPROCESSABLE_CONTENT,
    ),
    tags=["Narrative Reviews"],
)
def change_review_status(
    assignment_id: UUID,
    status_data: ReviewStatusUpdate,
    current_user: User = Depends(review_status_dependency),
    db: Session = Depends(get_db),
):
    can_manage = _is_assignment_manager(current_user)
    try:
        assignment = update_review_status(
            db,
            actor=current_user,
            assignment_id=assignment_id,
            status=status_data.status,
            reason=status_data.reason,
            can_manage_assignments=can_manage,
        )
    except (AssignmentStateConflict, ReviewStateConflict) as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from None

    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review assignment not found",
        )
    return _assignment_response(assignment)


@router.post(
    "/reviews/assignments/{assignment_id}/review",
    response_model=NarrativeReviewResponse,
    status_code=status.HTTP_201_CREATED,
    response_description="The immutable submitted review record.",
    summary="Submit a narrative review",
    description=(
        "Append one structured human review with optional evidence references. The "
        "original narrative and prior reviews are never modified."
    ),
    responses=documented_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
        status.HTTP_409_CONFLICT,
        status.HTTP_422_UNPROCESSABLE_CONTENT,
    ),
    tags=["Narrative Reviews"],
)
def submit_narrative_review(
    assignment_id: UUID,
    review_data: ReviewCreate,
    current_user: User = Depends(review_submit_dependency),
    db: Session = Depends(get_db),
):
    try:
        result = submit_review(
            db,
            actor=current_user,
            assignment_id=assignment_id,
            outcome=review_data.outcome,
            notes=review_data.notes,
            evidence=review_data.evidence,
        )
    except ReviewStateConflict as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from None

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review assignment not found",
        )
    return _review_response(result.review, result.evidence)


@router.get(
    "/reviews/assignments/{assignment_id}/history",
    response_model=NarrativeReviewHistoryResponse,
    status_code=status.HTTP_200_OK,
    response_description="Immutable review history and evidence references.",
    summary="List review history",
    description=(
        "Return immutable review records for the active assigned reviewer or an "
        "authorized assignment manager. Narrative owners cannot access this history."
    ),
    responses=documented_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
        status.HTTP_422_UNPROCESSABLE_CONTENT,
    ),
    tags=["Narrative Reviews"],
)
def get_review_history(
    assignment_id: UUID,
    query: ReviewPageQuery = Depends(),
    current_user: User = Depends(reviewer_read_dependency),
    db: Session = Depends(get_db),
):
    can_manage = _is_assignment_manager(current_user)
    result = list_review_history(
        db,
        assignment_id=assignment_id,
        reviewer_id=None if can_manage else current_user.id,
        can_manage_assignments=can_manage,
        page=query.page,
        page_size=query.page_size,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review assignment not found",
        )
    return NarrativeReviewHistoryResponse(
        items=[
            _review_response(review, result.evidence.get(review.id, []))
            for review in result.reviews
        ],
        page=query.page,
        page_size=query.page_size,
        total=result.total,
        total_pages=(result.total + query.page_size - 1) // query.page_size,
    )
