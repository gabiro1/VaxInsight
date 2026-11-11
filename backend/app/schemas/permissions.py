from uuid import UUID

from pydantic import BaseModel, Field

from app.models.user import UserRole


class PermissionResponse(BaseModel):
    name: str = Field(description="Stable permission identifier.")
    description: str = Field(description="Capability represented by the permission.")
    implemented: bool = Field(
        description="Whether the corresponding backend capability exists."
    )
    assignable: bool = Field(
        description="Whether the permission may be received by a current role."
    )


class PermissionCatalogueResponse(BaseModel):
    items: list[PermissionResponse] = Field(
        description="Known permissions, including reserved future permissions."
    )


class RolePermissionsResponse(BaseModel):
    role: UserRole = Field(description="Application role.")
    permissions: list[str] = Field(
        description="Permissions assigned to the role, in stable order."
    )


class RolePermissionsPageResponse(BaseModel):
    items: list[RolePermissionsResponse] = Field(
        description="Permission assignments for every application role."
    )


class UserPermissionsResponse(BaseModel):
    id: UUID = Field(description="Unique account identifier.")
    role: UserRole | None = Field(description="Current application role.")
    status: str = Field(description="Current account lifecycle status.")
    permissions: list[str] = Field(
        description="Effective permissions for the account's current role and state."
    )
