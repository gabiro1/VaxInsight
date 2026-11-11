from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import require_permissions
from app.api.docs import documented_responses
from app.core.permissions import Permission
from app.database.dependencies import get_db
from app.models.user import User
from app.schemas.dashboard import PersonalDashboardSummaryResponse
from app.services.dashboard import get_personal_dashboard_summary

router = APIRouter()
personal_dashboard_dependency = require_permissions(Permission.NARRATIVE_READ_OWN)


@router.get(
    "/dashboard/summary",
    response_model=PersonalDashboardSummaryResponse,
    status_code=status.HTTP_200_OK,
    response_description="Personal activity and owned narrative status summary.",
    summary="Get the personal dashboard summary",
    description=(
        "Return metrics and recent narratives owned by the authenticated account. "
        "Review data is limited to status and never includes reviewer notes, "
        "outcomes, evidence, or other users' records."
    ),
    responses=documented_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    ),
    tags=["Dashboard"],
)
def get_personal_dashboard(
    current_user: User = Depends(personal_dashboard_dependency),
    db: Session = Depends(get_db),
):
    return get_personal_dashboard_summary(db, owner_id=current_user.id)
