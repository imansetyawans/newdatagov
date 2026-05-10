from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import (
    Base,
    MODULE_DATABASES,
    get_admin_db,
    get_audit_db,
    get_catalogue_db,
    get_classification_db,
    get_db,
    get_glossary_db,
    get_policy_db,
    get_quality_db,
)
from app.main import app
from app.models import Connector, User
from app.services.access_control import ensure_default_roles
from app.services.classification_service import ensure_default_classification_labels
from app.utils.security import hash_password


DEPENDENCIES = {
    "admin": get_admin_db,
    "catalogue": get_catalogue_db,
    "classification": get_classification_db,
    "quality": get_quality_db,
    "policy": get_policy_db,
    "glossary": get_glossary_db,
    "audit": get_audit_db,
}


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    sessionmakers = {}
    for key, module in MODULE_DATABASES.items():
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        tables = [Base.metadata.tables[table_name] for table_name in module.tables]
        Base.metadata.create_all(bind=engine, tables=tables)
        sessionmakers[key] = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    with sessionmakers["admin"]() as db:
        ensure_default_roles(db)
        db.add(
            User(
                email="admin@test.local",
                hashed_password=hash_password("admin123"),
                full_name="Test Admin",
                role="admin",
            )
        )
        db.add(
            User(
                email="viewer@test.local",
                hashed_password=hash_password("viewer123"),
                full_name="Test Viewer",
                role="viewer",
            )
        )
        db.add(
            Connector(
                name="Test SQLite",
                connector_type="sqlite",
                config_encrypted={"database_path": ":memory:"},
                status="inactive",
            )
        )
        db.commit()

    with sessionmakers["classification"]() as db:
        ensure_default_classification_labels(db)

    def dependency_for(key: str):
        def override() -> Generator[Session, None, None]:
            db = sessionmakers[key]()
            try:
                yield db
            finally:
                db.close()

        return override

    for key, dependency in DEPENDENCIES.items():
        app.dependency_overrides[dependency] = dependency_for(key)
    app.dependency_overrides[get_db] = dependency_for("admin")

    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def admin_token(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.local", "password": "admin123"},
    )
    return response.json()["data"]["access_token"]


@pytest.fixture
def viewer_token(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "viewer@test.local", "password": "viewer123"},
    )
    return response.json()["data"]["access_token"]
