from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.mixins import TimestampMixin


class DQIssue(TimestampMixin, Base):
    __tablename__ = "dq_issues"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    asset_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    column_id: Mapped[str | None] = mapped_column(String(36), index=True)
    metric_name: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False, default="warning")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="open", index=True)
    delta_value: Mapped[float | None]
    current_score: Mapped[float | None]
    previous_score: Mapped[float | None]
    resolution_note: Mapped[str | None] = mapped_column(Text)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime)
    resolved_by_id: Mapped[str | None] = mapped_column(String(36))
