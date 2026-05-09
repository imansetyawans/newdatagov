import sqlite3
import re

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_admin_db, get_audit_db, get_catalogue_db, get_classification_db
from app.middleware.auth import get_current_user, require_roles
from app.models import ClassificationLabel, Connector, User
from app.schemas.catalogue import (
    AssetDetailResponse,
    AssetListResponse,
    AssetSampleResponse,
    AssetRead,
    AssetUpdate,
    ColumnListResponse,
    ColumnMetadataGenerationResponse,
    ColumnRead,
    ColumnResponse,
    ColumnUpdate,
)
from app.services.catalogue_service import get_asset, list_assets, update_asset
from app.services.audit_service import write_audit_log
from app.services.metadata_ai_service import generate_column_descriptions
from app.services.upload_service import infer_standard_format


router = APIRouter(prefix="/api/v1", tags=["catalogue"])


@router.get("/assets", response_model=AssetListResponse)
def assets(
    q: str | None = None,
    source: str | None = None,
    type: str | None = Query(default=None),
    owner: str | None = None,
    db: Session = Depends(get_catalogue_db),
    _: User = Depends(get_current_user),
) -> AssetListResponse:
    data = list_assets(db=db, q=q, source=source, asset_type=type, owner_id=owner)
    return AssetListResponse(data=[AssetRead.model_validate(asset) for asset in data], meta={"count": len(data)})


