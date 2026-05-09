from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.mixins import TimestampMixin


class Scan(TimestampMixin, Base):
    __tablename__ = "scans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    connector_ids: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    scan_type: Mapped[str] = mapped_column(String(64), nullable=False, default="full")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)
    assets_scanned: Mapped[int] = mapped_column(default=0, nullable=False)
    columns_scanned: Mapped[int] = mapped_column(default=0, nullable=False)
    dq_issues_raised: Mapped[int] = mapped_column(default=0, nullable=False)
    policies_applied: Mapped[int] = mapped_column(default=0, nullable=False)
    schedule_cron: Mapped[str | None] = mapped_column(String(128))
    errors: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

