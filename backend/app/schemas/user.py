from pydantic import BaseModel, Field


class UserRead(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    permissions: list[str] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class UserInviteRequest(BaseModel):
    email: str
    full_name: str
    role: str = "viewer"
    password: str = "changeme123"


class UserUpdateRequest(BaseModel):
    role: str | None = None
    is_active: bool | None = None
    full_name: str | None = None


class UserListResponse(BaseModel):
    data: list[UserRead]
    meta: dict = Field(default_factory=dict)


class PermissionDefinition(BaseModel):
    key: str
    label: str


class PermissionGroup(BaseModel):
    module: str
    permissions: list[PermissionDefinition]


class PermissionListResponse(BaseModel):
    data: list[PermissionGroup]
    meta: dict = Field(default_factory=dict)


class RoleRead(BaseModel):
    id: str
    name: str
    code: str
    description: str | None = None
    is_system: bool
    is_active: bool
    permissions: list[str] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class RoleCreateRequest(BaseModel):
    name: str
    code: str
    description: str | None = None
    permissions: list[str] = Field(default_factory=list)


class RoleUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class RolePermissionsUpdateRequest(BaseModel):
    permissions: list[str] = Field(default_factory=list)


class RoleListResponse(BaseModel):
    data: list[RoleRead]
    meta: dict = Field(default_factory=dict)


class RoleResponse(BaseModel):
    data: RoleRead
    meta: dict = Field(default_factory=dict)