@router.get("/assets/{asset_id}", response_model=AssetDetailResponse)
def asset_detail(
    asset_id: str,
    db: Session = Depends(get_catalogue_db),
    _: User = Depends(get_current_user),
) -> AssetDetailResponse:
    asset = get_asset(db, asset_id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return AssetDetailResponse(data=asset, meta={})


@router.patch("/assets/{asset_id}", response_model=AssetDetailResponse)
def asset_update(
    asset_id: str,
    payload: AssetUpdate,
    db: Session = Depends(get_catalogue_db),
    audit_db: Session = Depends(get_audit_db),
    user: User = Depends(require_roles(["admin", "editor"])),
) -> AssetDetailResponse:
    asset = get_asset(db, asset_id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    updated_asset = update_asset(db, asset, payload)
    write_audit_log(
        audit_db,
        user,
        action="asset_updated",
        resource_type="asset",
        resource_id=asset.id,
        event_type="catalogue",
        metadata={"name": asset.name},
    )
    audit_db.commit()
    return AssetDetailResponse(data=updated_asset, meta={})


@router.get("/assets/{asset_id}/columns", response_model=ColumnListResponse)
def asset_columns(
    asset_id: str,
    db: Session = Depends(get_catalogue_db),
    _: User = Depends(get_current_user),
) -> ColumnListResponse:
    asset = get_asset(db, asset_id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    columns = sorted(asset.columns, key=lambda column: column.ordinal_position)
    return ColumnListResponse(
        data=[ColumnRead.model_validate(column) for column in columns],
        meta={"count": len(columns)},
    )


@router.patch("/assets/{asset_id}/columns/{column_id}", response_model=ColumnResponse)
def column_update(
    asset_id: str,
    column_id: str,
    payload: ColumnUpdate,
    db: Session = Depends(get_catalogue_db),
    audit_db: Session = Depends(get_audit_db),
    user: User = Depends(require_roles(["admin", "editor"])),
) -> ColumnResponse:
    asset = get_asset(db, asset_id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    column = next((item for item in asset.columns if item.id == column_id), None)
    if column is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Column not found")
    if payload.description is not None:
        column.description = payload.description
    if payload.standard_format is not None:
        column.standard_format = payload.standard_format
    if payload.tags is not None:
        column.tags = payload.tags
    write_audit_log(
        audit_db,
        user,
        action="column_metadata_updated",
        resource_type="column",
        resource_id=column.id,
        event_type="catalogue",
        metadata={"asset": asset.name, "column": column.name},
    )
    audit_db.commit()
    db.commit()
    db.refresh(column)
    return ColumnResponse(data=ColumnRead.model_validate(column), meta={})


@router.post(
    "/assets/{asset_id}/columns/generate-metadata",
    response_model=ColumnMetadataGenerationResponse,
)
def generate_column_metadata(
    asset_id: str,
    db: Session = Depends(get_catalogue_db),
    audit_db: Session = Depends(get_audit_db),
    user: User = Depends(require_roles(["admin", "editor"])),
) -> ColumnMetadataGenerationResponse:
    asset = get_asset(db, asset_id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    descriptions, provider = generate_column_descriptions(asset)
    updated_count = 0
    for column in asset.columns:
        description = descriptions.get(column.id)
        if description:
            column.description = description
            updated_count += 1
    db.commit()
    db.refresh(asset)
    write_audit_log(
        audit_db,
        user,
        action="column_metadata_generated",
        resource_type="asset",
        resource_id=asset.id,
        event_type="catalogue",
        metadata={"updated_count": updated_count, "provider": provider},
    )
    audit_db.commit()
    return ColumnMetadataGenerationResponse(
        data=asset,
        meta={"provider": provider, "updated_count": updated_count},
    )


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
INTEGER_PATTERN = re.compile(r"^-?\d+$")
DECIMAL_PATTERN = re.compile(r"^-?\d+\.\d+$")
UUID_PATTERN = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
URL_PATTERN = re.compile(r"^https?://\S+$", re.IGNORECASE)


def _infer_standard_format(column_name: str, data_type: str, sample_values: list[object]) -> str | None:
    values = [str(value).strip() for value in sample_values if value is not None and str(value).strip()]
    if not values:
        return None

    lowered_values = [value.lower() for value in values]
    lower_name = column_name.lower()
    lower_type = data_type.lower()

    if all(EMAIL_PATTERN.match(value) for value in values):
        return "valid email address"
    if all(DATE_PATTERN.match(value) for value in values):
        return "YYYY-MM-DD date"
    if all(UUID_PATTERN.match(value) for value in values):
        return "UUID"
    if all(URL_PATTERN.match(value) for value in values):
        return "URL"
    if all(value in {"true", "false", "0", "1", "yes", "no"} for value in lowered_values):
        return "boolean value"
    if all(INTEGER_PATTERN.match(value) for value in values):
        return "integer identifier" if lower_name == "id" or lower_name.endswith("_id") else "integer number"
    if all(DECIMAL_PATTERN.match(value) or INTEGER_PATTERN.match(value) for value in values):
        return "decimal number"
    if 1 < len(set(values)) <= 5 and all(len(value) <= 32 for value in values):
        return f"controlled vocabulary: {', '.join(values)}"
    if all(value == value.lower() for value in values if any(character.isalpha() for character in value)):
        return "lowercase text"
    if "char" in lower_type or "text" in lower_type:
        return "free text"
    return None


def _is_uploaded_asset(asset) -> bool:
    return asset.connector_id is None and asset.source_path.startswith("upload.")


@router.post(
    "/assets/{asset_id}/columns/detect-formats",
    response_model=ColumnMetadataGenerationResponse,
)
def detect_column_formats(
    asset_id: str,
    catalogue_db: Session = Depends(get_catalogue_db),
    admin_db: Session = Depends(get_admin_db),
    audit_db: Session = Depends(get_audit_db),
    user: User = Depends(require_roles(["admin", "editor"])),
) -> ColumnMetadataGenerationResponse:
    asset = get_asset(catalogue_db, asset_id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    if _is_uploaded_asset(asset):
        updated_count = 0
        detected_formats: dict[str, str] = {}
        for column in sorted(asset.columns, key=lambda item: item.ordinal_position):
            detected_format = infer_standard_format(column.name, column.data_type, column.sample_values)
            if detected_format:
                column.standard_format = detected_format
                detected_formats[column.name] = detected_format
                updated_count += 1
        write_audit_log(
            audit_db,
            user,
            action="column_formats_detected",
            resource_type="asset",
            resource_id=asset.id,
            event_type="catalogue",
            metadata={"updated_count": updated_count, "columns": sorted(detected_formats)},
        )
        audit_db.commit()
        catalogue_db.commit()
        catalogue_db.refresh(asset)
        return ColumnMetadataGenerationResponse(
            data=asset,
            meta={"provider": "stored-sample-detector", "updated_count": updated_count, "detected_formats": detected_formats},
        )
    if asset.asset_type != "table" or asset.connector_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Format detection is available for scanned tables only")

    connector = admin_db.get(Connector, asset.connector_id)
    if connector is None or connector.connector_type != "sqlite":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Format detection is available for SQLite connectors only")

    updated_count = 0
    detected_formats: dict[str, str] = {}
    try:
        with sqlite3.connect(str(connector.config_encrypted.get("database_path", "datagov.db"))) as connection:
            for column in sorted(asset.columns, key=lambda item: item.ordinal_position):
                rows = connection.execute(
                    f"""
                    select distinct {_quote_identifier(column.name)}
                    from {_quote_identifier(asset.name)}
                    where {_quote_identifier(column.name)} is not null
                    limit ?
                    """,
                    (25,),
                ).fetchall()
                detected_format = _infer_standard_format(column.name, column.data_type, [row[0] for row in rows])
                if detected_format:
                    column.standard_format = detected_format
                    detected_formats[column.name] = detected_format
                    updated_count += 1
    except sqlite3.Error as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unable to detect standard formats: {exc}") from exc

    write_audit_log(
        audit_db,
        user,
        action="column_formats_detected",
        resource_type="asset",
        resource_id=asset.id,
        event_type="catalogue",
        metadata={"updated_count": updated_count, "columns": sorted(detected_formats)},
    )
    audit_db.commit()
    catalogue_db.commit()
    catalogue_db.refresh(asset)
    return ColumnMetadataGenerationResponse(
        data=asset,
        meta={"provider": "sample-detector", "updated_count": updated_count, "detected_formats": detected_formats},
    )


def _quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


SENSITIVE_LABELS = {"PII", "Sensitive", "Restricted"}
MASKED_SAMPLE_VALUE = "*****"


@router.get("/assets/{asset_id}/sample", response_model=AssetSampleResponse)
def asset_sample(
    asset_id: str,
    limit: int = Query(default=5, ge=1, le=25),
    catalogue_db: Session = Depends(get_catalogue_db),
    admin_db: Session = Depends(get_admin_db),
    classification_db: Session = Depends(get_classification_db),
    audit_db: Session = Depends(get_audit_db),
    user: User = Depends(get_current_user),
) -> AssetSampleResponse:
    asset = get_asset(catalogue_db, asset_id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    if _is_uploaded_asset(asset):
        columns = sorted(asset.columns, key=lambda column: column.ordinal_position)
        masking_labels = {
            label.name
            for label in classification_db.scalars(
                select(ClassificationLabel).where(ClassificationLabel.masks_samples.is_(True))
            ).all()
        } | SENSITIVE_LABELS
        sensitive_columns = {
            column.name
            for column in columns
            if masking_labels.intersection(set(column.classifications))
        }
        column_samples = {
            column.name: [MASKED_SAMPLE_VALUE] if column.name in sensitive_columns and column.sample_values else column.sample_values[:5]
            for column in columns
        }
        write_audit_log(
            audit_db,
            user,
            action="sample_viewed",
            resource_type="asset",
            resource_id=asset.id,
            event_type="data_access",
            metadata={"row_count": 0, "masked_columns": sorted(sensitive_columns), "source": "stored_column_samples"},
        )
        audit_db.commit()
        return AssetSampleResponse(
            data=[],
            meta={
                "count": 0,
                "masked_columns": sorted(sensitive_columns),
                "column_samples": column_samples,
                "source": "stored_column_samples",
            },
        )
    if asset.asset_type != "table" or asset.connector_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sample data is available for scanned tables only")

    connector = admin_db.get(Connector, asset.connector_id)
    if connector is None or connector.connector_type != "sqlite":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sample data is available for SQLite connectors only")

    columns = sorted(asset.columns, key=lambda column: column.ordinal_position)
    if not columns:
        return AssetSampleResponse(data=[], meta={"count": 0, "masked_columns": []})

    masking_labels = {
        label.name
        for label in classification_db.scalars(
            select(ClassificationLabel).where(ClassificationLabel.masks_samples.is_(True))
        ).all()
    } | SENSITIVE_LABELS
    sensitive_columns = {
        column.name
        for column in columns
        if masking_labels.intersection(set(column.classifications))
    }
    field_list = ", ".join(_quote_identifier(column.name) for column in columns)
    query = f"select {field_list} from {_quote_identifier(asset.name)} limit ?"
    try:
        with sqlite3.connect(str(connector.config_encrypted.get("database_path", "datagov.db"))) as connection:
            rows = connection.execute(query, (limit,)).fetchall()
            column_samples = {}
            for column in columns:
                if column.name in sensitive_columns:
                    column_samples[column.name] = [MASKED_SAMPLE_VALUE]
                    continue
                sample_rows = connection.execute(
                    f"""
                    select distinct {_quote_identifier(column.name)}
                    from {_quote_identifier(asset.name)}
                    where {_quote_identifier(column.name)} is not null
                    limit ?
                    """,
                    (5,),
                ).fetchall()
                column_samples[column.name] = [row[0] for row in sample_rows]
    except sqlite3.Error as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unable to read sample data: {exc}") from exc

    data = []
    for row in rows:
        item = {}
        for column, value in zip(columns, row, strict=True):
            item[column.name] = MASKED_SAMPLE_VALUE if column.name in sensitive_columns and value is not None else value
        data.append(item)

    write_audit_log(
        audit_db,
        user,
        action="sample_viewed",
        resource_type="asset",
        resource_id=asset.id,
        event_type="data_access",
        metadata={"row_count": len(data), "masked_columns": sorted(sensitive_columns)},
    )
    audit_db.commit()
    return AssetSampleResponse(
        data=data,
        meta={
            "count": len(data),
            "masked_columns": sorted(sensitive_columns),
            "column_samples": column_samples,
        },
    )


@router.get("/search", response_model=AssetListResponse)
def search(
    q: str,
    limit: int = 20,
    db: Session = Depends(get_catalogue_db),
    _: User = Depends(get_current_user),
) -> AssetListResponse:
    data = list_assets(db=db, q=q)[:limit]
    return AssetListResponse(data=[AssetRead.model_validate(asset) for asset in data], meta={"count": len(data)})
