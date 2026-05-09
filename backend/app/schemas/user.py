from pydantic import BaseModel, Field


class UserRead(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool

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
