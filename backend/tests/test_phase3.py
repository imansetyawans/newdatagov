import sqlite3

from fastapi.testclient import TestClient


def _create_lineage_source(path) -> None:
    with sqlite3.connect(path) as connection:
        connection.execute("create table customers (id integer primary key, email text, status text)")
        connection.execute("create table orders (id integer primary key, customer_id integer, order_total real)")
        connection.execute("insert into customers (email, status) values ('a@example.com', 'active')")
        connection.execute("insert into orders (customer_id, order_total) values (1, 100.0)")
        connection.commit()


def test_schedules_glossary_and_lineage_flow(client: TestClient, admin_token: str, tmp_path) -> None:
    db_path = tmp_path / "phase3_source.db"
    _create_lineage_source(db_path)
    headers = {"Authorization": f"Bearer {admin_token}"}

    connector = client.post(
        "/api/v1/connectors",
        headers=headers,
        json={"name": "Phase 3 SQLite", "connector_type": "sqlite", "config": {"database_path": str(db_path)}},
    )
    assert connector.status_code == 200
    connector_id = connector.json()["data"]["id"]

    schedule = client.post(
        "/api/v1/scans/schedules",
        headers=headers,
        json={
            "connector_ids": [connector_id],
            "scan_type": "full",
            "schedule_cron": "0 8 * * *",
            "notify_on_completion": True,
        },
    )
    assert schedule.status_code == 200
    assert schedule.json()["data"]["status"] == "scheduled"
    assert schedule.json()["data"]["schedule_cron"] == "0 8 * * *"

    schedules = client.get("/api/v1/scans/schedules", headers=headers)
    assert schedules.status_code == 200
    assert schedules.json()["meta"]["count"] == 1

    term = client.post(
        "/api/v1/glossary",
        headers=headers,
        json={
            "term": "Customer",
            "definition": "A person or organization with an account.",
            "synonyms": ["client"],
            "status": "approved",
        },
    )
    assert term.status_code == 200
    term_id = term.json()["data"]["id"]

    scan = client.post(
        "/api/v1/scans",
        headers=headers,
        json={"connector_ids": [connector_id], "scan_type": "full"},
    )
    assert scan.status_code == 200
    assert scan.json()["data"]["status"] == "completed"

    suggestions = client.get("/api/v1/glossary/suggestions", headers=headers)
    assert suggestions.status_code == 200
    assert suggestions.json()["data"]

    assets = client.get("/api/v1/assets", headers=headers).json()["data"]
    customer_asset = next(asset for asset in assets if asset["name"] == "customers")
    linked = client.patch(
        f"/api/v1/glossary/{term_id}",
        headers=headers,
        json={"linked_asset_ids": [customer_asset["id"]]},
    )
    assert linked.status_code == 200
    assert linked.json()["data"]["linked_asset_ids"] == [customer_asset["id"]]

    lineage = client.get("/api/v1/lineage", headers=headers)
    assert lineage.status_code == 200
    graph = lineage.json()["data"]
    assert {node["name"] for node in graph["nodes"]} == {"customers", "orders"}
    assert len(graph["edges"]) == 1

    extracted = client.post("/api/v1/lineage/extract", headers=headers)
    assert extracted.status_code == 200
    assert extracted.json()["meta"]["count"] == 1


def test_connector_rejects_metadata_database_filename(client: TestClient, admin_token: str) -> None:
    response = client.post(
        "/api/v1/connectors",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "Protected catalogue database",
            "connector_type": "sqlite",
            "config": {"database_path": "backend/datagov_catalogue.db"},
        },
    )

    assert response.status_code == 400
    assert "metadata databases" in response.json()["detail"]
