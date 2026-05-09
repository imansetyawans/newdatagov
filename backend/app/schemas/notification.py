from datetime import datetime

from pydantic import BaseModel, Field


class NotificationSettingCreate(BaseModel):
    channel: str
    target: str
    enabled: bool = True
    events: list[str] = Field(default_factory=lambda: ["scan_completed", "dq_issue_created"])


class NotificationSettingUpdate(BaseModel):
    target: str | None = None
    enabled: bool | None = None
    events: list[str] | None = None


class NotificationSettingRead(BaseModel):
    id: str
    channel: str
    target: str
    enabled: bool
    events: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NotificationSettingResponse(BaseModel):
    data: NotificationSettingRead
    meta: dict = Field(default_factory=dict)


class NotificationSettingListResponse(BaseModel):
    data: list[NotificationSettingRead]
    meta: dict = Field(default_factory=dict)


class NotificationTestResponse(BaseModel):
    data: dict
    meta: dict = Field(default_factory=dict)
