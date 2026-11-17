from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.api.docs import documented_responses
from app.database.dependencies import get_db
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.notifications import (
    NotificationDeviceRegistration,
    NotificationDeviceResponse,
    NotificationPreferencesResponse,
    NotificationPreferencesUpdate,
)
from app.services.notifications import (
    NotificationPersistenceError,
    get_or_create_notification_preferences,
    register_notification_device,
    unregister_notification_device,
    update_notification_preferences,
)

router = APIRouter()


@router.get(
    "/notifications/preferences",
    response_model=NotificationPreferencesResponse,
    status_code=status.HTTP_200_OK,
    response_description="The authenticated user's notification preferences.",
    summary="Get notification preferences",
    description=(
        "Return the authenticated user's cadence for new published vaccine-content "
        "notifications, creating the daily default when necessary."
    ),
    responses=documented_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_503_SERVICE_UNAVAILABLE,
    ),
    tags=["Notifications"],
)
def get_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return get_or_create_notification_preferences(db, user_id=current_user.id)
    except NotificationPersistenceError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Notification preferences are temporarily unavailable",
        ) from None


@router.patch(
    "/notifications/preferences",
    response_model=NotificationPreferencesResponse,
    status_code=status.HTTP_200_OK,
    response_description="The updated notification preferences.",
    summary="Update notification preferences",
    description="Set the authenticated user's notification cadence.",
    responses=documented_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        status.HTTP_503_SERVICE_UNAVAILABLE,
    ),
    tags=["Notifications"],
)
def update_preferences(
    preference_data: NotificationPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return update_notification_preferences(
            db,
            user_id=current_user.id,
            frequency=preference_data.frequency,
        )
    except NotificationPersistenceError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Notification preferences are temporarily unavailable",
        ) from None


@router.post(
    "/notifications/devices",
    response_model=NotificationDeviceResponse,
    status_code=status.HTTP_201_CREATED,
    response_description="The registered Expo push device.",
    summary="Register an Expo push device",
    description=(
        "Register or refresh one Expo push token for the authenticated account. "
        "Repeated registration of the same token is idempotent."
    ),
    responses=documented_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        status.HTTP_503_SERVICE_UNAVAILABLE,
    ),
    tags=["Notifications"],
)
def register_device(
    device_data: NotificationDeviceRegistration,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return register_notification_device(
            db,
            user_id=current_user.id,
            token=device_data.token,
            platform=device_data.platform,
        )
    except NotificationPersistenceError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Notification device registration is temporarily unavailable",
        ) from None


@router.delete(
    "/notifications/devices/{device_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    response_description="The device registration was removed.",
    summary="Remove an Expo push device",
    description="Remove one device registration owned by the authenticated account.",
    responses=documented_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_404_NOT_FOUND,
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        status.HTTP_503_SERVICE_UNAVAILABLE,
    ),
    tags=["Notifications"],
)
def delete_device(
    device_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        removed = unregister_notification_device(
            db,
            user_id=current_user.id,
            device_id=device_id,
        )
    except NotificationPersistenceError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Notification device registration is temporarily unavailable",
        ) from None

    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification device not found",
        )
    return {"message": "Notification device removed"}
