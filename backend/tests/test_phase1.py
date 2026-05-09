import sqlite3

from fastapi.testclient import TestClient


def test_connector_catalogue_and_scan_flow(client: TestClient, admin_token: str, tmp_path) -> None:
    db_path = tmp_path / "source.db"
    with sqlite3.connect(db_path) as connection:
        connection.execute("create table customers (id integer primary key, email text not null, age integer)")
        connection.execute("insert into customers (email, age) values ('a@example.com', 32)")
        connection.execute("insert into customers (email, age) values ('b@example.com', 27)")
        connection.commit()

    headers = {"Authorization": f"Bearer {admin_token}"}
    created = client.post(
        "/api/v1/connectors",
        headers=headers,
        json={"name": "Customer SQLite", "connector_type": "sqlite", "config": {"database_path": str(db_path)}},
    )
    assert created.status_code == 200
    connector_id = created.json()["data"]["id"]

    tested = client.post(f"/api/v1/connectors/{connector_id}/test", headers=headers)
    assert tested.status_code == 200
    assert tested.json()["data"]["success"] is True

    scan = client.post(
        "/api/v1/scans",
        headers=headers,
        json={"connector_ids": [connector_id], "scan_type": "full"},
    )
    assert scan.status_code == 200
    assert scan.json()["data"]["status"] == "completed"
    assert scan.json()["data"]["assets_scanned"] == 1
    assert scan.json()["data"]["columns_scanned"] == 3

    assets = client.get("/api/v1/assets", headers=headers)
    assert assets.status_code == 200
    assert assets.json()["meta"]["count"] == 1
    asset = assets.json()["data"][0]
    assert asset["name"] == "customers"
    assert asset["row_count"] == 2

    detail = client.get(f"/api/v1/assets/{asset['id']}", headers=headers)
    assert detail.status_code == 200
    columns = detail.json()["data"]["columns"]
    assert [column["name"] for column in columns] == ["id", "email", "age"]

    updated_column = client.patch(
        f"/api/v1/assets/{asset['id']}/columns/{columns[1]['id']}",
        headers=headers,
        json={"description": "Customer email address used for contact and identity matching"},
    )
    assert updated_column.status_code == 200
    assert updated_column.json()["data"]["description"] == "Customer email address used for contact and identity matching"

    generated = client.post(
        f"/api/v1/assets/{asset['id']}/columns/generate-metadata",
        headers=headers,
    )
    assert generated.status_code == 200
    assert generated.json()["meta"]["updated_count"] == 3
    generated_columns = generated.json()["data"]["columns"]
    assert all(column["description"] for column in generated_columns)


def test_viewer_can_read_catalogue_but_not_create_connector(client: TestClient, viewer_token: str) -> None:
    headers = {"Authorization": f"Bearer {viewer_token}"}
    assert client.get("/api/v1/assets", headers=headers).status_code == 200
    response = client.post(
        "/api/v1/connectors",
        headers=headers,
        json={"name": "Denied", "connector_type": "sqlite", "config": {}},
    )
    assert response.status_code == 403


def test_admin_cannot_create_connector_to_metadata_database(client: TestClient, admin_token: str) -> None:
    response = client.post(
        "/api/v1/connectors",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "Blocked metadata DB",
            "connector_type": "sqlite",
            "config": {"database_path": "datagov_admin.db"},
        },
    )
    assert response.status_code == 400
    assert "metadata databases cannot be used" in response.json()["detail"]


