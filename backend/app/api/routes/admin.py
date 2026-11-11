from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.api.dependencies import require_permissions
from app.api.docs import documented_responses
from app.core.account import is_active_account
from app.core.permissions import (
    PERMISSION_DEFINITIONS,
    Permission,
    effective_permissions_for_user,
    permissions_for_role,
)
from app.database.dependencies import get_db
from app.models.user import AccountStatus, User, UserRole
from app.schemas.admin_invitations import (
    AdminInvitationPageResponse,
    AdminInvitationResponse,
    InvitationDirectoryQuery,
)
from app.schemas.admin_users import (
    AdminUserPageResponse,
    AdminUserResponse,
    UserDirectoryQuery,
)
from app.schemas.audit import (
    AuditEventPageResponse,
    AuditEventQuery,
    AuditEventResponse,
)
from app.schemas.common import MessageResponse
from app.schemas.dashboard import DashboardSummaryResponse
from app.schemas.permissions import (
    PermissionCatalogueResponse,
    PermissionResponse,
    RolePermissionsPageResponse,
    RolePermissionsResponse,
    UserPermissionsResponse,
)
from app.services.admin_invitations import (
    InvitationNotDeletable,
    delete_revoked_invitation,
    get_admin_invitation,
    invitation_status,
    list_admin_invitations,
)
from app.services.admin_users import (
    get_admin_user,
    list_admin_users,
)
from app.services.audit import list_audit_events, sanitize_audit_details
from app.services.auth import InvitationNotRevocable
from app.services.auth import revoke_invitation as revoke_invitation_service
from app.services.dashboard import get_dashboard_summary

router = APIRouter()
audit_read_dependency = require_permissions(Permission.AUDIT_READ)
invitation_manage_dependency = require_permissions(Permission.INVITATION_MANAGE)
user_read_dependency = require_permissions(Permission.USER_READ)
role_read_dependency = require_permissions(Permission.ROLE_READ)
user_role_read_dependency = require_permissions(
    Permission.USER_READ,
    Permission.ROLE_READ,
)


def _role_permissions_response(role: UserRole) -> RolePermissionsResponse:
    return RolePermissionsResponse(
        role=role,
        permissions=sorted(permissions_for_role(role)),
    )


@router.get(
    "/permissions",
    response_model=PermissionCatalogueResponse,
    status_code=http_status.HTTP_200_OK,
    response_description="The known permission catalogue.",
    summary="List permissions",
    description=(
        "Return the static permission catalogue. Reserved future permissions are "
        "reported but are not assigned to any current role."
    ),
    responses=documented_responses(
        http_status.HTTP_401_UNAUTHORIZED,
        http_status.HTTP_403_FORBIDDEN,
    ),
    tags=["Permission Management"],
)
def list_permissions(
    _current_user: User = Depends(role_read_dependency),
):
    """Return permission definitions without exposing account or narrative data."""

    return PermissionCatalogueResponse(
        items=[
            PermissionResponse(
                name=definition.name,
                description=definition.description,
                implemented=definition.implemented,
                assignable=definition.assignable,
            )
            for definition in PERMISSION_DEFINITIONS
        ]
    )


@router.get(
    "/roles",
    response_model=RolePermissionsPageResponse,
    status_code=http_status.HTTP_200_OK,
    response_description="Permission assignments for all application roles.",
    summary="List role permissions",
    description=(
        "Return the explicit static role-to-permission mapping. This endpoint does "
        "not edit roles or create custom permission assignments."
    ),
    responses=documented_responses(
        http_status.HTTP_401_UNAUTHORIZED,
        http_status.HTTP_403_FORBIDDEN,
    ),
    tags=["Permission Management"],
)
def list_role_permissions(
    _current_user: User = Depends(role_read_dependency),
):
    """Return every current role and its explicitly assigned permissions."""

    return RolePermissionsPageResponse(
        items=[_role_permissions_response(role) for role in UserRole]
    )


