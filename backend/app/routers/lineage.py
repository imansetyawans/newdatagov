from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_audit_db, get_catalogue_db
from app.middleware.auth import get_current_user, require_roles
from app.models import Asset, LineageEdge, User
from app.schemas.lineage import (
    LineageEdgeCreate,
    LineageEdgeListResponse,
    LineageEdgeRead,
    LineageEdgeResponse,
    LineageGraphResponse,
)
from app.services.lineage_service import build_lineage_graph, extract_table_lineage
from app.services.audit_service import write_audit_log


router = APIRouter(prefix="/api/v1/lineage", tags=["lineage"])


@router.get("", response_model=LineageGraphResponse)
def lineage_graph(
    db: Session = Depends(get_catalogue_db),
    _: User = Depends(get_current_user),
) -> LineageGraphResponse:
    graph = build_lineage_graph(db)
    return LineageGraphResponse(data=graph, meta={"node_count": len(graph["nodes"]), "edge_count": len(graph["edges"])})


@router.get("/edges", response_model=LineageEdgeListResponse)
def lineage_edges(
    db: Session = Depends(get_catalogue_db),
    _: User = Depends(get_current_user),
) -> LineageEdgeListResponse:
    edges = list(db.scalars(select(LineageEdge).order_by(LineageEdge.created_at.desc())).all())
    return LineageEdgeListResponse(data=[LineageEdgeRead.model_validate(edge) for edge in edges], meta={"count": len(edges)})


@router.post("/edges", response_model=LineageEdgeResponse)
def create_lineage_edge(
    payload: LineageEdgeCreate,
    db: Session = Depends(get_catalogue_db),
    audit_db: Session = Depends(get_audit_db),
    user: User = Depends(require_roles(["admin", "editor"])),
) -> LineageEdgeResponse:
    upstream = db.get(Asset, payload.upstream_asset_id)
    downstream = db.get(Asset, payload.downstream_asset_id)
    if upstream is None or downstream is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lineage asset not found")
    edge = LineageEdge(**payload.model_dump())
    db.add(edge)
    db.commit()
    db.refresh(edge)
    write_audit_log(
        audit_db,
        user,
        action="lineage_edge_created",
        resource_type="lineage_edge",
        resource_id=edge.id,
        event_type="lineage",
        metadata={"upstream_asset_id": edge.upstream_asset_id, "downstream_asset_id": edge.downstream_asset_id},
    )
    audit_db.commit()
    return LineageEdgeResponse(data=LineageEdgeRead.model_validate(edge), meta={})


@router.post("/extract", response_model=LineageEdgeListResponse)
def extract_lineage(
    db: Session = Depends(get_catalogue_db),
    audit_db: Session = Depends(get_audit_db),
    user: User = Depends(require_roles(["admin", "editor"])),
) -> LineageEdgeListResponse:
    extract_table_lineage(db)
    db.commit()
    edges = list(db.scalars(select(LineageEdge).order_by(LineageEdge.created_at.desc())).all())
    write_audit_log(
        audit_db,
        user,
        action="lineage_extracted",
        resource_type="lineage",
        resource_id=None,
        event_type="lineage",
        metadata={"edge_count": len(edges)},
    )
    audit_db.commit()
    return LineageEdgeListResponse(data=[LineageEdgeRead.model_validate(edge) for edge in edges], meta={"count": len(edges)})
