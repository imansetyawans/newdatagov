from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_admin_db, get_audit_db
from app.middleware.auth import get_current_user, require_roles
from app.models import Connector, User
from app.schemas.connector import (
    ConnectorCreate,
    ConnectorListResponse,
    ConnectorRead,
    ConnectorResponse,
    ConnectorSchemaListResponse,
    ConnectorSchemaRead,
    ConnectorScopeUpdate,
    ConnectorTestResponse,
)
from app.services.connector_service import build_connector, validate_sqlite_connector_config
from app.services.audit_service import write_audit_log


router = APIRouter(prefix="/api/v1/connectors", tags=["connectors"])


@router.get("", response_model=ConnectorListResponse)
def list_connectors(
    db: Session = Depends(get_admin_db),
    _: User = Depends(get_current_user),
) -> ConnectorListResponse:
    connectors = list(db.scalars(select(Connector).order_by(Connector.name)).all())
    return ConnectorListResponse(
        data=[ConnectorRead.model_validate(connector) for connector in connectors],
        meta={"count": len(connectors)},
    )


@router.post("", response_model=ConnectorResponse)
def create_connector(
    payload: ConnectorCreate,
    db: Session = Depends(get_admin_db),
    audit_db: Session = Depends(get_audit_db),
    user: User = Depends(require_roles(["admin"])),
) -> ConnectorResponse:
    if payload.connector_type == "sqlite":
        try:
            validate_sqlite_connector_config(payload.config)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    connector = Connector(
        name=payload.name,
        connector_type=payload.connector_type,
        config_encrypted=payload.config,
        status="inactive",
    )
    db.add(connector)
    db.commit()
    db.refresh(connector)
    write_audit_log(
        audit_db,
        user,
        action="connector_created",
        resource_type="connector",
        resource_id=connector.id,
        event_type="settings",
        metadata={"name": connector.name, "connector_type": connector.connector_type},
    )
    audit_db.commit()
    return ConnectorResponse(data=ConnectorRead.model_validate(connector), meta={})


@router.post("/{connector_id}/test", response_model=ConnectorTestResponse)
def test_connector(
    connector_id: str,
    db: Session = Depends(get_admin_db),
    audit_db: Session = Depends(get_audit_db),
    user: User = Depends(require_roles(["admin"])),
) -> ConnectorTestResponse:
    connector = db.get(Connector, connector_id)
    if connector is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connector not found")
    try:
        result = build_connector(connector).test()
        connector.status = "active"
    except Exception as exc:  # noqa: BLE001 - returned as connector test feedback
        result = {"success": False, "error": str(exc)}
        connector.status = "error"
    db.commit()
    write_audit_log(
        audit_db,
        user,
        action="connector_tested",
        resource_type="connector",
        resource_id=connector.id,
        event_type="settings",
        metadata={"name": connector.name, "success": bool(result.get("success"))},
    )
    audit_db.commit()
    return ConnectorTestResponse(data=result, meta={})


@router.get("/{connector_id}/schemas", response_model=ConnectorSchemaListResponse)
def discover_connector_schemas(
    connector_id: str,
    db: Session = Depends(get_admin_db),
    _: User = Depends(get_current_user),
) -> ConnectorSchemaListResponse:
    connector = db.get(Connector, connector_id)
    if connector is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connector not found")
    try:
        schemas = build_connector(connector).discover_schemas()
    except Exception as exc:  # noqa: BLE001 - returned as connector discovery feedback
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return ConnectorSchemaListResponse(
        data=[ConnectorSchemaRead(name=schema.name, asset_names=schema.asset_names) for schema in schemas],
        meta={"count": len(schemas), "connector_type": connector.connector_type},
    )


@router.patch("/{connector_id}/scope", response_model=ConnectorResponse)
def update_connector_scope(
    connector_id: str,
    payload: ConnectorScopeUpdate,
    db: Session = Depends(get_admin_db),
    audit_db: Session = Depends(get_audit_db),
    user: User = Depends(require_roles(["admin", "editor"])),
) -> ConnectorResponse:
    connector = db.get(Connector, connector_id)
    if connector is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connector not found")
    config = dict(connector.config_encrypted or {})
    config["catalogue_scope"] = payload.catalogue_scope
    connector.config_encrypted = config
    db.commit()
    db.refresh(connector)
    write_audit_log(
        audit_db,
        user,
        action="connector_scope_updated",
        resource_type="connector",
        resource_id=connector.id,
        event_type="settings",
        metadata={"name": connector.name, "catalogue_scope": payload.catalogue_scope},
    )
    audit_db.commit()
    return ConnectorResponse(data=ConnectorRead.model_validate(connector), meta={})


@router.delete("/{connector_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_connector(
    connector_id: str,
    db: Session = Depends(get_admin_db),
    audit_db: Session = Depends(get_audit_db),
    user: User = Depends(require_roles(["admin"])),
) -> None:
    connector = db.get(Connector, connector_id)
    if connector is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connector not found")
    connector_name = connector.name
    db.delete(connector)
    db.commit()
    write_audit_log(
        audit_db,
        user,
        action="connector_deleted",
        resource_type="connector",
        resource_id=connector_id,
        event_type="settings",
        metadata={"name": connector_name},
    )
    audit_db.commit()