@router.get(
    "/roles/{role}",
    response_model=RolePermissionsResponse,
    status_code=http_status.HTTP_200_OK,
    response_description="Permission assignments for one application role.",
    summary="Get role permissions",
    description="Return the permissions explicitly assigned to one application role.",
    responses=documented_responses(
        http_status.HTTP_401_UNAUTHORIZED,
        http_status.HTTP_403_FORBIDDEN,
        http_status.HTTP_422_UNPROCESSABLE_CONTENT,
    ),
    tags=["Permission Management"],
)
def get_role_permissions(
    role: UserRole,
    _current_user: User = Depends(role_read_dependency),
):
    """Return one role's static permission assignment."""

    return _role_permissions_response(role)


@router.get(
    "/users/{user_id}/permissions",
    response_model=UserPermissionsResponse,
    status_code=http_status.HTTP_200_OK,
    response_description="The requested user's effective permissions.",
    summary="Get user permissions",
    description=(
        "Return the effective permissions for an account's current role. Inactive "
        "accounts have no effective permissions even when a role remains assigned."
    ),
    responses=documented_responses(
        http_status.HTTP_401_UNAUTHORIZED,
        http_status.HTTP_403_FORBIDDEN,
        http_status.HTTP_404_NOT_FOUND,
        http_status.HTTP_422_UNPROCESSABLE_CONTENT,
    ),
    tags=["Permission Management"],
)
def get_user_permissions(
    user_id: UUID,
    _current_user: User = Depends(user_role_read_dependency),
    db: Session = Depends(get_db),
):
    """Return effective permissions without exposing credentials or narrative data."""

    target_user = db.get(User, user_id)
    if target_user is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    permissions = (
        sorted(effective_permissions_for_user(target_user))
        if is_active_account(target_user)
        else []
    )
    return UserPermissionsResponse(
        id=target_user.id,
        role=target_user.role,
        status=target_user.status,
        permissions=permissions,
    )


def get_audit_event_query(
    page: int = Query(
        default=1,
        ge=1,
        le=10_000,
        description="1-based page number.",
    ),
    page_size: int = Query(
        default=50,
        ge=1,
        le=100,
        description="Number of audit events to return per page.",
    ),
    action: str | None = Query(
        default=None,
        min_length=1,
        max_length=64,
        description="Filter by the recorded audit action.",
    ),
    outcome: str | None = Query(
        default=None,
        min_length=1,
        max_length=32,
        description="Filter by the recorded outcome, such as success or failure.",
    ),
    actor_user_id: UUID | None = Query(
        default=None,
        description="Filter by the user who initiated the event.",
    ),
    target_user_id: UUID | None = Query(
        default=None,
        description="Filter by the user affected by the event.",
    ),
    start_date: datetime | None = Query(
        default=None,
        description="Include events created at or after this UTC timestamp.",
    ),
    end_date: datetime | None = Query(
        default=None,
        description="Include events created at or before this UTC timestamp.",
    ),
) -> AuditEventQuery:
    try:
        return AuditEventQuery(
            page=page,
            page_size=page_size,
            action=action,
            outcome=outcome,
            actor_user_id=actor_user_id,
            target_user_id=target_user_id,
            start_date=start_date,
            end_date=end_date,
        )
    except ValidationError as error:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Invalid audit event filters",
        ) from error


def get_user_directory_query(
    page: int = Query(
        default=1,
        ge=1,
        le=10_000,
        description="1-based page number.",
    ),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Number of users to return per page.",
    ),
    search: str | None = Query(
        default=None,
        min_length=1,
        max_length=255,
        description="Search by a normalized email fragment.",
    ),
    role: UserRole | None = Query(
        default=None,
        description="Filter by role: chw, reviewer, or administrator.",
    ),
    status: AccountStatus | None = Query(
        default=None,
        description=(
            "Filter by account status: active, suspended, deactivated, or deleted."
        ),
    ),
    email_verified: bool | None = Query(
        default=None,
        description="Filter by whether the account email has been verified.",
    ),
    sort_by: str = Query(
        default="created_at",
        description=(
            "Sort field: created_at, updated_at, email, last_login_at, status, or role."
        ),
    ),
    sort_order: str = Query(
        default="desc",
        description="Sort direction: asc or desc.",
    ),
) -> UserDirectoryQuery:
    try:
        return UserDirectoryQuery(
            page=page,
            page_size=page_size,
            search=search,
            role=role,
            status=status,
            email_verified=email_verified,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    except ValidationError as error:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Invalid user directory filters",
        ) from error


