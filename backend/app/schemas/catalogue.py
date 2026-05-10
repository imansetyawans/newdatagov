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
    sample_values: list = Field(default_factory=list)
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
    project_id: str | None = None
    category_id: str | None = None
    project_name: str | None = None
    category_name: str | None = None
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
    project_id: str | None = None
    category_id: str | None = None


class ProjectCategoryBase(BaseModel):
    name: str
    code: str
    description: str | None = None
    status: str = "active"


class ProjectCategoryCreate(ProjectCategoryBase):
    project_id: str


class ProjectCategoryUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    description: str | None = None
    status: str | None = None


class ProjectCategoryRead(ProjectCategoryBase):
    id: str
    project_id: str
    asset_count: int = 0

    model_config = {"from_attributes": True}


class CatalogueProjectBase(BaseModel):
    name: str
    code: str
    description: str | None = None
    owner_id: str | None = None
    status: str = "active"


class CatalogueProjectCreate(CatalogueProjectBase):
    pass


class CatalogueProjectUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    description: str | None = None
    owner_id: str | None = None
    status: str | None = None


class CatalogueProjectRead(CatalogueProjectBase):
    id: str
    asset_count: int = 0
    categories: list[ProjectCategoryRead] = Field(default_factory=list)

    model_config = {"from_attributes": True}


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


class ProjectListResponse(BaseModel):
    data: list[CatalogueProjectRead]
    meta: dict = Field(default_factory=dict)


class ProjectResponse(BaseModel):
    data: CatalogueProjectRead
    meta: dict = Field(default_factory=dict)


class CategoryListResponse(BaseModel):
    data: list[ProjectCategoryRead]
    meta: dict = Field(default_factory=dict)


class CategoryResponse(BaseModel):
    data: ProjectCategoryRead
    meta: dict = Field(default_factory=dict)
