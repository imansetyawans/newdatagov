from uuid import uuid4

from sqlalchemy import ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.mixins import TimestampMixin


class LineageEdge(TimestampMixin, Base):
    __tablename__ = "lineage_edges"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    upstream_asset_id: Mapped[str] = mapped_column(ForeignKey("assets.id"), index=True, nullable=False)
    downstream_asset_id: Mapped[str] = mapped_column(ForeignKey("assets.id"), index=True, nullable=False)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False, default="manual")
    confidence: Mapped[float | None]
    edge_metadata: Mapped[dict] = mapped_column("metadata", JSON, default=dict, nullable=False)