def get_invitation_directory_query(
    page: int = Query(
        default=1,
        ge=1,
        le=10_000,
        description="1-based page number.",
    ),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Number of invitations to return per page.",
    ),
    search: str | None = Query(
        default=None,
        min_length=1,
        max_length=255,
        description="Search by a normalized invitee email fragment.",
    ),
    role: UserRole | None = Query(
        default=None,
        description="Filter by invited role: chw, reviewer, or administrator.",
    ),
    status: str | None = Query(
        default=None,
        description="Filter by status: pending, accepted, revoked, or expired.",
    ),
    sort_by: str = Query(
        default="created_at",
        description="Sort field: created_at, expires_at, email, or status.",
    ),
    sort_order: str = Query(
        default="desc",
        description="Sort direction: asc or desc.",
    ),
) -> InvitationDirectoryQuery:
    try:
        return InvitationDirectoryQuery(
            page=page,
            page_size=page_size,
            search=search,
            role=role,
            status=status,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    except ValidationError as error:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Invalid invitation filters",
        ) from error


@router.get(
    "/audit-events",
    response_model=AuditEventPageResponse,
    status_code=http_status.HTTP_200_OK,
    response_description="A filtered page of sanitized audit events.",
    summary="List audit events",
    description=(
        "Return a newest-first, paginated audit log. Sensitive audit details are "
        "sanitized before they are included in the response."
    ),
    responses=documented_responses(
        http_status.HTTP_401_UNAUTHORIZED,
        http_status.HTTP_403_FORBIDDEN,
        http_status.HTTP_422_UNPROCESSABLE_CONTENT,
    ),
    tags=["Audit Logs"],
)
def get_audit_events(
    _current_user: User = Depends(audit_read_dependency),
    query: AuditEventQuery = Depends(get_audit_event_query),
    db: Session = Depends(get_db),
):
    """Return a filtered, newest-first audit event page to administrators."""

    result = list_audit_events(
        db,
        page=query.page,
        page_size=query.page_size,
        action=query.action,
        outcome=query.outcome,
        actor_user_id=query.actor_user_id,
        target_user_id=query.target_user_id,
        start_date=query.start_date,
        end_date=query.end_date,
    )

    return AuditEventPageResponse(
        items=[
            AuditEventResponse(
                id=event.id,
                actor_user_id=event.actor_user_id,
                target_user_id=event.target_user_id,
                action=event.action,
                outcome=event.outcome,
                ip_address=event.ip_address,
                user_agent=event.user_agent,
                created_at=event.created_at,
                details=sanitize_audit_details(event.details),
            )
            for event in result.events
        ],
        page=query.page,
        page_size=query.page_size,
        total=result.total,
        total_pages=(result.total + query.page_size - 1) // query.page_size,
    )


def _admin_invitation_response(invitation) -> AdminInvitationResponse:
    return AdminInvitationResponse(
        id=invitation.id,
        email=invitation.email,
        role=invitation.role,
        status=invitation_status(
            accepted_at=invitation.accepted_at,
            revoked_at=invitation.revoked_at,
            expires_at=invitation.expires_at,
            now=datetime.now(UTC),
        ),
        created_at=invitation.created_at,
        expires_at=invitation.expires_at,
        accepted_at=invitation.accepted_at,
        revoked_at=invitation.revoked_at,
    )


