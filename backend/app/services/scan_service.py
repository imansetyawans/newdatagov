from datetime import datetime

from sqlalchemy.orm import Session

from app.models import Connector, Scan
from app.services.catalogue_service import mark_missing_connector_assets_deleted, upsert_discovered_asset
from app.services.connector_service import build_connector
from app.services.dq_engine import calculate_asset_quality
from app.services.policy_engine import evaluate_policies
from app.services.lineage_service import extract_table_lineage


def run_scan(
    admin_db: Session,
    catalogue_db: Session,
    quality_db: Session,
    policy_db: Session,
    classification_db: Session,
    audit_db: Session,
    scan: Scan,
    scan_scopes: dict[str, dict] | None = None,
) -> Scan:
    scan.status = "running"
    scan.started_at = datetime.utcnow()
    admin_db.commit()
    admin_db.refresh(scan)

    assets_scanned = 0
    columns_scanned = 0
    errors: list[dict] = []

    for connector_id in scan.connector_ids:
        connector = admin_db.get(Connector, connector_id)
        if connector is None:
            errors.append({"connector_id": connector_id, "error": "Connector not found"})
            continue

        try:
            connector_scope = (scan_scopes or {}).get(connector.id) or connector.config_encrypted.get("catalogue_scope")
            discovered_assets = build_connector(connector).discover_assets(scope=connector_scope)
            connector.status = "active"
            connector.last_tested_at = datetime.utcnow()
            active_source_paths: set[str] = set()
            for discovered in discovered_assets:
                scanned_at = datetime.utcnow()
                active_source_paths.add(discovered.source_path)
                asset, column_count = upsert_discovered_asset(
                    db=catalogue_db,
                    connector_id=connector.id,
                    discovered=discovered,
                    scanned_at=scanned_at,
                )
                assets_scanned += 1
                columns_scanned += column_count
                database_path = connector.config_encrypted.get("database_path", "datagov.db")
                if discovered.asset_type == "table":
                    scan.dq_issues_raised += calculate_asset_quality(
                        catalogue_db,
                        quality_db,
                        database_path,
                        asset,
                        discovered.name,
                        connector.config_encrypted.get("attached_databases", []),
                    )
                scan.policies_applied += evaluate_policies(policy_db, classification_db, catalogue_db, asset)
            mark_missing_connector_assets_deleted(
                catalogue_db,
                connector.id,
                active_source_paths,
                datetime.utcnow(),
            )
        except Exception as exc:  # noqa: BLE001 - captured into scan record for UI visibility
            connector.status = "error"
            errors.append({"connector_id": connector.id, "error": str(exc)})

    catalogue_db.commit()
    quality_db.commit()
    policy_db.commit()
    classification_db.commit()
    audit_db.commit()
    extract_table_lineage(catalogue_db)
    catalogue_db.commit()
    scan.assets_scanned = assets_scanned
    scan.columns_scanned = columns_scanned
    scan.errors = errors
    scan.status = "failed" if errors and assets_scanned == 0 else "completed"
    scan.finished_at = datetime.utcnow()
    admin_db.commit()
    admin_db.refresh(scan)
    return scan
