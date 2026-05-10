from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import Asset, CatalogueProject, ProjectCategory
from app.schemas.catalogue import (
    CatalogueProjectCreate,
    CatalogueProjectRead,
    CatalogueProjectUpdate,
    ProjectCategoryCreate,
    ProjectCategoryRead,
    ProjectCategoryUpdate,
)


def normalize_code(value: str) -> str:
    return "_".join(value.strip().lower().replace("-", "_").split())


def list_projects(db: Session, include_inactive: bool = False) -> list[CatalogueProject]:
    statement = select(CatalogueProject).options(selectinload(CatalogueProject.categories)).order_by(CatalogueProject.name)
    if not include_inactive:
        statement = statement.where(CatalogueProject.status == "active")
    return list(db.scalars(statement).all())


def get_project(db: Session, project_id: str) -> CatalogueProject | None:
    return db.scalar(
        select(CatalogueProject)
        .options(selectinload(CatalogueProject.categories))
        .where(CatalogueProject.id == project_id)
    )


def create_project(db: Session, payload: CatalogueProjectCreate) -> CatalogueProject:
    project = CatalogueProject(
        name=payload.name.strip(),
        code=normalize_code(payload.code or payload.name),
        description=payload.description,
        owner_id=payload.owner_id,
        status=payload.status,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def update_project(db: Session, project: CatalogueProject, payload: CatalogueProjectUpdate) -> CatalogueProject:
    if payload.name is not None:
        project.name = payload.name.strip()
    if payload.code is not None:
        project.code = normalize_code(payload.code)
    if payload.description is not None:
        project.description = payload.description
    if payload.owner_id is not None:
        project.owner_id = payload.owner_id
    if payload.status is not None:
        project.status = payload.status
    db.commit()
    db.refresh(project)
    return project


def list_categories(db: Session, project_id: str | None = None, include_inactive: bool = False) -> list[ProjectCategory]:
    statement = select(ProjectCategory).order_by(ProjectCategory.name)
    if project_id:
        statement = statement.where(ProjectCategory.project_id == project_id)
    if not include_inactive:
        statement = statement.where(ProjectCategory.status == "active")
    return list(db.scalars(statement).all())


def get_category(db: Session, category_id: str) -> ProjectCategory | None:
    return db.get(ProjectCategory, category_id)


def create_category(db: Session, payload: ProjectCategoryCreate) -> ProjectCategory:
    category = ProjectCategory(
        project_id=payload.project_id,
        name=payload.name.strip(),
        code=normalize_code(payload.code or payload.name),
        description=payload.description,
        status=payload.status,
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def update_category(db: Session, category: ProjectCategory, payload: ProjectCategoryUpdate) -> ProjectCategory:
    if payload.name is not None:
        category.name = payload.name.strip()
    if payload.code is not None:
        category.code = normalize_code(payload.code)
    if payload.description is not None:
        category.description = payload.description
    if payload.status is not None:
        category.status = payload.status
    db.commit()
    db.refresh(category)
    return category


def project_to_read(db: Session, project: CatalogueProject, include_inactive_categories: bool = False) -> CatalogueProjectRead:
    category_counts = {
        row.category_id: row.count
        for row in db.execute(
            select(Asset.category_id, func.count(Asset.id).label("count"))
            .where(Asset.project_id == project.id, Asset.deleted_at.is_(None), Asset.category_id.is_not(None))
            .group_by(Asset.category_id)
        ).all()
    }
    project_count = db.scalar(
        select(func.count(Asset.id)).where(Asset.project_id == project.id, Asset.deleted_at.is_(None))
    ) or 0
    categories = [
        ProjectCategoryRead.model_validate(category).model_copy(
            update={"asset_count": int(category_counts.get(category.id, 0))}
        )
        for category in sorted(project.categories, key=lambda item: item.name)
        if include_inactive_categories or category.status == "active"
    ]
    return CatalogueProjectRead.model_validate(project).model_copy(
        update={"asset_count": int(project_count), "categories": categories}
    )


def category_to_read(db: Session, category: ProjectCategory) -> ProjectCategoryRead:
    count = db.scalar(
        select(func.count(Asset.id)).where(Asset.category_id == category.id, Asset.deleted_at.is_(None))
    ) or 0
    return ProjectCategoryRead.model_validate(category).model_copy(update={"asset_count": int(count)})


def validate_project_category(db: Session, project_id: str | None, category_id: str | None) -> None:
    project_id = project_id or None
    category_id = category_id or None
    if project_id is None and category_id is None:
        return
    if project_id is None and category_id is not None:
        raise ValueError("Project is required when category is selected")
    project = db.get(CatalogueProject, project_id)
    if project is None or project.status != "active":
        raise ValueError("Selected project is not available")
    if category_id is None:
        return
    category = db.get(ProjectCategory, category_id)
    if category is None or category.status != "active" or category.project_id != project_id:
        raise ValueError("Selected category is not available for this project")
