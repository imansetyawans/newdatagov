from uuid import uuid4
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.asset import Asset


class Column(TimestampMixin, Base):
    __tablename__ = "columns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    asset_id: Mapped[str] = mapped_column(ForeignKey("assets.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    data_type: Mapped[str] = mapped_column(String(128), nullable=False)
    ordinal_position: Mapped[int] = mapped_column(nullable=False, default=0)
    nullable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    standard_format: Mapped[str | None] = mapped_column(Text)
    sample_values: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    tags: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    classifications: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    completeness_score: Mapped[float | None]
    uniqueness_score: Mapped[float | None]
    consistency_score: Mapped[float | None]
    accuracy_score: Mapped[float | None]

    asset: Mapped["Asset"] = relationship(back_populates="columns")
