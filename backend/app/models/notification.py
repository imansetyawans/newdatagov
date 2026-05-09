from uuid import uuid4

from sqlalchemy import Boolean, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.mixins import TimestampMixin


class NotificationSetting(TimestampMixin, Base):
    __tablename__ = "notification_settings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    channel: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    target: Mapped[str] = mapped_column(String(512), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    events: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