@router.get(
    "/invitations",
    response_model=AdminInvitationPageResponse,
    status_code=http_status.HTTP_200_OK,
    response_description="A paginated page of invitation metadata.",
    summary="List account invitations",
    description=(
        "Return searchable, sortable invitation metadata without raw invitation "
        "tokens or token hashes."
    ),
    responses=documented_responses(
        http_status.HTTP_401_UNAUTHORIZED,
        http_status.HTTP_403_FORBIDDEN,
        http_status.HTTP_422_UNPROCESSABLE_CONTENT,
    ),
    tags=["Invitation Management"],
)
def list_invitations_for_admin(
    _current_user: User = Depends(invitation_manage_dependency),
    query: InvitationDirectoryQuery = Depends(get_invitation_directory_query),
    db: Session = Depends(get_db),
):
    """Return a filtered page of invitation metadata."""

    result = list_admin_invitations(
        db,
        page=query.page,
        page_size=query.page_size,
        search=query.search,
        role=query.role.value if query.role is not None else None,
        status=query.status,
        sort_by=query.sort_by,
        sort_order=query.sort_order,
    )
    return AdminInvitationPageResponse(
        items=[
            _admin_invitation_response(invitation) for invitation in result.invitations
        ],
        page=query.page,
        page_size=query.page_size,
        total=result.total,
        total_pages=(result.total + query.page_size - 1) // query.page_size,
    )


@router.get(
    "/invitations/{invitation_id}",
    response_model=AdminInvitationResponse,
    status_code=http_status.HTTP_200_OK,
    response_description="Sanitized metadata for the requested invitation.",
    summary="Get invitation details",
    description="Return non-secret metadata for one invitation.",
    responses=documented_responses(
        http_status.HTTP_401_UNAUTHORIZED,
        http_status.HTTP_403_FORBIDDEN,
        http_status.HTTP_404_NOT_FOUND,
        http_status.HTTP_422_UNPROCESSABLE_CONTENT,
    ),
    tags=["Invitation Management"],
)
def get_invitation_for_admin(
    invitation_id: UUID,
    _current_user: User = Depends(invitation_manage_dependency),
    db: Session = Depends(get_db),
):
    """Return approved metadata for one invitation."""

    invitation = get_admin_invitation(db, invitation_id)
    if invitation is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Invitation not found",
        )
    return _admin_invitation_response(invitation)


@router.post(
    "/invitations/{invitation_id}/revoke",
    response_model=AdminInvitationResponse,
    status_code=http_status.HTTP_200_OK,
    response_description="The revoked invitation metadata.",
    summary="Revoke an invitation",
    description="Revoke one pending invitation and return its resulting metadata.",
    responses=documented_responses(
        http_status.HTTP_401_UNAUTHORIZED,
        http_status.HTTP_403_FORBIDDEN,
        http_status.HTTP_404_NOT_FOUND,
        http_status.HTTP_409_CONFLICT,
        http_status.HTTP_422_UNPROCESSABLE_CONTENT,
    ),
    tags=["Invitation Management"],
)
def revoke_invitation_for_admin(
    invitation_id: UUID,
    current_user: User = Depends(invitation_manage_dependency),
    db: Session = Depends(get_db),
):
    """Revoke one pending invitation and return its resulting metadata."""

    try:
        invitation = revoke_invitation_service(
            db,
            invitation_id=invitation_id,
            revoked_by=current_user,
        )
    except InvitationNotRevocable:
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail="Only pending invitations can be revoked",
        ) from None

    if invitation is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Invitation not found",
        )
    return _admin_invitation_response(invitation)


