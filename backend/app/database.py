from collections.abc import Generator
from dataclasses import dataclass

from sqlalchemy import create_engine, inspect
from sqlalchemy import text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


@dataclass(frozen=True)
class ModuleDatabase:
    key: str
    url: str
    tables: tuple[str, ...]


MODULE_DATABASES = {
    "admin": ModuleDatabase("admin", settings.admin_database_url, ("users", "connectors", "scans", "notification_settings")),
    "catalogue": ModuleDatabase(
        "catalogue",
        settings.catalogue_database_url,
        ("catalogue_projects", "project_categories", "assets", "columns", "lineage_edges"),
    ),
    "classification": ModuleDatabase(
        "classification",
        settings.classification_database_url,
        ("classification_labels", "classification_assignments"),
    ),
    "quality": ModuleDatabase("quality", settings.quality_database_url, ("dq_issues",)),
    "policy": ModuleDatabase("policy", settings.policy_database_url, ("policies",)),
    "glossary": ModuleDatabase("glossary", settings.glossary_database_url, ("glossary_terms",)),
    "audit": ModuleDatabase("audit", settings.audit_database_url, ("audit_log",)),
}


def _connect_args(url: str) -> dict:
    if url.startswith("sqlite"):
        return {"check_same_thread": False}
    if url.startswith("postgresql+psycopg"):
        return {"prepare_threshold": None}
    return {}


engines = {
    key: create_engine(module.url, connect_args=_connect_args(module.url), echo=settings.debug)
    for key, module in MODULE_DATABASES.items()
}

sessionmakers = {
    key: sessionmaker(autocommit=False, autoflush=False, bind=engine)
    for key, engine in engines.items()
}

# Backward-compatible aliases for older code and a few test fixtures.
engine = engines["admin"]
SessionLocal = sessionmakers["admin"]


def create_module_tables() -> None:
    for key, module in MODULE_DATABASES.items():
        tables = [Base.metadata.tables[table_name] for table_name in module.tables]
        Base.metadata.create_all(bind=engines[key], tables=tables)
    ensure_compatibility_columns()
    ensure_sqlite_performance_indexes()


def _sqlite_columns(key: str, table_name: str) -> set[str]:
    with engines[key].connect() as connection:
        rows = connection.execute(text(f"pragma table_info({table_name})")).mappings().all()
    return {str(row["name"]) for row in rows}


def ensure_compatibility_columns() -> None:
    compatibility_columns = {
        "catalogue": {
            "columns": {
                "standard_format": {"sqlite": "TEXT", "postgresql": "TEXT"},
                "sample_values": {
                    "sqlite": "TEXT NOT NULL DEFAULT '[]'",
                    "postgresql": "JSON NOT NULL DEFAULT '[]'::json",
                },
            },
            "assets": {
                "project_id": {"sqlite": "VARCHAR(36)", "postgresql": "VARCHAR(36)"},
                "category_id": {"sqlite": "VARCHAR(36)", "postgresql": "VARCHAR(36)"},
            },
        },
        "classification": {
            "classification_labels": {
                "masks_samples": {"sqlite": "BOOLEAN NOT NULL DEFAULT 0", "postgresql": "BOOLEAN NOT NULL DEFAULT FALSE"},
            },
        },
    }
    for key, tables in compatibility_columns.items():
        dialect = engines[key].dialect.name
        for table_name, columns in tables.items():
            if MODULE_DATABASES[key].url.startswith("sqlite"):
                existing_columns = _sqlite_columns(key, table_name)
            else:
                existing_columns = {column["name"] for column in inspect(engines[key]).get_columns(table_name)}
            with engines[key].begin() as connection:
                for column_name, ddl_by_dialect in columns.items():
                    if column_name not in existing_columns:
                        ddl = ddl_by_dialect.get(dialect)
                        if ddl is None:
                            continue
                        connection.execute(text(f"alter table {table_name} add column {column_name} {ddl}"))


def ensure_sqlite_performance_indexes() -> None:
    indexes = {
        "admin": [
            "create index if not exists ix_scans_status_created_at on scans (status, created_at)",
            "create index if not exists ix_notification_settings_channel_enabled on notification_settings (channel, enabled)",
        ],
        "catalogue": [
            "create index if not exists ix_assets_deleted_name on assets (deleted_at, name)",
            "create index if not exists ix_assets_connector_source on assets (connector_id, source_path)",
            "create index if not exists ix_assets_project_category on assets (project_id, category_id)",
            "create index if not exists ix_columns_asset_position on columns (asset_id, ordinal_position)",
            "create index if not exists ix_project_categories_project_status on project_categories (project_id, status)",
        ],
        "quality": [
            "create index if not exists ix_dq_issues_status_created_at on dq_issues (status, created_at)",
            "create index if not exists ix_dq_issues_asset_status on dq_issues (asset_id, status)",
        ],
        "audit": [
            "create index if not exists ix_audit_log_event_created_at on audit_log (event_type, created_at)",
            "create index if not exists ix_audit_log_created_at on audit_log (created_at)",
        ],
        "glossary": [
            "create index if not exists ix_glossary_terms_status_term on glossary_terms (status, term)",
        ],
    }
    for key, statements in indexes.items():
        if not MODULE_DATABASES[key].url.startswith("sqlite"):
            continue
        with engines[key].begin() as connection:
            for statement in statements:
                connection.execute(text(statement))


def get_module_db(key: str) -> Generator[Session, None, None]:
    db = sessionmakers[key]()
    try:
        yield db
    finally:
        db.close()


def get_db() -> Generator[Session, None, None]:
    yield from get_admin_db()


def get_admin_db() -> Generator[Session, None, None]:
    yield from get_module_db("admin")


def get_catalogue_db() -> Generator[Session, None, None]:
    yield from get_module_db("catalogue")


def get_classification_db() -> Generator[Session, None, None]:
    yield from get_module_db("classification")


def get_quality_db() -> Generator[Session, None, None]:
    yield from get_module_db("quality")


def get_policy_db() -> Generator[Session, None, None]:
    yield from get_module_db("policy")


def get_glossary_db() -> Generator[Session, None, None]:
    yield from get_module_db("glossary")


def get_audit_db() -> Generator[Session, None, None]:
    yield from get_module_db("audit")
