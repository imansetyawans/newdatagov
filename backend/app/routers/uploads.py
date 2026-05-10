from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_audit_db, get_catalogue_db, get_classification_db, get_policy_db, get_quality_db
from app.middleware.auth import require_roles
from app.models import User
from app.schemas.catalogue import AssetDetailResponse
from app.services.audit_service import write_audit_log
from app.services.metadata_ai_service import generate_column_descriptions
from app.services.policy_engine import evaluate_policies
from app.services.project_service import validate_project_category
from app.services.upload_service import (
    calculate_uploaded_quality,
    normalize_identifier,
    parse_dataset_upload,
    upsert_uploaded_asset,
)


router = APIRouter(prefix="/api/v1/uploads", tags=["uploads"])


@router.post("/datasets", response_model=AssetDetailResponse)
async def upload_dataset(
    file: UploadFile = File(...),
    schema_name: str = Form(...),
    table_name: str = Form(...),
    description: str | None = Form(default=None),
    project_id: str | None = Form(default=None),
    category_id: str | None = Form(default=None),
    catalogue_db: Session = Depends(get_catalogue_db),
    quality_db: Session = Depends(get_quality_db),
    policy_db: Session = Depends(get_policy_db),
    classification_db: Session = Depends(get_classification_db),
    audit_db: Session = Depends(get_audit_db),
    user: User = Depends(require_roles(["admin", "editor"])),
) -> AssetDetailResponse:
    filename = file.filename or "uploaded_dataset.csv"
    content = await file.read()
    try:
        parsed = parse_dataset_upload(filename, content)
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to read file as UTF-8 CSV") from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    normalized_schema = normalize_identifier(schema_name)
    normalized_table = normalize_identifier(table_name)
    if not normalized_schema or not normalized_table:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Schema name and table name are required")
    try:
        validate_project_category(catalogue_db, project_id, category_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    asset = upsert_uploaded_asset(
        catalogue_db,
        schema_name=normalized_schema,
        table_name=normalized_table,
        table_description=description,
        parsed=parsed,
        project_id=project_id,
        category_id=category_id,
    )
    descriptions, provider = generate_column_descriptions(asset)
    updated_descriptions = 0
    for column in asset.columns:
        description_value = descriptions.get(column.id)
        if description_value:
            column.description = description_value
            updated_descriptions += 1

    dq_issues = calculate_uploaded_quality(catalogue_db, quality_db, asset, parsed)
    policies_applied = evaluate_policies(policy_db, classification_db, catalogue_db, asset)

    write_audit_log(
        audit_db,
        user,
        action="dataset_uploaded",
        resource_type="asset",
        resource_id=asset.id,
        event_type="catalogue",
        metadata={
            "filename": filename,
            "schema_name": normalized_schema,
            "table_name": normalized_table,
            "rows": len(parsed.rows),
            "columns": len(parsed.headers),
            "project_id": project_id,
            "category_id": category_id,
        },
    )
    write_audit_log(
        audit_db,
        user,
        action="column_metadata_generated",
        resource_type="asset",
        resource_id=asset.id,
        event_type="catalogue",
        metadata={"updated_count": updated_descriptions, "provider": provider},
    )
    write_audit_log(
        audit_db,
        user,
        action="uploaded_dataset_quality_processed",
        resource_type="asset",
        resource_id=asset.id,
        event_type="quality",
        metadata={"dq_score": asset.dq_score, "issues_raised": dq_issues},
    )
    write_audit_log(
        audit_db,
        user,
        action="uploaded_dataset_policies_applied",
        resource_type="asset",
        resource_id=asset.id,
        event_type="governance",
        metadata={"policies_applied": policies_applied},
    )

    catalogue_db.commit()
    quality_db.commit()
    classification_db.commit()
    audit_db.commit()
    catalogue_db.refresh(asset)
    return AssetDetailResponse(
        data=asset,
        meta={
            "filename": filename,
            "rows": len(parsed.rows),
            "columns": len(parsed.headers),
            "metadata_provider": provider,
            "metadata_updated": updated_descriptions,
            "dq_issues": dq_issues,
            "policies_applied": policies_applied,
        },
    )
