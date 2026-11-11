from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Final

from app.models.user import UserRole


class Permission(str, Enum):
    """Permission identifiers understood by the backend."""

    USER_READ = "user.read"
    USER_MANAGE = "user.manage"
    ROLE_READ = "role.read"
    ROLE_MANAGE = "role.manage"
    INVITATION_MANAGE = "invitation.manage"
    NARRATIVE_CREATE = "narrative.create"
    NARRATIVE_READ_OWN = "narrative.read.own"
    NARRATIVE_UPDATE_OWN = "narrative.update.own"
    NARRATIVE_ASSIGN = "narrative.assign"
    NARRATIVE_READ_ASSIGNED = "narrative.read.assigned"
    NARRATIVE_REVIEW = "narrative.review"
    VACCINE_CONTENT_READ = "vaccine_content.read"
    VACCINE_CONTENT_MANAGE = "vaccine_content.manage"
    QUESTION_CREATE = "question.create"
    QUESTION_READ_OWN = "question.read.own"
    QUESTION_REVIEW = "question.review"
    VACCINE_ANALYSIS_REQUEST = "vaccine_analysis.request"
    VACCINE_ANALYSIS_READ = "vaccine_analysis.read"
    ANALYSIS_REQUEST = "analysis.request"
    ANALYSIS_READ = "analysis.read"
    DATASET_MANAGE = "dataset.manage"
    MODEL_MANAGE = "model.manage"
    AUDIT_READ = "audit.read"


@dataclass(frozen=True)
class PermissionDefinition:
    """Metadata for one known permission."""

    name: str
    description: str
    implemented: bool
    assignable: bool


PERMISSION_DEFINITIONS: Final[tuple[PermissionDefinition, ...]] = (
    PermissionDefinition(
        Permission.USER_READ.value,
        "View permitted user account information.",
        True,
        True,
    ),
    PermissionDefinition(
        Permission.USER_MANAGE.value,
        "Manage user account lifecycle state.",
        True,
        True,
    ),
    PermissionDefinition(
        Permission.ROLE_READ.value,
        "View role assignments and permission mappings.",
        True,
        True,
    ),
    PermissionDefinition(
        Permission.ROLE_MANAGE.value,
        "Assign one of the existing application roles.",
        True,
        True,
    ),
    PermissionDefinition(
        Permission.INVITATION_MANAGE.value,
        "Create, inspect, and revoke account invitations.",
        True,
        True,
    ),
    PermissionDefinition(
        Permission.NARRATIVE_CREATE.value,
        "Submit a narrative record.",
        True,
        True,
    ),
    PermissionDefinition(
        Permission.NARRATIVE_READ_OWN.value,
        "Read narrative records owned by the authenticated user.",
        True,
        True,
    ),
    PermissionDefinition(
        Permission.NARRATIVE_UPDATE_OWN.value,
        "Update narrative records owned by the authenticated user.",
        True,
        True,
    ),
    PermissionDefinition(
        Permission.NARRATIVE_ASSIGN.value,
        "Assign and manage narrative review assignments.",
        True,
        True,
    ),
    PermissionDefinition(
        Permission.NARRATIVE_READ_ASSIGNED.value,
        "Read narratives explicitly assigned to the authenticated user.",
        True,
        True,
    ),
    PermissionDefinition(
        Permission.NARRATIVE_REVIEW.value,
        "Perform an authorized narrative review.",
        True,
        True,
    ),
    PermissionDefinition(
        Permission.VACCINE_CONTENT_READ.value,
        "Read published official vaccine content.",
        True,
        True,
    ),
    PermissionDefinition(
        Permission.VACCINE_CONTENT_MANAGE.value,
        "Create and publish official vaccine content.",
        True,
        True,
    ),
    PermissionDefinition(
        Permission.QUESTION_CREATE.value,
        "Ask a vaccine question.",
        True,
        True,
    ),
    PermissionDefinition(
        Permission.QUESTION_READ_OWN.value,
        "Read questions asked by the authenticated account.",
        True,
        True,
    ),
    PermissionDefinition(
        Permission.QUESTION_REVIEW.value,
        "Review questions and publish professional responses.",
        True,
        True,
    ),
    PermissionDefinition(
        Permission.VACCINE_ANALYSIS_REQUEST.value,
        "Request a vaccine-question analysis run through an approved provider.",
        True,
        True,
    ),
    PermissionDefinition(
        Permission.VACCINE_ANALYSIS_READ.value,
        "Read vaccine-question analysis runs.",
        True,
        True,
    ),
    PermissionDefinition(
        Permission.ANALYSIS_REQUEST.value,
        "Request analysis when an approved analysis capability exists.",
        False,
        False,
    ),
    PermissionDefinition(
        Permission.ANALYSIS_READ.value,
        "Read authorized analysis results.",
        False,
        False,
    ),
    PermissionDefinition(
        Permission.DATASET_MANAGE.value,
        "Manage approved dataset metadata.",
        False,
        False,
    ),
    PermissionDefinition(
        Permission.MODEL_MANAGE.value,
        "Manage approved model metadata.",
        False,
        False,
    ),
    PermissionDefinition(
        Permission.AUDIT_READ.value,
        "Read authorized audit records.",
        True,
        True,
    ),
)

