from app.database import sessionmakers
from app.models import Scan
from app.services.scan_service import run_scan
from app.workers.celery_app import celery_app


@celery_app.task(name="scan.run")
def run_scan_task(scan_id: str) -> dict:
    with (
        sessionmakers["admin"]() as admin_db,
        sessionmakers["catalogue"]() as catalogue_db,
        sessionmakers["quality"]() as quality_db,
        sessionmakers["policy"]() as policy_db,
        sessionmakers["classification"]() as classification_db,
        sessionmakers["audit"]() as audit_db,
    ):
        scan = admin_db.get(Scan, scan_id)
        if scan is None:
            return {"status": "failed", "error": "Scan not found"}
        scan = run_scan(
            admin_db=admin_db,
            catalogue_db=catalogue_db,
            quality_db=quality_db,
            policy_db=policy_db,
            classification_db=classification_db,
            audit_db=audit_db,
            scan=scan,
        )
        return {
            "id": scan.id,
            "status": scan.status,
            "assets_scanned": scan.assets_scanned,
            "columns_scanned": scan.columns_scanned,
        }
