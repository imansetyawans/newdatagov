from uuid import uuid4

from sqlalchemy import Boolean, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.mixins import TimestampMixin


class ClassificationLabel(TimestampMixin, Base):
    __tablename__ = "classification_labels"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    color_key: Mapped[str] = mapped_column(String(32), nullable=False, default="custom")
    description: Mapped[str | None] = mapped_column(Text)
    masks_samples: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class ClassificationAssignment(TimestampMixin, Base):
    __tablename__ = "classification_assignments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    label: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    resource_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    resource_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="policy")
    policy_id: Mapped[str | None] = mapped_column(String(36), index=True)


class Policy(TimestampMixin, Base):
    __tablename__ = "policies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    policy_type: Mapped[str] = mapped_column(String(64), nullable=False, default="classification")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    rules: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    action: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_by_id: Mapped[str | None] = mapped_column(String(36), index=True)
    last_run_at: Mapped[str | None] = mapped_column(String(64))
