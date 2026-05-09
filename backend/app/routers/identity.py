from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_admin_db, get_audit_db
from app.middleware.auth import get_current_user, require_roles
from app.models import User
from app.schemas.auth import CurrentUserResponse, LoginRequest, LoginResponse
from app.schemas.user import UserInviteRequest, UserListResponse, UserRead, UserUpdateRequest
from app.services.auth_service import authenticate_user, create_access_token
from app.services.audit_service import write_audit_log
from app.utils.security import hash_password


router = APIRouter(prefix="/api/v1", tags=["identity"])


@router.post("/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_admin_db)) -> LoginResponse:
    user = authenticate_user(db, payload.email, payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token, expires_in = create_access_token(user)
    return LoginResponse(
        data={
            "access_token": token,
            "token_type": "bearer",
            "expires_in": expires_in,
            "user": UserRead.model_validate(user),
        },
        meta={},
    )


@router.get("/users/me", response_model=CurrentUserResponse)
def current_user(user: User = Depends(get_current_user)) -> CurrentUserResponse:
    return CurrentUserResponse(data=UserRead.model_validate(user), meta={})


@router.get("/users", response_model=UserListResponse)
def list_users(
    db: Session = Depends(get_admin_db),
    _: User = Depends(require_roles(["admin"])),
) -> UserListResponse:
    users = list(db.scalars(select(User).order_by(User.full_name)).all())
    return UserListResponse(data=[UserRead.model_validate(user) for user in users], meta={"count": len(users)})


@router.post("/users/invite", response_model=CurrentUserResponse)
def invite_user(
    payload: UserInviteRequest,
    db: Session = Depends(get_admin_db),
    audit_db: Session = Depends(get_audit_db),
    actor: User = Depends(require_roles(["admin"])),
) -> CurrentUserResponse:
    existing = db.scalar(select(User).where(User.email == payload.email))
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")
    user = User(
        email=payload.email,
        full_name=payload.full_name,
        role=payload.role,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    write_audit_log(
        audit_db,
        actor,
        action="user_invited",
        resource_type="user",
        resource_id=user.id,
        event_type="settings",
        metadata={"email": user.email, "role": user.role},
    )
    audit_db.commit()
    return CurrentUserResponse(data=UserRead.model_validate(user), meta={})


@router.patch("/users/{user_id}", response_model=CurrentUserResponse)
def update_user(
    user_id: str,
    payload: UserUpdateRequest,
    db: Session = Depends(get_admin_db),
    audit_db: Session = Depends(get_audit_db),
    actor: User = Depends(require_roles(["admin"])),
) -> CurrentUserResponse:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if payload.role is not None:
        user.role = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.full_name is not None:
        user.full_name = payload.full_name
    db.commit()
    db.refresh(user)
    write_audit_log(
        audit_db,
        actor,
        action="user_updated",
        resource_type="user",
        resource_id=user.id,
        event_type="settings",
        metadata={"email": user.email, "role": user.role, "is_active": user.is_active},
    )
    audit_db.commit()
    return CurrentUserResponse(data=UserRead.model_validate(user), meta={})
