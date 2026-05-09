from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Asset, ClassificationAssignment, Policy


def _matches_rule(asset: Asset, column_name: str, rule: dict) -> bool:
    field = rule.get("field", "column_name")
    operator = rule.get("operator", "contains")
    value = str(rule.get("value", "")).lower()
    target = column_name.lower() if field == "column_name" else asset.name.lower()
    if operator == "contains":
        return value in target
    if operator == "equals":
        return value == target
    if operator == "starts_with":
        return target.startswith(value)
    if operator == "ends_with":
        return target.endswith(value)
    return False


def _record_assignment(
    classification_db: Session,
    label: str,
    resource_type: str,
    resource_id: str,
    policy_id: str,
) -> None:
    existing = classification_db.scalar(
        select(ClassificationAssignment).where(
            ClassificationAssignment.label == label,
            ClassificationAssignment.resource_type == resource_type,
            ClassificationAssignment.resource_id == resource_id,
            ClassificationAssignment.policy_id == policy_id,
        )
    )
    if existing is None:
        classification_db.add(
            ClassificationAssignment(
                label=label,
                resource_type=resource_type,
                resource_id=resource_id,
                source="policy",
                policy_id=policy_id,
            )
        )


def _reset_policy_classifications(
    classification_db: Session,
    asset: Asset,
) -> None:
    resource_ids = [asset.id, *[column.id for column in asset.columns]]
    assignments = list(
        classification_db.scalars(
            select(ClassificationAssignment).where(
                ClassificationAssignment.source == "policy",
                ClassificationAssignment.resource_id.in_(resource_ids),
            )
        ).all()
    )
    for assignment in assignments:
        classification_db.delete(assignment)

    asset.classifications = []
    for column in asset.columns:
        column.classifications = []


def evaluate_policies(
    policy_db: Session,
    classification_db: Session,
    catalogue_db: Session,
    asset: Asset,
) -> int:
    _reset_policy_classifications(classification_db, asset)
    policies = list(policy_db.scalars(select(Policy).where(Policy.status == "active")).all())
    applied_count = 0
    for policy in policies:
        classification = policy.action.get("classification")
        if not classification:
            continue
        for column in asset.columns:
            if all(_matches_rule(asset, column.name, rule) for rule in policy.rules):
                if classification not in column.classifications:
                    column.classifications = [*column.classifications, classification]
                    applied_count += 1
                _record_assignment(classification_db, classification, "column", column.id, policy.id)
                if classification not in asset.classifications:
                    asset.classifications = [*asset.classifications, classification]
                _record_assignment(classification_db, classification, "asset", asset.id, policy.id)
    catalogue_db.flush()
    classification_db.flush()
    return applied_count


def recalculate_policy_classifications(
    policy_db: Session,
    classification_db: Session,
    catalogue_db: Session,
) -> int:
    assets = list(
        catalogue_db.scalars(
            select(Asset)
            .options(selectinload(Asset.columns))
            .where(Asset.deleted_at.is_(None))
        ).all()
    )
    return sum(evaluate_policies(policy_db, classification_db, catalogue_db, asset) for asset in assets)
