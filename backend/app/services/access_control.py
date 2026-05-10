from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.models import Role, RolePermission, User


PERMISSION_GROUPS: dict[str, list[dict[str, str]]] = {
    "Dashboard": [{"key": "dashboard.view", "label": "View dashboard"}],
    "Catalogue": [
        {"key": "catalogue.view", "label": "View catalogue"},
        {"key": "catalogue.upload", "label": "Upload dataset"},
        {"key": "catalogue.edit_metadata", "label": "Edit metadata"},
        {"key": "catalogue.generate_metadata", "label": "Generate metadata"},
        {"key": "catalogue.assign_project", "label": "Assign project/category"},
    ],
    "Projects": [
        {"key": "projects.view", "label": "View projects"},
        {"key": "projects.create", "label": "Create projects"},
        {"key": "projects.edit", "label": "Edit projects"},
        {"key": "projects.disable", "label": "Disable projects"},
        {"key": "projects.manage_categories", "label": "Manage categories"},
    ],
    "Quality": [
        {"key": "quality.view", "label": "View quality"},
        {"key": "quality.resolve_issue", "label": "Resolve issues"},
    ],
    "Policies": [
        {"key": "policies.view", "label": "View policies"},
        {"key": "policies.create", "label": "Create policies"},
        {"key": "policies.edit", "label": "Edit policies"},
        {"key": "policies.disable", "label": "Disable policies"},
        {"key": "classifications.manage", "label": "Manage classifications"},
    ],
    "Glossary": [
        {"key": "glossary.view", "label": "View glossary"},
        {"key": "glossary.create", "label": "Create terms"},
        {"key": "glossary.edit", "label": "Edit terms"},
        {"key": "glossary.approve", "label": "Approve terms"},
    ],
    "Lineage": [
        {"key": "lineage.view", "label": "View lineage"},
        {"key": "lineage.extract", "label": "Extract lineage"},
    ],
    "Scan": [
        {"key": "scan.view", "label": "View scan"},
        {"key": "scan.run", "label": "Run scan"},
        {"key": "scan.schedule", "label": "Schedule scan"},
    ],
    "Connectors": [
        {"key": "connectors.view", "label": "View connectors"},
        {"key": "connectors.create", "label": "Create connectors"},
        {"key": "connectors.edit", "label": "Edit connectors"},
        {"key": "connectors.test", "label": "Test connectors"},
        {"key": "connectors.delete", "label": "Delete connectors"},
    ],
    "Users": [
        {"key": "users.view", "label": "View users"},
        {"key": "users.invite", "label": "Invite users"},
        {"key": "users.edit", "label": "Edit users"},
        {"key": "users.activate", "label": "Activate/deactivate users"},
    ],
    "Roles": [
        {"key": "roles.view", "label": "View roles"},
        {"key": "roles.manage_permissions", "label": "Manage role permissions"},
    ],
}

ALL_PERMISSION_KEYS = [permission["key"] for permissions in PERMISSION_GROUPS.values() for permission in permissions]

EDITOR_PERMISSION_KEYS = [
    key
    for key in ALL_PERMISSION_KEYS
    if key
    not in {
        "connectors.delete",
        "users.view",
        "users.invite",
        "users.edit",
        "users.activate",
        "roles.view",
        "roles.manage_permissions",
    }
]

VIEWER_PERMISSION_KEYS = [
    "dashboard.view",
    "catalogue.view",
    "projects.view",
    "quality.view",
    "policies.view",
    "glossary.view",
    "lineage.view",
    "scan.view",
    "connectors.view",
]

DEFAULT_ROLES = {
    "admin": {
        "name": "Admin",
        "description": "Full platform administration access.",
        "permissions": ALL_PERMISSION_KEYS,
    },
    "editor": {
        "name": "Editor",
        "description": "Governance operator with create and update access except user and role administration.",
        "permissions": EDITOR_PERMISSION_KEYS,
    },
    "viewer": {
        "name": "Viewer",
        "description": "Read-only workspace access.",
        "permissions": VIEWER_PERMISSION_KEYS,
    },
}


def ensure_default_roles(db: Session) -> None:
    for code, defaults in DEFAULT_ROLES.items():
        role = db.scalar(select(Role).where(Role.code == code))
        if role is None:
            role = Role(code=code, name=defaults["name"], description=defaults["description"], is_system=True)
            db.add(role)
            db.flush()
        role.name = defaults["name"]
        role.description = defaults["description"]
        role.is_system = True
        role.is_active = True
        set_role_permissions(db, role, defaults["permissions"])
    db.commit()


def list_roles(db: Session, include_inactive: bool = False) -> list[Role]:
    statement = select(Role).options(selectinload(Role.permissions)).order_by(Role.name)
    if not include_inactive:
        statement = statement.where(Role.is_active.is_(True))
    return list(db.scalars(statement).all())


def get_role_by_code(db: Session, code: str) -> Role | None:
    return db.scalar(select(Role).options(selectinload(Role.permissions)).where(Role.code == code))


def get_role(db: Session, role_id: str) -> Role | None:
    return db.scalar(select(Role).options(selectinload(Role.permissions)).where(Role.id == role_id))


def normalize_role_code(value: str) -> str:
    return "_".join(value.strip().lower().replace("-", "_").split())


def role_permission_keys(role: Role | None) -> list[str]:
    if role is None:
        return []
    return sorted({permission.permission_key for permission in role.permissions})


def user_permission_keys(db: Session, user: User) -> list[str]:
    role = get_role_by_code(db, user.role)
    if role is None or not role.is_active:
        return []
    return role_permission_keys(role)


def user_has_permission(db: Session, user: User, permission_key: str) -> bool:
    return permission_key in set(user_permission_keys(db, user))


def create_role(db: Session, name: str, code: str, description: str | None, permission_keys: list[str]) -> Role:
    role = Role(name=name.strip(), code=normalize_role_code(code or name), description=description, is_system=False)
    db.add(role)
    db.flush()
    set_role_permissions(db, role, permission_keys)
    db.commit()
    db.refresh(role)
    return get_role(db, role.id) or role


def update_role(
    db: Session,
    role: Role,
    *,
    name: str | None = None,
    description: str | None = None,
    is_active: bool | None = None,
) -> Role:
    if name is not None:
        role.name = name.strip()
    if description is not None:
        role.description = description
    if is_active is not None:
        role.is_active = is_active
    db.commit()
    db.refresh(role)
    return get_role(db, role.id) or role


def set_role_permissions(db: Session, role: Role, permission_keys: list[str]) -> Role:
    allowed = set(ALL_PERMISSION_KEYS)
    clean_keys = sorted({key for key in permission_keys if key in allowed})
    db.execute(delete(RolePermission).where(RolePermission.role_id == role.id))
    for key in clean_keys:
        db.add(RolePermission(role_id=role.id, permission_key=key))
    db.flush()
    db.refresh(role)
    return role
