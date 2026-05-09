from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_admin_db, get_audit_db, get_catalogue_db, get_classification_db, get_policy_db
from app.middleware.auth import get_current_user, require_roles
from app.models import Asset, AuditLog, ClassificationAssignment, ClassificationLabel, Column, Policy, User
from app.schemas.governance import (
    AuditLogListResponse,
    AuditLogRead,
    ClassificationLabelCreate,
    ClassificationLabelListResponse,
    ClassificationLabelRead,
    ClassificationLabelResponse,
    ClassificationLabelUpdate,
    CoverageResponse,
    PolicyCreate,
    PolicyListResponse,
    PolicyRead,
    PolicyResponse,
    PolicyUpdate,
)
from app.services.audit_service import write_audit_log
from app.services.classification_service import ensure_default_classification_labels
from app.services.policy_engine import recalculate_policy_classifications


router = APIRouter(prefix="/api/v1", tags=["governance"])


def _policy_classification(policy: Policy) -> str | None:
    classification = policy.action.get("classification")
    return str(classification) if classification else None


def _require_label_exists(db: Session, name: str) -> ClassificationLabel:
    label = db.scalar(select(ClassificationLabel).where(ClassificationLabel.name == name.strip()))
    if label is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Classification "{name}" does not exist. Create it in Classification management first.',
        )
    return label


@router.get("/classifications", response_model=ClassificationLabelListResponse)
def list_classification_labels(
    db: Session = Depends(get_classification_db),
    _: User = Depends(get_current_user),
) -> ClassificationLabelListResponse:
    ensure_default_classification_labels(db)
    labels = list(db.scalars(select(ClassificationLabel).order_by(ClassificationLabel.name)).all())
    return ClassificationLabelListResponse(
        data=[ClassificationLabelRead.model_validate(label) for label in labels],
        meta={"count": len(labels)},
    )


@router.post("/classifications", response_model=ClassificationLabelResponse)
def create_classification_label(
    payload: ClassificationLabelCreate,
    db: Session = Depends(get_classification_db),
    audit_db: Session = Depends(get_audit_db),
    user: User = Depends(require_roles(["admin", "editor"])),
) -> ClassificationLabelResponse:
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Classification name is required")
    existing = db.scalar(select(ClassificationLabel).where(ClassificationLabel.name == name))
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Classification already exists")
    label = ClassificationLabel(
        name=name,
        color_key=payload.color_key.strip() or "custom",
        description=payload.description,
        masks_samples=payload.masks_samples,
    )
    db.add(label)
    db.flush()
    write_audit_log(audit_db, user, "classification_created", "classification", label.id, metadata={"name": label.name})
    audit_db.commit()
    db.commit()
    db.refresh(label)
    return ClassificationLabelResponse(data=ClassificationLabelRead.model_validate(label), meta={})


@router.patch("/classifications/{label_id}", response_model=ClassificationLabelResponse)
def update_classification_label(
    label_id: str,
    payload: ClassificationLabelUpdate,
    db: Session = Depends(get_classification_db),
    audit_db: Session = Depends(get_audit_db),
    user: User = Depends(require_roles(["admin", "editor"])),
) -> ClassificationLabelResponse:
    label = db.get(ClassificationLabel, label_id)
    if label is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classification not found")
    if payload.name is not None:
        name = payload.name.strip()
        if not name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Classification name is required")
        duplicate = db.scalar(select(ClassificationLabel).where(ClassificationLabel.name == name, ClassificationLabel.id != label_id))
        if duplicate is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Classification already exists")
        label.name = name
    if payload.color_key is not None:
        label.color_key = payload.color_key.strip() or "custom"
    if payload.description is not None:
        label.description = payload.description
    if payload.masks_samples is not None:
        label.masks_samples = payload.masks_samples
    write_audit_log(audit_db, user, "classification_updated", "classification", label.id, metadata={"name": label.name})
    audit_db.commit()
    db.commit()
    db.refresh(label)
    return ClassificationLabelResponse(data=ClassificationLabelRead.model_validate(label), meta={})


@router.delete("/classifications/{label_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_classification_label(
    label_id: str,
    classification_db: Session = Depends(get_classification_db),
    policy_db: Session = Depends(get_policy_db),
    audit_db: Session = Depends(get_audit_db),
    user: User = Depends(require_roles(["admin"])),
) -> None:
    label = classification_db.get(ClassificationLabel, label_id)
    if label is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classification not found")
    policies = list(policy_db.scalars(select(Policy)).all())
    if any(_policy_classification(policy) == label.name for policy in policies):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Classification is used by a policy")
    assignment = classification_db.scalar(select(ClassificationAssignment).where(ClassificationAssignment.label == label.name))
    if assignment is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Classification already has assignments")
    write_audit_log(audit_db, user, "classification_deleted", "classification", label.id, metadata={"name": label.name})
    audit_db.commit()
    classification_db.delete(label)
    classification_db.commit()


@router.get("/policies", response_model=PolicyListResponse)
def list_policies(
    db: Session = Depends(get_policy_db),
    _: User = Depends(get_current_user),
) -> PolicyListResponse:
    policies = list(db.scalars(select(Policy).order_by(Policy.created_at.desc())).all())
    return PolicyListResponse(data=[PolicyRead.model_validate(policy) for policy in policies], meta={"count": len(policies)})