PERMISSION_BY_NAME: Final[Mapping[str, PermissionDefinition]] = MappingProxyType(
    {definition.name: definition for definition in PERMISSION_DEFINITIONS}
)
ALL_PERMISSIONS: Final[frozenset[str]] = frozenset(PERMISSION_BY_NAME)
IMPLEMENTED_PERMISSIONS: Final[frozenset[str]] = frozenset(
    definition.name for definition in PERMISSION_DEFINITIONS if definition.implemented
)
FUTURE_PERMISSIONS: Final[frozenset[str]] = ALL_PERMISSIONS - IMPLEMENTED_PERMISSIONS

# This is intentionally configuration-backed. The existing database stores one
# application role per user and does not support custom roles or permission rows.
ROLE_PERMISSIONS: Final[Mapping[str, frozenset[str]]] = MappingProxyType(
    {
        UserRole.COMMUNITY_MEMBER.value: frozenset(
            {
                Permission.VACCINE_CONTENT_READ.value,
                Permission.NARRATIVE_CREATE.value,
                Permission.NARRATIVE_READ_OWN.value,
                Permission.NARRATIVE_UPDATE_OWN.value,
                Permission.QUESTION_CREATE.value,
                Permission.QUESTION_READ_OWN.value,
                Permission.VACCINE_ANALYSIS_REQUEST.value,
                Permission.VACCINE_ANALYSIS_READ.value,
            }
        ),
        UserRole.CHW.value: frozenset(
            {
                Permission.VACCINE_CONTENT_READ.value,
                Permission.NARRATIVE_CREATE.value,
                Permission.NARRATIVE_READ_OWN.value,
                Permission.NARRATIVE_UPDATE_OWN.value,
                Permission.QUESTION_CREATE.value,
                Permission.QUESTION_READ_OWN.value,
                Permission.VACCINE_ANALYSIS_REQUEST.value,
                Permission.VACCINE_ANALYSIS_READ.value,
            }
        ),
        UserRole.REVIEWER.value: frozenset(
            {
                Permission.VACCINE_CONTENT_READ.value,
                Permission.NARRATIVE_CREATE.value,
                Permission.NARRATIVE_READ_OWN.value,
                Permission.NARRATIVE_UPDATE_OWN.value,
                Permission.NARRATIVE_READ_ASSIGNED.value,
                Permission.NARRATIVE_REVIEW.value,
                Permission.QUESTION_CREATE.value,
                Permission.QUESTION_READ_OWN.value,
                Permission.QUESTION_REVIEW.value,
                Permission.VACCINE_ANALYSIS_REQUEST.value,
                Permission.VACCINE_ANALYSIS_READ.value,
            }
        ),
        UserRole.ADMINISTRATOR.value: frozenset(
            {
                Permission.USER_READ.value,
                Permission.USER_MANAGE.value,
                Permission.ROLE_READ.value,
                Permission.ROLE_MANAGE.value,
                Permission.INVITATION_MANAGE.value,
                Permission.NARRATIVE_ASSIGN.value,
                Permission.NARRATIVE_CREATE.value,
                Permission.NARRATIVE_READ_OWN.value,
                Permission.NARRATIVE_UPDATE_OWN.value,
                Permission.VACCINE_CONTENT_READ.value,
                Permission.VACCINE_CONTENT_MANAGE.value,
                Permission.AUDIT_READ.value,
            }
        ),
    }
)


def validate_permission(permission: Permission | str) -> str:
    """Return a known permission name or fail closed for programmer errors."""

    name = permission.value if isinstance(permission, Permission) else permission
    if not isinstance(name, str) or name not in ALL_PERMISSIONS:
        raise ValueError(f"Unknown permission: {permission!r}")
    return name


def validate_implemented_permission(permission: Permission | str) -> str:
    """Return a permission that is backed by an available capability."""

    name = validate_permission(permission)
    if name not in IMPLEMENTED_PERMISSIONS:
        raise ValueError(f"Permission is reserved for future use: {name}")
    return name


def permissions_for_role(role: UserRole | str | None) -> frozenset[str]:
    """Return the statically assigned permissions for a role."""

    role_name = role.value if isinstance(role, UserRole) else role
    return ROLE_PERMISSIONS.get(role_name, frozenset())


def effective_permissions_for_user(user) -> frozenset[str]:
    """Return permissions granted by the user's current role."""

    return permissions_for_role(getattr(user, "role", None))


def has_permission(user, permission: Permission | str) -> bool:
    """Check one validated permission against the user's current role."""

    return validate_permission(permission) in effective_permissions_for_user(user)


def has_permissions(
    user,
    *permissions: Permission | str,
    require_all: bool = True,
) -> bool:
    """Check several permissions using an explicit all/any policy."""

    if not permissions:
        raise ValueError("At least one permission is required")

    required = [validate_permission(permission) for permission in permissions]
    assigned = effective_permissions_for_user(user)
    if require_all:
        return all(permission in assigned for permission in required)
    return any(permission in assigned for permission in required)
