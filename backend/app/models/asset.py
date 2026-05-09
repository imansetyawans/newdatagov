from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import DateTime, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.column import Column


class Asset(TimestampMixin, Base):
    __tablename__ = "assets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    connector_id: Mapped[str | None] = mapped_column(String(36), index=True)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    source_path: Mapped[str] = mapped_column(String(512), index=True, nullable=False)
    asset_type: Mapped[str] = mapped_column(String(64), nullable=False, default="table")
    schema_name: Mapped[str | None] = mapped_column(String(255), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    owner_id: Mapped[str | None] = mapped_column(String(36), index=True)
    tags: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    classifications: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    dq_score: Mapped[float | None]
    row_count: Mapped[int | None]
    last_scanned_at: Mapped[datetime | None] = mapped_column(DateTime)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, index=True)

    columns: Mapped[list["Column"]] = relationship(back_populates="asset", cascade="all, delete-orphan")
