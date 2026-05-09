import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database import (
    get_admin_db,
    get_audit_db,
    get_catalogue_db,
    get_classification_db,
    get_policy_db,
    get_quality_db,
)
from app.middleware.auth import get_current_user, require_roles
from app.models import Scan, User
from app.schemas.scan import ScanCreate, ScanListResponse, ScanRead, ScanResponse, ScheduledScanCreate, ScheduledScanUpdate
from app.services.audit_service import write_audit_log
from app.services.notification_service import dispatch_notifications
from app.services.scan_service import run_scan


router = APIRouter(prefix="/api/v1/scans", tags=["scans"])


def _notification_config(scan: Scan) -> dict:
    for item in scan.errors:
        if isinstance(item, dict) and "schedule" in item:
            return item["schedule"]
    return {"notify_on_completion": False}


@router.get("/schedules", response_model=ScanListResponse)
def list_scheduled_scans(
    db: Session = Depends(get_admin_db),
    _: User = Depends(get_current_user),
) -> ScanListResponse:
    scans = list(
        db.scalars(
            select(Scan).where(Scan.schedule_cron.is_not(None)).order_by(Scan.created_at.desc())
        ).all()
    )
    return ScanListResponse(
        data=[ScanRead.model_validate(scan) for scan in scans],
        meta={"count": len(scans), "notifications": {scan.id: _notification_config(scan) for scan in scans}},
    )


@router.post("/schedules", response_model=ScanResponse)
def create_scheduled_scan(
    payload: ScheduledScanCreate,
    db: Session = Depends(get_admin_db),
    audit_db: Session = Depends(get_audit_db),
    user: User = Depends(require_roles(["admin", "editor"])),
) -> ScanResponse:
    scan = Scan(
        connector_ids=payload.connector_ids,
        scan_type=payload.scan_type,
        status="scheduled",
        schedule_cron=payload.schedule_cron,
        errors=[{"schedule": {"notify_on_completion": payload.notify_on_completion}}],
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)
    write_audit_log(
        audit_db,
        user,
        action="scan_schedule_created",
        resource_type="scan",
        resource_id=scan.id,
        event_type="scan",
        metadata={"schedule_cron": scan.schedule_cron, "scan_type": scan.scan_type},
    )
    audit_db.commit()
    return ScanResponse(data=scan, meta={"notification": _notification_config(scan)})


@router.patch("/schedules/{scan_id}", response_model=ScanResponse)
def update_scheduled_scan(
    scan_id: str,
    payload: ScheduledScanUpdate,
    db: Session = Depends(get_admin_db),
    audit_db: Session = Depends(get_audit_db),
    user: User = Depends(require_roles(["admin", "editor"])),
) -> ScanResponse:
    scan = db.get(Scan, scan_id)
    if scan is None or scan.schedule_cron is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scheduled scan not found")
    if payload.schedule_cron is not None:
        scan.schedule_cron = payload.schedule_cron
    if payload.status is not None:
        scan.status = payload.status
    if payload.notify_on_completion is not None:
        scan.errors = [{"schedule": {"notify_on_completion": payload.notify_on_completion}}]
    db.commit()
    db.refresh(scan)
    write_audit_log(
        audit_db,
        user,
        action="scan_schedule_updated",
        resource_type="scan",
        resource_id=scan.id,
        event_type="scan",
        metadata={"status": scan.status, "schedule_cron": scan.schedule_cron},
    )
    audit_db.commit()
    return ScanResponse(data=scan, meta={"notification": _notification_config(scan)})


@router.post("", response_model=ScanResponse)
def create_scan(
    payload: ScanCreate,
    admin_db: Session = Depends(get_admin_db),
    catalogue_db: Session = Depends(get_catalogue_db),
    quality_db: Session = Depends(get_quality_db),
    policy_db: Session = Depends(get_policy_db),
    classification_db: Session = Depends(get_classification_db),
    audit_db: Session = Depends(get_audit_db),
    user: User = Depends(require_roles(["admin", "editor"])),
) -> ScanResponse:
    scan = Scan(connector_ids=payload.connector_ids, scan_type=payload.scan_type)
    admin_db.add(scan)
    admin_db.commit()
    admin_db.refresh(scan)
    scan = run_scan(
        admin_db=admin_db,
        catalogue_db=catalogue_db,
        quality_db=quality_db,
        policy_db=policy_db,
        classification_db=classification_db,
        audit_db=audit_db,
        scan=scan,
        scan_scopes=payload.connector_scopes,
    )
    write_audit_log(
        audit_db,
        user,
        action="scan_completed",
        resource_type="scan",
        resource_id=scan.id,
        event_type="scan",
        metadata={
            "status": scan.status,
            "assets_scanned": scan.assets_scanned,
            "columns_scanned": scan.columns_scanned,
            "policies_applied": scan.policies_applied,
        },
    )
    notification_count = dispatch_notifications(
        admin_db,
        audit_db,
        "scan_completed",
        {
            "scan_id": scan.id,
            "status": scan.status,
            "assets_scanned": scan.assets_scanned,
            "columns_scanned": scan.columns_scanned,
        },
        user,
    )
    audit_db.commit()
    return ScanResponse(data=scan, meta={"notifications_sent": notification_count})


@router.get("/{scan_id}", response_model=ScanResponse)
def scan_detail(
    scan_id: str,
    db: Session = Depends(get_admin_db),
    _: User = Depends(get_current_user),
) -> ScanResponse:
    scan = db.get(Scan, scan_id)
    if scan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")
    return ScanResponse(data=scan, meta={})


@router.get("/{scan_id}/stream")
async def scan_stream(
    scan_id: str,
    db: Session = Depends(get_admin_db),
    _: User = Depends(get_current_user),
) -> StreamingResponse:
    scan = db.get(Scan, scan_id)
    if scan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")

    async def events():
        stages = [
            ("connect", 20),
            ("discover", 45),
            ("catalogue", 70),
            ("complete", 100),
        ]
        for stage, progress in stages:
            payload = {"stage": stage, "progress": progress, "status": scan.status}
            yield f"data: {json.dumps(payload)}\n\n"
            await asyncio.sleep(0.05)

    return StreamingResponse(events(), media_type="text/event-stream")