@router.post("/policies", response_model=PolicyResponse)
def create_policy(
    payload: PolicyCreate,
    db: Session = Depends(get_policy_db),
    classification_db: Session = Depends(get_classification_db),
    catalogue_db: Session = Depends(get_catalogue_db),
    audit_db: Session = Depends(get_audit_db),
    user: User = Depends(require_roles(["admin", "editor"])),
) -> PolicyResponse:
    classification = payload.action.get("classification")
    if payload.policy_type == "classification" and classification:
        _require_label_exists(classification_db, str(classification))
    policy = Policy(
        name=payload.name,
        policy_type=payload.policy_type,
        status=payload.status,
        rules=payload.rules,
        action=payload.action,
        created_by_id=user.id,
    )
    db.add(policy)
    db.flush()
    write_audit_log(audit_db, user, "policy_created", "policy", policy.id, metadata={"name": policy.name})
    applied_count = recalculate_policy_classifications(db, classification_db, catalogue_db)
    catalogue_db.commit()
    classification_db.commit()
    audit_db.commit()
    db.commit()
    db.refresh(policy)
    return PolicyResponse(data=PolicyRead.model_validate(policy), meta={"recalculated_policy_actions": applied_count})


@router.patch("/policies/{policy_id}", response_model=PolicyResponse)
def update_policy(
    policy_id: str,
    payload: PolicyUpdate,
    db: Session = Depends(get_policy_db),
    classification_db: Session = Depends(get_classification_db),
    catalogue_db: Session = Depends(get_catalogue_db),
    audit_db: Session = Depends(get_audit_db),
    user: User = Depends(require_roles(["admin", "editor"])),
) -> PolicyResponse:
    policy = db.get(Policy, policy_id)
    if policy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
    if payload.name is not None:
        policy.name = payload.name
    if payload.status is not None:
        policy.status = payload.status
    if payload.rules is not None:
        policy.rules = payload.rules
    if payload.action is not None:
        classification = payload.action.get("classification")
        if policy.policy_type == "classification" and classification:
            _require_label_exists(classification_db, str(classification))
        policy.action = payload.action
    write_audit_log(audit_db, user, "policy_updated", "policy", policy.id, metadata={"status": policy.status})
    applied_count = recalculate_policy_classifications(db, classification_db, catalogue_db)
    catalogue_db.commit()
    classification_db.commit()
    audit_db.commit()
    db.commit()
    db.refresh(policy)
    return PolicyResponse(data=PolicyRead.model_validate(policy), meta={"recalculated_policy_actions": applied_count})


@router.delete("/policies/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_policy(
    policy_id: str,
    db: Session = Depends(get_policy_db),
    classification_db: Session = Depends(get_classification_db),
    catalogue_db: Session = Depends(get_catalogue_db),
    audit_db: Session = Depends(get_audit_db),
    user: User = Depends(require_roles(["admin"])),
) -> None:
    policy = db.get(Policy, policy_id)
    if policy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
    write_audit_log(audit_db, user, "policy_deleted", "policy", policy.id, metadata={"name": policy.name})
    db.delete(policy)
    db.flush()
    recalculate_policy_classifications(db, classification_db, catalogue_db)
    catalogue_db.commit()
    classification_db.commit()
    audit_db.commit()
    db.commit()


@router.get("/governance/coverage", response_model=CoverageResponse)
def classification_coverage(
    db: Session = Depends(get_catalogue_db),
    _: User = Depends(get_current_user),
) -> CoverageResponse:
    assets = list(db.scalars(select(Asset).where(Asset.deleted_at.is_(None))).all())
    columns = list(db.scalars(select(Column)).all())
    pii_columns = sum(1 for column in columns if "PII" in column.classifications)
    gdpr_assets = sum(1 for asset in assets if "GDPR" in asset.classifications)
    unclassified_assets = sum(1 for asset in assets if not asset.classifications)
    fully_governed_assets = sum(1 for asset in assets if asset.classifications)
    return CoverageResponse(
        data={
            "pii_columns": pii_columns,
            "gdpr_assets": gdpr_assets,
            "unclassified_assets": unclassified_assets,
            "fully_governed_assets": fully_governed_assets,
            "total_assets": len(assets),
            "total_columns": len(columns),
        },
        meta={},
    )


@router.get("/audit-log", response_model=AuditLogListResponse)
def audit_log(
    limit: int = 100,
    event_type: str | None = None,
    db: Session = Depends(get_audit_db),
    admin_db: Session = Depends(get_admin_db),
    _: User = Depends(require_roles(["admin"])),
) -> AuditLogListResponse:
    limit = min(max(limit, 1), 100)
    statement = select(AuditLog).order_by(AuditLog.created_at.desc())
    if event_type:
        statement = statement.where(AuditLog.event_type == event_type)
    statement = statement.limit(limit)
    entries = list(db.scalars(statement).all())
    user_ids = {entry.user_id for entry in entries if entry.user_id}
    users = {
        user.id: user
        for user in admin_db.scalars(select(User).where(User.id.in_(user_ids))).all()
    } if user_ids else {}
    data = []
    for entry in entries:
        item = AuditLogRead.model_validate(entry)
        user = users.get(entry.user_id or "")
        item.user_email = user.email if user else None
        item.user_name = user.full_name if user else None
        data.append(item)
    return AuditLogListResponse(data=data, meta={"count": len(entries)})
