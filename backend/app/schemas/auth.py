from pydantic import BaseModel, Field

from app.schemas.user import UserRead


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginData(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserRead


class LoginResponse(BaseModel):
    data: LoginData
    meta: dict = Field(default_factory=dict)


class CurrentUserResponse(BaseModel):
    data: UserRead
    meta: dict = Field(default_factory=dict)
