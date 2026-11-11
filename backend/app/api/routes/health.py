from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.docs import documented_responses
from app.core.config import settings
from app.database.dependencies import get_db
from app.schemas.common import DatabaseHealthResponse, HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    response_description="Application health information.",
    summary="Check application health",
    description="Return a lightweight liveness response for the VaxInsight API.",
    tags=["Health"],
)
async def health_check():
    return {
        "status": "healthy",
        "application": settings.APP_NAME,
        "message": f"{settings.APP_NAME} API is running successfully",
    }


@router.get(
    "/health/database",
    response_model=DatabaseHealthResponse,
    status_code=status.HTTP_200_OK,
    response_description="PostgreSQL connectivity information.",
    summary="Check database health",
    description="Verify that the configured PostgreSQL database can execute a query.",
    responses=documented_responses(status.HTTP_503_SERVICE_UNAVAILABLE),
    tags=["Health"],
)
def database_health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))

    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database temporarily unavailable",
        ) from None

    return {
        "status": "healthy",
        "database": "connected",
        "message": f"{settings.APP_NAME} successfully connected to PostgreSQL",
    }
