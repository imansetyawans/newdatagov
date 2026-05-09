from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import NotificationSetting, User
from app.services.audit_service import write_audit_log


SUPPORTED_CHANNELS = {"email", "slack"}


def normalize_channel(channel: str) -> str:
    normalized = channel.strip().lower()
    if normalized not in SUPPORTED_CHANNELS:
        raise ValueError("Notification channel must be email or slack")
    return normalized


def validate_target(channel: str, target: str) -> str:
    clean_target = target.strip()
    if not clean_target:
        raise ValueError("Notification target is required")
    if channel == "email" and "@" not in clean_target:
        raise ValueError("Email notification target must be an email address")
    if channel == "slack" and not clean_target.startswith(("http://", "https://")):
        raise ValueError("Slack notification target must be a webhook URL")
    return clean_target


def dispatch_notifications(
    admin_db: Session,
    audit_db: Session,
    event_name: str,
    payload: dict,
    user: User | None = None,
) -> int:
    settings = list(
        admin_db.scalars(
            select(NotificationSetting).where(NotificationSetting.enabled.is_(True))
        ).all()
    )
    sent_count = 0
    for setting in settings:
        if event_name not in setting.events:
            continue
        sent_count += 1
        write_audit_log(
            audit_db,
            user,
            action="notification_sent",
            resource_type="notification",
            resource_id=setting.id,
            event_type="notification",
            metadata={
                "channel": setting.channel,
                "target": setting.target,
                "event": event_name,
                "payload": payload,
            },
        )
    return sent_count
