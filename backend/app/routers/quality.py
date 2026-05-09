from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_audit_db, get_catalogue_db, get_quality_db
from app.middleware.auth import get_current_user, require_roles
from app.models import Asset, DQIssue, User
from app.schemas.quality import (
    DQIssueListResponse,
    DQIssueRead,
    DQIssueResponse,
    DQIssueUpdate,
    DQScoreListResponse,
    DQScoreRead,
)
from app.services.audit_service import write_audit_log


router = APIRouter(prefix="/api/v1/dq", tags=["quality"])


@router.get("/scores", response_model=DQScoreListResponse)
def dq_scores(
    db: Session = Depends(get_catalogue_db),
    _: User = Depends(get_current_user),
) -> DQScoreListResponse:
    assets = list(db.scalars(select(Asset).where(Asset.deleted_at.is_(None)).order_by(Asset.name)).all())
    return DQScoreListResponse(
        data=[
            DQScoreRead(
                asset_id=asset.id,
                asset_name=asset.name,
                source_path=asset.source_path,
                dq_score=asset.dq_score,
                last_scanned_at=asset.last_scanned_at,
            )
            for asset in assets
        ],
        meta={"count": len(assets)},
    )


@router.get("/scores/{asset_id}", response_model=DQScoreRead)
def dq_score_detail(
    asset_id: str,
    db: Session = Depends(get_catalogue_db),
    _: User = Depends(get_current_user),
) -> DQScoreRead:
    asset = db.get(Asset, asset_id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return DQScoreRead(
        asset_id=asset.id,
        asset_name=asset.name,
        source_path=asset.source_path,
        dq_score=asset.dq_score,
        last_scanned_at=asset.last_scanned_at,
    )


@router.get("/issues", response_model=DQIssueListResponse)
def dq_issues(
    status_filter: str | None = None,
    severity: str | None = None,
    asset_id: str | None = None,
    db: Session = Depends(get_quality_db),
    _: User = Depends(get_current_user),
) -> DQIssueListResponse:
    statement = select(DQIssue).order_by(DQIssue.created_at.desc())
    if status_filter:
        statement = statement.where(DQIssue.status == status_filter)
    if severity:
        statement = statement.where(DQIssue.severity == severity)
    if asset_id:
        statement = statement.where(DQIssue.asset_id == asset_id)
    issues = list(db.scalars(statement).all())
    return DQIssueListResponse(data=[DQIssueRead.model_validate(issue) for issue in issues], meta={"count": len(issues)})


@router.patch("/issues/{issue_id}", response_model=DQIssueResponse)
def update_dq_issue(
    issue_id: str,
    payload: DQIssueUpdate,
    db: Session = Depends(get_quality_db),
    audit_db: Session = Depends(get_audit_db),
    user: User = Depends(require_roles(["admin", "editor"])),
) -> DQIssueResponse:
    issue = db.get(DQIssue, issue_id)
    if issue is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Issue not found")
    issue.status = payload.status
    issue.resolution_note = payload.resolution_note
    if payload.status == "resolved":
        issue.resolved_at = datetime.utcnow()
        issue.resolved_by_id = user.id
    write_audit_log(
        audit_db,
        user,
        action="dq_issue_updated",
        resource_type="dq_issue",
        resource_id=issue.id,
        event_type="quality",
        metadata={"status": payload.status},
    )
    audit_db.commit()
    db.commit()
    db.refresh(issue)
    return DQIssueResponse(data=DQIssueRead.model_validate(issue), meta={})
