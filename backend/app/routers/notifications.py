from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_admin_db, get_audit_db
from app.middleware.auth import get_current_user, require_roles
from app.models import NotificationSetting, User
from app.schemas.notification import (
    NotificationSettingCreate,
    NotificationSettingListResponse,
    NotificationSettingRead,
    NotificationSettingResponse,
    NotificationSettingUpdate,
    NotificationTestResponse,
)
from app.services.audit_service import write_audit_log
from app.services.notification_service import normalize_channel, validate_target


router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


@router.get("", response_model=NotificationSettingListResponse)
def list_notification_settings(
    db: Session = Depends(get_admin_db),
    _: User = Depends(get_current_user),
) -> NotificationSettingListResponse:
    settings = list(db.scalars(select(NotificationSetting).order_by(NotificationSetting.channel)).all())
    return NotificationSettingListResponse(
        data=[NotificationSettingRead.model_validate(setting) for setting in settings],
        meta={"count": len(settings)},
    )


@router.post("", response_model=NotificationSettingResponse)
def create_notification_setting(
    payload: NotificationSettingCreate,
    db: Session = Depends(get_admin_db),
    audit_db: Session = Depends(get_audit_db),
    user: User = Depends(require_roles(["admin"])),
) -> NotificationSettingResponse:
    try:
        channel = normalize_channel(payload.channel)
        target = validate_target(channel, payload.target)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    setting = NotificationSetting(channel=channel, target=target, enabled=payload.enabled, events=payload.events)
    db.add(setting)
    db.commit()
    db.refresh(setting)
    write_audit_log(
        audit_db,
        user,
        action="notification_setting_created",
        resource_type="notification",
        resource_id=setting.id,
        event_type="notification",
        metadata={"channel": channel, "target": target, "enabled": setting.enabled},
    )
    audit_db.commit()
    return NotificationSettingResponse(data=NotificationSettingRead.model_validate(setting), meta={})


@router.patch("/{setting_id}", response_model=NotificationSettingResponse)
def update_notification_setting(
    setting_id: str,
    payload: NotificationSettingUpdate,
    db: Session = Depends(get_admin_db),
    audit_db: Session = Depends(get_audit_db),
    user: User = Depends(require_roles(["admin"])),
) -> NotificationSettingResponse:
    setting = db.get(NotificationSetting, setting_id)
    if setting is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification setting not found")
    if payload.target is not None:
        try:
            setting.target = validate_target(setting.channel, payload.target)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if payload.enabled is not None:
        setting.enabled = payload.enabled
    if payload.events is not None:
        setting.events = payload.events
    db.commit()
    db.refresh(setting)
    write_audit_log(
        audit_db,
        user,
        action="notification_setting_updated",
        resource_type="notification",
        resource_id=setting.id,
        event_type="notification",
        metadata={"channel": setting.channel, "enabled": setting.enabled},
    )
    audit_db.commit()
    return NotificationSettingResponse(data=NotificationSettingRead.model_validate(setting), meta={})


@router.post("/{setting_id}/test", response_model=NotificationTestResponse)
def test_notification_setting(
    setting_id: str,
    db: Session = Depends(get_admin_db),
    audit_db: Session = Depends(get_audit_db),
    user: User = Depends(require_roles(["admin"])),
) -> NotificationTestResponse:
    setting = db.get(NotificationSetting, setting_id)
    if setting is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification setting not found")
    write_audit_log(
        audit_db,
        user,
        action="notification_test_sent",
        resource_type="notification",
        resource_id=setting.id,
        event_type="notification",
        metadata={"channel": setting.channel, "target": setting.target},
    )
    audit_db.commit()
    return NotificationTestResponse(
        data={
            "success": True,
            "channel": setting.channel,
            "message": "Localhost notification test recorded in audit log",
        },
        meta={},
    )


@router.delete("/{setting_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notification_setting(
    setting_id: str,
    db: Session = Depends(get_admin_db),
    audit_db: Session = Depends(get_audit_db),
    user: User = Depends(require_roles(["admin"])),
) -> None:
    setting = db.get(NotificationSetting, setting_id)
    if setting is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification setting not found")
    db.delete(setting)
    db.commit()
    write_audit_log(
        audit_db,
        user,
        action="notification_setting_deleted",
        resource_type="notification",
        resource_id=setting_id,
        event_type="notification",
        metadata={"channel": setting.channel, "target": setting.target},
    )
    audit_db.commit()
