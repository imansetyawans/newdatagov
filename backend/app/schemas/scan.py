from datetime import datetime

from pydantic import BaseModel, Field


class ScanCreate(BaseModel):
    connector_ids: list[str]
    scan_type: str = "full"
    connector_scopes: dict[str, dict] = Field(default_factory=dict)
    project_id: str | None = None
    category_id: str | None = None
    dq_metrics: list[str] = Field(
        default_factory=lambda: ["completeness", "uniqueness", "consistency", "accuracy"]
    )


class ScheduledScanCreate(BaseModel):
    connector_ids: list[str]
    scan_type: str = "full"
    schedule_cron: str
    notify_on_completion: bool = True


class ScheduledScanUpdate(BaseModel):
    schedule_cron: str | None = None
    status: str | None = None
    notify_on_completion: bool | None = None


class ScanRead(BaseModel):
    id: str
    connector_ids: list[str]
    scan_type: str
    status: str
    started_at: datetime | None = None
    finished_at: datetime | None = None
    assets_scanned: int
    columns_scanned: int
    dq_issues_raised: int
    policies_applied: int
    schedule_cron: str | None = None
    errors: list = Field(default_factory=list)

    model_config = {"from_attributes": True}


class ScanResponse(BaseModel):
    data: ScanRead
    meta: dict = Field(default_factory=dict)


class ScanListResponse(BaseModel):
    data: list[ScanRead]
    meta: dict = Field(default_factory=dict)
