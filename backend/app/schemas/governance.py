from datetime import datetime

from pydantic import BaseModel, Field


class PolicyRead(BaseModel):
    id: str
    name: str
    policy_type: str
    status: str
    rules: list = Field(default_factory=list)
    action: dict = Field(default_factory=dict)
    created_by_id: str | None = None
    last_run_at: str | None = None

    model_config = {"from_attributes": True}


class PolicyCreate(BaseModel):
    name: str
    policy_type: str = "classification"
    status: str = "active"
    rules: list[dict] = Field(default_factory=list)
    action: dict = Field(default_factory=dict)


class PolicyUpdate(BaseModel):
    name: str | None = None
    status: str | None = None
    rules: list[dict] | None = None
    action: dict | None = None


class PolicyListResponse(BaseModel):
    data: list[PolicyRead]
    meta: dict = Field(default_factory=dict)


class PolicyResponse(BaseModel):
    data: PolicyRead
    meta: dict = Field(default_factory=dict)


class ClassificationLabelRead(BaseModel):
    id: str
    name: str
    color_key: str
    description: str | None = None
    masks_samples: bool = False

    model_config = {"from_attributes": True}


class ClassificationLabelCreate(BaseModel):
    name: str
    color_key: str = "custom"
    description: str | None = None
    masks_samples: bool = False


class ClassificationLabelUpdate(BaseModel):
    name: str | None = None
    color_key: str | None = None
    description: str | None = None
    masks_samples: bool | None = None


class ClassificationLabelListResponse(BaseModel):
    data: list[ClassificationLabelRead]
    meta: dict = Field(default_factory=dict)


class ClassificationLabelResponse(BaseModel):
    data: ClassificationLabelRead
    meta: dict = Field(default_factory=dict)


class CoverageResponse(BaseModel):
    data: dict
    meta: dict = Field(default_factory=dict)


class AuditLogRead(BaseModel):
    id: str
    user_id: str | None
    user_email: str | None = None
    user_name: str | None = None
    event_type: str
    action: str
    resource_type: str
    resource_id: str | None
    event_metadata: dict = Field(default_factory=dict)
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogListResponse(BaseModel):
    data: list[AuditLogRead]
    meta: dict = Field(default_factory=dict)
