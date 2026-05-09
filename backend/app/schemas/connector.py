from datetime import datetime

from pydantic import BaseModel, Field


class ConnectorCreate(BaseModel):
    name: str
    connector_type: str = "sqlite"
    config: dict = Field(default_factory=dict)


class ConnectorRead(BaseModel):
    id: str
    name: str
    connector_type: str
    config_encrypted: dict = Field(default_factory=dict)
    status: str
    last_tested_at: datetime | None = None

    model_config = {"from_attributes": True}


class ConnectorListResponse(BaseModel):
    data: list[ConnectorRead]
    meta: dict = Field(default_factory=dict)


class ConnectorSchemaRead(BaseModel):
    name: str
    asset_names: list[str] = Field(default_factory=list)


class ConnectorScopeUpdate(BaseModel):
    catalogue_scope: dict = Field(default_factory=dict)


class ConnectorResponse(BaseModel):
    data: ConnectorRead
    meta: dict = Field(default_factory=dict)


class ConnectorSchemaListResponse(BaseModel):
    data: list[ConnectorSchemaRead]
    meta: dict = Field(default_factory=dict)


class ConnectorTestResponse(BaseModel):
    data: dict
    meta: dict = Field(default_factory=dict)
