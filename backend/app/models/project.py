from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.asset import Asset


class CatalogueProject(TimestampMixin, Base):
    __tablename__ = "catalogue_projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(96), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    owner_id: Mapped[str | None] = mapped_column(String(36), index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", index=True)

    categories: Mapped[list["ProjectCategory"]] = relationship(
        "ProjectCategory",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    assets: Mapped[list["Asset"]] = relationship("Asset", back_populates="project")


class ProjectCategory(TimestampMixin, Base):
    __tablename__ = "project_categories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(ForeignKey("catalogue_projects.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(96), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", index=True)

    project: Mapped["CatalogueProject"] = relationship("CatalogueProject", back_populates="categories")
    assets: Mapped[list["Asset"]] = relationship("Asset", back_populates="category")
