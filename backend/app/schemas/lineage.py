from datetime import datetime

from pydantic import BaseModel, Field


class LineageEdgeRead(BaseModel):
    id: str
    upstream_asset_id: str
    downstream_asset_id: str
    source_type: str
    confidence: float | None = None
    edge_metadata: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LineageEdgeCreate(BaseModel):
    upstream_asset_id: str
    downstream_asset_id: str
    source_type: str = "manual"
    confidence: float | None = 1.0
    edge_metadata: dict = Field(default_factory=dict)


class LineageGraphResponse(BaseModel):
    data: dict
    meta: dict = Field(default_factory=dict)


class LineageEdgeResponse(BaseModel):
    data: LineageEdgeRead
    meta: dict = Field(default_factory=dict)


class LineageEdgeListResponse(BaseModel):
    data: list[LineageEdgeRead]
    meta: dict = Field(default_factory=dict)
