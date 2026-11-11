from datetime import UTC, datetime
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.account import is_active_account
from app.core.permissions import (
    Permission,
    has_permissions,
    validate_implemented_permission,
)
from app.core.tokens import verify_access_token
from app.database.dependencies import get_db
from app.models.user import User

bearer_scheme = HTTPBearer(
    scheme_name="BearerAuth",
    bearerFormat="JWT",
    description=(
        "JWT access token. Send the token in the Authorization header as "
        "`Bearer <access_token>`."
    ),
)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Validate the JWT and retrieve the active authenticated user."""

    payload = verify_access_token(credentials.credentials)

    if payload is None or not payload.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = UUID(payload["sub"])
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    user = db.scalar(select(User).where(User.id == user_id))

    if user is None or not is_active_account(user):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    password_changed_at = getattr(user, "password_changed_at", None)
    issued_at = payload.get("iat")
    if password_changed_at is not None and issued_at is not None:
        try:
            issued_at_datetime = datetime.fromtimestamp(issued_at, UTC)
        except (TypeError, ValueError, OverflowError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            ) from None
        if issued_at_datetime < password_changed_at:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication token is no longer valid",
                headers={"WWW-Authenticate": "Bearer"},
            )

    return user


def require_roles(*allowed_roles: str):
    """Build a dependency that enforces server-side role authorization."""

    def role_dependency(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if getattr(current_user, "role", None) not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return role_dependency


def require_permissions(*required_permissions: Permission | str):
    """Build a dependency that enforces all required permissions."""

    if not required_permissions:
        raise ValueError("At least one permission is required")

    validated_permissions = tuple(
        validate_implemented_permission(permission)
        for permission in required_permissions
    )

    def permission_dependency(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if not is_active_account(current_user):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account not found or inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not has_permissions(current_user, *validated_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return permission_dependency


def require_any_permissions(*required_permissions: Permission | str):
    """Build a dependency that accepts any one of the required permissions."""

    if not required_permissions:
        raise ValueError("At least one permission is required")

    validated_permissions = tuple(
        validate_implemented_permission(permission)
        for permission in required_permissions
    )

    def permission_dependency(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if not is_active_account(current_user):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account not found or inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not has_permissions(
            current_user,
            *validated_permissions,
            require_all=False,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return permission_dependency