@router.delete(
    "/invitations/{invitation_id}",
    response_model=MessageResponse,
    status_code=http_status.HTTP_200_OK,
    response_description="Confirmation that the revoked invitation was deleted.",
    summary="Delete a revoked invitation",
    description="Permanently delete one revoked invitation and its email metadata.",
    responses=documented_responses(
        http_status.HTTP_401_UNAUTHORIZED,
        http_status.HTTP_403_FORBIDDEN,
        http_status.HTTP_404_NOT_FOUND,
        http_status.HTTP_409_CONFLICT,
        http_status.HTTP_422_UNPROCESSABLE_CONTENT,
    ),
    tags=["Invitation Management"],
)
def delete_invitation_for_admin(
    invitation_id: UUID,
    current_user: User = Depends(invitation_manage_dependency),
    db: Session = Depends(get_db),
):
    """Permanently delete one revoked invitation without deleting its audit event."""

    try:
        deleted = delete_revoked_invitation(
            db,
            invitation_id=invitation_id,
            deleted_by=current_user,
        )
    except InvitationNotDeletable:
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail="Only revoked invitations can be deleted",
        ) from None

    if not deleted:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Invitation not found",
        )
    return {"message": "Invitation deleted successfully"}


def _admin_user_response(user) -> AdminUserResponse:
    return AdminUserResponse(
        id=user.id,
        email=user.email,
        role=user.role,
        status=user.status,
        email_verified=user.email_verified_at is not None,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
        updated_at=user.updated_at,
    )


@router.get(
    "/users",
    response_model=AdminUserPageResponse,
    status_code=http_status.HTTP_200_OK,
    response_description="A paginated page of sanitized user account fields.",
    summary="List users",
    description=(
        "Return searchable, sortable user account metadata for administrators "
        "without password or token fields."
    ),
    responses=documented_responses(
        http_status.HTTP_401_UNAUTHORIZED,
        http_status.HTTP_403_FORBIDDEN,
        http_status.HTTP_422_UNPROCESSABLE_CONTENT,
    ),
    tags=["User Management"],
)
def list_users_for_admin(
    _current_user: User = Depends(user_read_dependency),
    query: UserDirectoryQuery = Depends(get_user_directory_query),
    db: Session = Depends(get_db),
):
    """Return a filtered page of approved user account fields."""

    result = list_admin_users(
        db,
        page=query.page,
        page_size=query.page_size,
        search=query.search,
        role=query.role.value if query.role is not None else None,
        status=query.status.value if query.status is not None else None,
        email_verified=query.email_verified,
        sort_by=query.sort_by,
        sort_order=query.sort_order,
    )
    return AdminUserPageResponse(
        items=[_admin_user_response(user) for user in result.users],
        page=query.page,
        page_size=query.page_size,
        total=result.total,
        total_pages=(result.total + query.page_size - 1) // query.page_size,
    )


@router.get(
    "/users/{user_id}",
    response_model=AdminUserResponse,
    status_code=http_status.HTTP_200_OK,
    response_description="Sanitized account fields for the requested user.",
    summary="Get user details",
    description="Return approved, non-sensitive account fields for one user.",
    responses=documented_responses(
        http_status.HTTP_401_UNAUTHORIZED,
        http_status.HTTP_403_FORBIDDEN,
        http_status.HTTP_404_NOT_FOUND,
        http_status.HTTP_422_UNPROCESSABLE_CONTENT,
    ),
    tags=["User Management"],
)
def get_user_for_admin(
    user_id: UUID,
    _current_user: User = Depends(user_read_dependency),
    db: Session = Depends(get_db),
):
    """Return approved account fields for one user."""

    user = get_admin_user(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return _admin_user_response(user)


@router.get(
    "/dashboard/summary",
    response_model=DashboardSummaryResponse,
    status_code=http_status.HTTP_200_OK,
    response_description="Aggregate counts for the administrator dashboard.",
    summary="Get dashboard summary",
    description=(
        "Return aggregate user, invitation, role, session, and platform metrics "
        "for an administrator dashboard."
    ),
    responses=documented_responses(
        http_status.HTTP_401_UNAUTHORIZED,
        http_status.HTTP_403_FORBIDDEN,
    ),
    tags=["Administrator Dashboard"],
)
def get_admin_dashboard_summary(
    _current_user: User = Depends(user_read_dependency),
    db: Session = Depends(get_db),
):
    """Return aggregate operational statistics to administrators."""

    return get_dashboard_summary(db)