def test_connector_scope_scans_only_selected_tables(client: TestClient, admin_token: str, tmp_path) -> None:
    db_path = tmp_path / "scoped_source.db"
    with sqlite3.connect(db_path) as connection:
        connection.execute("create table customers (id integer primary key, email text)")
        connection.execute("create table orders (id integer primary key, customer_id integer, amount real)")
        connection.execute("insert into customers (email) values ('a@example.com')")
        connection.execute("insert into orders (customer_id, amount) values (1, 25.50)")
        connection.commit()

    headers = {"Authorization": f"Bearer {admin_token}"}
    created = client.post(
        "/api/v1/connectors",
        headers=headers,
        json={"name": "Scoped SQLite", "connector_type": "sqlite", "config": {"database_path": str(db_path)}},
    )
    assert created.status_code == 200
    connector_id = created.json()["data"]["id"]

    schemas = client.get(f"/api/v1/connectors/{connector_id}/schemas", headers=headers)
    assert schemas.status_code == 200
    assert schemas.json()["data"] == [{"name": "main", "asset_names": ["customers", "orders"]}]

    scope = {"schemas": ["main"], "tables": {"main": ["customers"]}}
    scan = client.post(
        "/api/v1/scans",
        headers=headers,
        json={"connector_ids": [connector_id], "scan_type": "full", "connector_scopes": {connector_id: scope}},
    )
    assert scan.status_code == 200
    assert scan.json()["data"]["assets_scanned"] == 1

    assets = client.get("/api/v1/assets", headers=headers)
    assert assets.status_code == 200
    assert [asset["name"] for asset in assets.json()["data"]] == ["customers"]

    updated = client.patch(
        f"/api/v1/connectors/{connector_id}/scope",
        headers=headers,
        json={"catalogue_scope": {"schemas": ["main"], "tables": {"main": ["orders"]}}},
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["config_encrypted"]["catalogue_scope"]["tables"]["main"] == ["orders"]

    scan = client.post(
        "/api/v1/scans",
        headers=headers,
        json={"connector_ids": [connector_id], "scan_type": "full"},
    )
    assert scan.status_code == 200
    assets = client.get("/api/v1/assets", headers=headers)
    assert [asset["name"] for asset in assets.json()["data"]] == ["orders"]


def test_sqlite_connector_supports_attached_dataset_schemas(client: TestClient, admin_token: str, tmp_path) -> None:
    main_path = tmp_path / "main.db"
    sales_path = tmp_path / "sales.db"
    hr_path = tmp_path / "hr.db"
    with sqlite3.connect(main_path) as connection:
        connection.execute("create table customers (id integer primary key, email text)")
        connection.execute("insert into customers (email) values ('main@example.com')")
        connection.commit()
    with sqlite3.connect(sales_path) as connection:
        connection.execute("create table invoices (id integer primary key, invoice_number text, amount real)")
        connection.execute("insert into invoices values (1, 'INV-1', 100.0)")
        connection.commit()
    with sqlite3.connect(hr_path) as connection:
        connection.execute("create table employees (id integer primary key, work_email text)")
        connection.execute("insert into employees values (1, 'person@example.com')")
        connection.commit()

    headers = {"Authorization": f"Bearer {admin_token}"}
    created = client.post(
        "/api/v1/connectors",
        headers=headers,
        json={
            "name": "Attached SQLite",
            "connector_type": "sqlite",
            "config": {
                "database_path": str(main_path),
                "attached_databases": [
                    {"schema": "sales", "database_path": str(sales_path)},
                    {"schema": "hr", "database_path": str(hr_path)},
                ],
            },
        },
    )
    assert created.status_code == 200
    connector_id = created.json()["data"]["id"]

    schemas = client.get(f"/api/v1/connectors/{connector_id}/schemas", headers=headers)
    assert schemas.status_code == 200
    assert schemas.json()["data"] == [
        {"name": "main", "asset_names": ["customers"]},
        {"name": "sales", "asset_names": ["invoices"]},
        {"name": "hr", "asset_names": ["employees"]},
    ]

    scope = {"schemas": ["sales", "hr"], "tables": {"sales": ["invoices"], "hr": ["employees"]}}
    scan = client.post(
        "/api/v1/scans",
        headers=headers,
        json={"connector_ids": [connector_id], "scan_type": "full", "connector_scopes": {connector_id: scope}},
    )
    assert scan.status_code == 200
    assert scan.json()["data"]["assets_scanned"] == 2
    assets = client.get("/api/v1/assets", headers=headers)
    assert [(asset["schema_name"], asset["name"]) for asset in assets.json()["data"]] == [
        ("hr", "employees"),
        ("sales", "invoices"),
    ]


def test_notification_settings_are_audited_on_scan_completion(client: TestClient, admin_token: str, tmp_path) -> None:
    db_path = tmp_path / "notification_source.db"
    with sqlite3.connect(db_path) as connection:
        connection.execute("create table customers (id integer primary key, email text)")
        connection.execute("insert into customers (email) values ('notify@example.com')")
        connection.commit()

    headers = {"Authorization": f"Bearer {admin_token}"}
    notification = client.post(
        "/api/v1/notifications",
        headers=headers,
        json={"channel": "email", "target": "admin@datagov.local", "events": ["scan_completed"]},
    )
    assert notification.status_code == 200
    setting_id = notification.json()["data"]["id"]

    tested = client.post(f"/api/v1/notifications/{setting_id}/test", headers=headers)
    assert tested.status_code == 200
    assert tested.json()["data"]["success"] is True

    created = client.post(
        "/api/v1/connectors",
        headers=headers,
        json={"name": "Notification SQLite", "connector_type": "sqlite", "config": {"database_path": str(db_path)}},
    )
    assert created.status_code == 200
    scan = client.post(
        "/api/v1/scans",
        headers=headers,
        json={"connector_ids": [created.json()["data"]["id"]], "scan_type": "full"},
    )
    assert scan.status_code == 200
    assert scan.json()["meta"]["notifications_sent"] == 1

    audit = client.get("/api/v1/audit-log", headers=headers, params={"event_type": "notification"})
    assert audit.status_code == 200
    actions = {entry["action"] for entry in audit.json()["data"]}
    assert {"notification_setting_created", "notification_test_sent", "notification_sent"}.issubset(actions)

    disabled = client.patch(f"/api/v1/notifications/{setting_id}", headers=headers, json={"enabled": False})
    assert disabled.status_code == 200
    deleted = client.delete(f"/api/v1/notifications/{setting_id}", headers=headers)
    assert deleted.status_code == 204
