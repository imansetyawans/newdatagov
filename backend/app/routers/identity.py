from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_admin_db, get_audit_db
from app.middleware.auth import get_current_user, require_permission
from app.models import Role, User
from app.schemas.auth import CurrentUserResponse, LoginRequest, LoginResponse
from app.schemas.user import (
    PermissionListResponse,
    RoleCreateRequest,
    RoleListResponse,
    RolePermissionsUpdateRequest,
    RoleRead,
    RoleResponse,
    RoleUpdateRequest,
    UserInviteRequest,
    UserListResponse,
    UserRead,
    UserUpdateRequest,
)
from app.services.auth_service import authenticate_user, create_access_token
from app.services.access_control import (
    PERMISSION_GROUPS,
    create_role,
    get_role,
    get_role_by_code,
    list_roles,
    role_permission_keys,
    set_role_permissions,
    update_role,
    user_permission_keys,
)
from app.services.audit_service import write_audit_log
from app.utils.security import hash_password


router = APIRouter(prefix="/api/v1", tags=["identity"])


def _user_read(db: Session, user: User) -> UserRead:
    return UserRead.model_validate(user).model_copy(update={"permissions": user_permission_keys(db, user)})


def _role_read(role: Role) -> RoleRead:
    return RoleRead(
        id=role.id,
        name=role.name,
        code=role.code,
        description=role.description,
        is_system=role.is_system,
        is_active=role.is_active,
        permissions=role_permission_keys(role),
    )


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
            "user": _user_read(db, user),
        },
        meta={},
    )


@router.get("/users/me", response_model=CurrentUserResponse)
def current_user(user: User = Depends(get_current_user), db: Session = Depends(get_admin_db)) -> CurrentUserResponse:
    return CurrentUserResponse(data=_user_read(db, user), meta={})


@router.get("/users", response_model=UserListResponse)
def list_users(
    db: Session = Depends(get_admin_db),
    _: User = Depends(require_permission("users.view")),
) -> UserListResponse:
    users = list(db.scalars(select(User).order_by(User.full_name)).all())
    return UserListResponse(data=[_user_read(db, user) for user in users], meta={"count": len(users)})


@router.get("/permissions", response_model=PermissionListResponse)
def permissions(
    _: User = Depends(require_permission("roles.view")),
) -> PermissionListResponse:
    return PermissionListResponse(
        data=[
            {"module": module, "permissions": permissions}
            for module, permissions in PERMISSION_GROUPS.items()
        ],
        meta={"count": sum(len(permissions) for permissions in PERMISSION_GROUPS.values())},
    )


@router.get("/roles", response_model=RoleListResponse)
def roles(
    include_inactive: bool = False,
    db: Session = Depends(get_admin_db),
    _: User = Depends(require_permission("roles.view")),
) -> RoleListResponse:
    data = [_role_read(role) for role in list_roles(db, include_inactive=include_inactive)]
    return RoleListResponse(data=data, meta={"count": len(data)})


@router.post("/roles", response_model=RoleResponse)
def role_create(
    payload: RoleCreateRequest,
    db: Session = Depends(get_admin_db),
    audit_db: Session = Depends(get_audit_db),
    actor: User = Depends(require_permission("roles.manage_permissions")),
) -> RoleResponse:
    if get_role_by_code(db, payload.code) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Role code already exists")
    role = create_role(db, payload.name, payload.code, payload.description, payload.permissions)
    write_audit_log(
        audit_db,
        actor,
        action="role_created",
        resource_type="role",
        resource_id=role.id,
        event_type="security",
        metadata={"name": role.name, "code": role.code},
    )
    audit_db.commit()
    return RoleResponse(data=_role_read(role), meta={})


@router.patch("/roles/{role_id}", response_model=RoleResponse)
def role_update(
    role_id: str,
    payload: RoleUpdateRequest,
    db: Session = Depends(get_admin_db),
    audit_db: Session = Depends(get_audit_db),
    actor: User = Depends(require_permission("roles.manage_permissions")),
) -> RoleResponse:
    role = get_role(db, role_id)
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    role = update_role(db, role, name=payload.name, description=payload.description, is_active=payload.is_active)
    write_audit_log(
        audit_db,
        actor,
        action="role_updated",
        resource_type="role",
        resource_id=role.id,
        event_type="security",
        metadata={"name": role.name, "code": role.code, "is_active": role.is_active},
    )
    audit_db.commit()
    return RoleResponse(data=_role_read(role), meta={})


@router.put("/roles/{role_id}/permissions", response_model=RoleResponse)
def role_permissions_update(
    role_id: str,
    payload: RolePermissionsUpdateRequest,
    db: Session = Depends(get_admin_db),
    audit_db: Session = Depends(get_audit_db),
    actor: User = Depends(require_permission("roles.manage_permissions")),
) -> RoleResponse:
    role = get_role(db, role_id)
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    role = set_role_permissions(db, role, payload.permissions)
    db.commit()
    role = get_role(db, role.id) or role
    write_audit_log(
        audit_db,
        actor,
        action="role_permissions_updated",
        resource_type="role",
        resource_id=role.id,
        event_type="security",
        metadata={"code": role.code, "permission_count": len(payload.permissions)},
    )
    audit_db.commit()
    return RoleResponse(data=_role_read(role), meta={})


@router.post("/users/invite", response_model=CurrentUserResponse)
def invite_user(
    payload: UserInviteRequest,
    db: Session = Depends(get_admin_db),
    audit_db: Session = Depends(get_audit_db),
    actor: User = Depends(require_permission("users.invite")),
) -> CurrentUserResponse:
    existing = db.scalar(select(User).where(User.email == payload.email))
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")
    if get_role_by_code(db, payload.role) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role is not available")
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
        event_type="security",
        metadata={"email": user.email, "role": user.role},
    )
    audit_db.commit()
    return CurrentUserResponse(data=_user_read(db, user), meta={})


@router.patch("/users/{user_id}", response_model=CurrentUserResponse)
def update_user(
    user_id: str,
    payload: UserUpdateRequest,
    db: Session = Depends(get_admin_db),
    audit_db: Session = Depends(get_audit_db),
    actor: User = Depends(require_permission("users.edit")),
) -> CurrentUserResponse:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if payload.role is not None:
        if get_role_by_code(db, payload.role) is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role is not available")
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
        event_type="security",
        metadata={"email": user.email, "role": user.role, "is_active": user.is_active},
    )
    audit_db.commit()
    return CurrentUserResponse(data=_user_read(db, user), meta={})
