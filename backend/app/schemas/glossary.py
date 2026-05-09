from datetime import datetime

from pydantic import BaseModel, Field


class GlossaryTermRead(BaseModel):
    id: str
    term: str
    definition: str
    synonyms: list[str] = Field(default_factory=list)
    related_term_ids: list[str] = Field(default_factory=list)
    linked_asset_ids: list[str] = Field(default_factory=list)
    linked_column_ids: list[str] = Field(default_factory=list)
    status: str
    steward_id: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GlossaryTermCreate(BaseModel):
    term: str
    definition: str
    synonyms: list[str] = Field(default_factory=list)
    related_term_ids: list[str] = Field(default_factory=list)
    linked_asset_ids: list[str] = Field(default_factory=list)
    linked_column_ids: list[str] = Field(default_factory=list)
    status: str = "draft"
    steward_id: str | None = None


class GlossaryTermUpdate(BaseModel):
    term: str | None = None
    definition: str | None = None
    synonyms: list[str] | None = None
    related_term_ids: list[str] | None = None
    linked_asset_ids: list[str] | None = None
    linked_column_ids: list[str] | None = None
    status: str | None = None
    steward_id: str | None = None


class GlossarySuggestionRead(BaseModel):
    term_id: str
    term: str
    resource_type: str
    resource_id: str
    resource_name: str
    confidence: float


class GlossaryTermResponse(BaseModel):
    data: GlossaryTermRead
    meta: dict = Field(default_factory=dict)


class GlossaryTermListResponse(BaseModel):
    data: list[GlossaryTermRead]
    meta: dict = Field(default_factory=dict)


class GlossarySuggestionListResponse(BaseModel):
    data: list[GlossarySuggestionRead]
    meta: dict = Field(default_factory=dict)
