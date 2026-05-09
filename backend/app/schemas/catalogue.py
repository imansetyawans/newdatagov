from datetime import datetime

from pydantic import BaseModel, Field


class ColumnRead(BaseModel):
    id: str
    name: str
    data_type: str
    ordinal_position: int
    nullable: bool
    description: str | None = None
    standard_format: str | None = None
    tags: list[str] = Field(default_factory=list)
    classifications: list[str] = Field(default_factory=list)
    completeness_score: float | None = None
    uniqueness_score: float | None = None
    consistency_score: float | None = None
    accuracy_score: float | None = None

    model_config = {"from_attributes": True}


class AssetRead(BaseModel):
    id: str
    connector_id: str | None = None
    name: str
    source_path: str
    asset_type: str
    schema_name: str | None = None
    description: str | None = None
    owner_id: str | None = None
    tags: list[str] = Field(default_factory=list)
    classifications: list[str] = Field(default_factory=list)
    dq_score: float | None = None
    row_count: int | None = None
    last_scanned_at: datetime | None = None

    model_config = {"from_attributes": True}


class AssetDetailRead(AssetRead):
    columns: list[ColumnRead] = Field(default_factory=list)


class AssetUpdate(BaseModel):
    description: str | None = None
    owner_id: str | None = None
    tags: list[str] | None = None


class ColumnUpdate(BaseModel):
    description: str | None = None
    standard_format: str | None = None
    tags: list[str] | None = None


class AssetListResponse(BaseModel):
    data: list[AssetRead]
    meta: dict = Field(default_factory=dict)


class AssetDetailResponse(BaseModel):
    data: AssetDetailRead
    meta: dict = Field(default_factory=dict)


class ColumnListResponse(BaseModel):
    data: list[ColumnRead]
    meta: dict = Field(default_factory=dict)


class ColumnResponse(BaseModel):
    data: ColumnRead
    meta: dict = Field(default_factory=dict)


class ColumnMetadataGenerationResponse(BaseModel):
    data: AssetDetailRead
    meta: dict = Field(default_factory=dict)


class AssetSampleResponse(BaseModel):
    data: list[dict]
    meta: dict = Field(default_factory=dict)
