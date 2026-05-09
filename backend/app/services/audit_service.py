from sqlalchemy.orm import Session

from app.models import AuditLog, User


def write_audit_log(
    db: Session,
    user: User | None,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    event_type: str = "governance",
    metadata: dict | None = None,
) -> None:
    db.add(
        AuditLog(
            user_id=user.id if user else None,
            event_type=event_type,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            event_metadata=metadata or {},
        )
    )

