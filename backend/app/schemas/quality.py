from datetime import datetime

from pydantic import BaseModel, Field


class DQScoreRead(BaseModel):
    asset_id: str
    asset_name: str
    source_path: str
    dq_score: float | None
    last_scanned_at: datetime | None


class DQIssueRead(BaseModel):
    id: str
    asset_id: str
    column_id: str | None
    metric_name: str
    severity: str
    status: str
    delta_value: float | None
    current_score: float | None
    previous_score: float | None
    resolution_note: str | None = None

    model_config = {"from_attributes": True}


class DQIssueUpdate(BaseModel):
    status: str
    resolution_note: str | None = None


class DQScoreListResponse(BaseModel):
    data: list[DQScoreRead]
    meta: dict = Field(default_factory=dict)


class DQIssueListResponse(BaseModel):
    data: list[DQIssueRead]
    meta: dict = Field(default_factory=dict)


class DQIssueResponse(BaseModel):
    data: DQIssueRead
    meta: dict = Field(default_factory=dict)

