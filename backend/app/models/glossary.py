from uuid import uuid4

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.mixins import TimestampMixin


class GlossaryTerm(TimestampMixin, Base):
    __tablename__ = "glossary_terms"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    term: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    definition: Mapped[str] = mapped_column(Text, nullable=False)
    synonyms: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    related_term_ids: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    linked_asset_ids: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    linked_column_ids: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="draft", nullable=False)
    steward_id: Mapped[str | None] = mapped_column(String(36))
