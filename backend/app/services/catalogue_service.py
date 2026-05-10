from datetime import datetime

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.connectors.base import DiscoveredAsset
from app.models import Asset, Column
from app.schemas.catalogue import AssetUpdate


def list_assets(
    db: Session,
    q: str | None = None,
    source: str | None = None,
    asset_type: str | None = None,
    owner_id: str | None = None,
    project_id: str | None = None,
    category_id: str | None = None,
    unassigned: bool = False,
) -> list[Asset]:
    statement = (
        select(Asset)
        .options(selectinload(Asset.project), selectinload(Asset.category))
        .where(Asset.deleted_at.is_(None))
        .order_by(Asset.name)
    )
    if q:
        like = f"%{q}%"
        statement = statement.where(
            or_(
                Asset.name.ilike(like),
                Asset.source_path.ilike(like),
                Asset.description.ilike(like),
            )
        )
    if source:
        statement = statement.where(Asset.source_path.ilike(f"%{source}%"))
    if asset_type:
        statement = statement.where(Asset.asset_type == asset_type)
    if owner_id:
        statement = statement.where(Asset.owner_id == owner_id)
    if project_id:
        statement = statement.where(Asset.project_id == project_id)
    if category_id:
        statement = statement.where(Asset.category_id == category_id)
    if unassigned:
        statement = statement.where(Asset.project_id.is_(None))
    return list(db.scalars(statement).all())


def get_asset(db: Session, asset_id: str) -> Asset | None:
    return db.scalar(
        select(Asset)
        .options(selectinload(Asset.columns), selectinload(Asset.project), selectinload(Asset.category))
        .where(Asset.id == asset_id, Asset.deleted_at.is_(None))
    )


def update_asset(db: Session, asset: Asset, payload: AssetUpdate) -> Asset:
    if payload.description is not None:
        asset.description = payload.description
    if payload.owner_id is not None:
        asset.owner_id = payload.owner_id
    if payload.tags is not None:
        asset.tags = payload.tags
    if payload.project_id is not None:
        asset.project_id = payload.project_id or None
        if asset.project_id is None:
            asset.category_id = None
    if payload.category_id is not None:
        asset.category_id = payload.category_id or None
    db.commit()
    db.refresh(asset)
    return asset


def mark_missing_connector_assets_deleted(
    db: Session,
    connector_id: str,
    active_source_paths: set[str],
    scanned_at: datetime,
) -> None:
    assets = db.scalars(
        select(Asset).where(
            Asset.connector_id == connector_id,
            Asset.deleted_at.is_(None),
        )
    ).all()
    for asset in assets:
        if asset.source_path not in active_source_paths:
            asset.deleted_at = scanned_at


def upsert_discovered_asset(
    db: Session,
    connector_id: str,
    discovered: DiscoveredAsset,
    scanned_at: datetime,
    project_id: str | None = None,
    category_id: str | None = None,
) -> tuple[Asset, int]:
    asset = db.scalar(
        select(Asset).where(
            Asset.connector_id == connector_id,
            Asset.source_path == discovered.source_path,
        )
    )
    if asset is None:
        asset = Asset(
            connector_id=connector_id,
            name=discovered.name,
            source_path=discovered.source_path,
            asset_type=discovered.asset_type,
            schema_name=discovered.schema_name,
            project_id=project_id,
            category_id=category_id,
        )
        db.add(asset)

    if project_id is not None:
        asset.project_id = project_id
        asset.category_id = category_id
    asset.row_count = discovered.row_count
    asset.last_scanned_at = scanned_at
    asset.deleted_at = None

    existing_columns = {column.name: column for column in asset.columns}
    seen_column_names: set[str] = set()
    for discovered_column in discovered.columns:
        seen_column_names.add(discovered_column.name)
        column = existing_columns.get(discovered_column.name)
        if column is None:
            column = Column(asset=asset, name=discovered_column.name, data_type=discovered_column.data_type)
            db.add(column)
        column.data_type = discovered_column.data_type
        column.ordinal_position = discovered_column.ordinal_position
        column.nullable = discovered_column.nullable

    for column_name, column in existing_columns.items():
        if column_name not in seen_column_names:
            db.delete(column)

    return asset, len(discovered.columns)
