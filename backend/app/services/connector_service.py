from pathlib import Path
from urllib.parse import unquote, urlparse

from sqlalchemy.orm import Session

from app.connectors.base import BaseConnector
from app.connectors.sqlite_connector import SQLiteConnector
from app.config import settings
from app.database import MODULE_DATABASES
from app.models import Connector


def _path_from_sqlite_url(url: str) -> Path | None:
    if not url.startswith("sqlite"):
        return None
    parsed = urlparse(url)
    raw_path = unquote(parsed.path)
    if url.startswith("sqlite:///./"):
        return (Path.cwd() / url.removeprefix("sqlite:///./")).resolve()
    if url.startswith("sqlite:///"):
        return Path(raw_path).resolve()
    return None


def protected_metadata_paths() -> set[Path]:
    paths = set()
    for module in MODULE_DATABASES.values():
        path = _path_from_sqlite_url(module.url)
        if path is not None:
            paths.add(path)
    return paths


def validate_sqlite_source_path(database_path: str) -> None:
    source_path = Path(database_path).expanduser()
    if not source_path.is_absolute():
        source_path = Path.cwd() / source_path
    protected_paths = protected_metadata_paths()
    protected_names = {path.name for path in protected_paths}
    if source_path.resolve() in protected_paths or source_path.name in protected_names:
        raise ValueError("DataGov metadata databases cannot be used as scanned source connectors")


def validate_sqlite_connector_config(config: dict) -> None:
    validate_sqlite_source_path(str(config.get("database_path", "")))
    for attached in config.get("attached_databases", []) or []:
        validate_sqlite_source_path(str(attached.get("database_path", "")))


def build_connector(connector: Connector) -> BaseConnector:
    if connector.connector_type != "sqlite":
        raise ValueError(f"Unsupported connector type: {connector.connector_type}")

    database_path = connector.config_encrypted.get("database_path")
    if not database_path:
        database_path = str(Path.cwd() / settings.sample_source_path)
    validate_sqlite_source_path(str(database_path))
    return SQLiteConnector(
        database_path=database_path,
        attached_databases=connector.config_encrypted.get("attached_databases", []),
    )


def create_default_sqlite_connector(db: Session) -> Connector:
    connector = Connector(
        name="Local DataGov SQLite",
        connector_type="sqlite",
        config_encrypted={"database_path": str(Path.cwd() / settings.sample_source_path), "attached_databases": []},
        status="active",
    )
    db.add(connector)
    db.commit()
    db.refresh(connector)
    return connector
