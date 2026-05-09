import sqlite3

from fastapi.testclient import TestClient


def _create_source(path) -> None:
    with sqlite3.connect(path) as connection:
        connection.execute("create table customers (id integer primary key, email text, age integer, status text)")
        connection.executemany(
            "insert into customers (email, age, status) values (?, ?, ?)",
            [
                ("ana@example.com", 31, "active"),
                ("bima@example.com", 27, "inactive"),
                ("citra@example.com", 44, "pending"),
                ("dian@example.com", 36, "active"),
            ],
        )
        connection.commit()


def _create_connector(client: TestClient, headers: dict[str, str], db_path) -> str:
    created = client.post(
        "/api/v1/connectors",
        headers=headers,
        json={"name": "Phase 2 SQLite", "connector_type": "sqlite", "config": {"database_path": str(db_path)}},
    )
    assert created.status_code == 200
    return created.json()["data"]["id"]


def _run_scan(client: TestClient, headers: dict[str, str], connector_id: str) -> dict:
    response = client.post(
        "/api/v1/scans",
        headers=headers,
        json={"connector_ids": [connector_id], "scan_type": "full"},
    )
    assert response.status_code == 200
    return response.json()["data"]


def test_phase2_quality_policy_masking_and_audit_flow(
    client: TestClient,
    admin_token: str,
    viewer_token: str,
    tmp_path,
) -> None:
    db_path = tmp_path / "phase2_source.db"
    _create_source(db_path)

    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    viewer_headers = {"Authorization": f"Bearer {viewer_token}"}
    connector_id = _create_connector(client, admin_headers, db_path)

    labels = client.get("/api/v1/classifications", headers=admin_headers)
    assert labels.status_code == 200
    assert any(label["name"] == "PII" and label["masks_samples"] for label in labels.json()["data"])

    custom_label = client.post(
        "/api/v1/classifications",
        headers=admin_headers,
        json={
            "name": "Highly Confidential",
            "color_key": "danger",
            "description": "Business-critical restricted data",
            "masks_samples": True,
        },
    )
    assert custom_label.status_code == 200
    assert custom_label.json()["data"]["masks_samples"] is True

    policy = client.post(
        "/api/v1/policies",
        headers=admin_headers,
        json={
            "name": "Email columns are PII",
            "policy_type": "classification",
            "status": "active",
            "rules": [{"field": "column_name", "operator": "contains", "value": "email"}],
            "action": {"classification": "PII"},
        },
    )
    assert policy.status_code == 200

    custom_policy = client.post(
        "/api/v1/policies",
        headers=admin_headers,
        json={
            "name": "Email columns are highly confidential",
            "policy_type": "classification",
            "status": "active",
            "rules": [{"field": "column_name", "operator": "contains", "value": "email"}],
            "action": {"classification": "Highly Confidential"},
        },
    )
    assert custom_policy.status_code == 200

    scan = _run_scan(client, admin_headers, connector_id)
    assert scan["status"] == "completed"
    assert scan["policies_applied"] == 2

    assets = client.get("/api/v1/assets", headers=admin_headers).json()["data"]
    asset = assets[0]
    assert asset["dq_score"] is not None

    detail = client.get(f"/api/v1/assets/{asset['id']}", headers=admin_headers)
    columns = detail.json()["data"]["columns"]
    email = next(column for column in columns if column["name"] == "email")
    assert "PII" in email["classifications"]
    assert "Highly Confidential" in email["classifications"]
    assert email["completeness_score"] == 100.0
    assert email["consistency_score"] == 100.0

    broad_policy = client.post(
        "/api/v1/policies",
        headers=admin_headers,
        json={
            "name": "Status columns are PII",
            "policy_type": "classification",
            "status": "active",
            "rules": [{"field": "column_name", "operator": "contains", "value": "status"}],
            "action": {"classification": "PII"},
        },
    )
    assert broad_policy.status_code == 200
    detail_after_broad_policy = client.get(f"/api/v1/assets/{asset['id']}", headers=admin_headers)
    status = next(column for column in detail_after_broad_policy.json()["data"]["columns"] if column["name"] == "status")
    assert "PII" in status["classifications"]

    deleted_broad_policy = client.delete(f"/api/v1/policies/{broad_policy.json()['data']['id']}", headers=admin_headers)
    assert deleted_broad_policy.status_code == 204
    detail_after_delete = client.get(f"/api/v1/assets/{asset['id']}", headers=admin_headers)
    status = next(column for column in detail_after_delete.json()["data"]["columns"] if column["name"] == "status")
    email = next(column for column in detail_after_delete.json()["data"]["columns"] if column["name"] == "email")
    assert "PII" not in status["classifications"]
    assert "PII" in email["classifications"]

    detected = client.post(f"/api/v1/assets/{asset['id']}/columns/detect-formats", headers=admin_headers)
    assert detected.status_code == 200
    detected_columns = detected.json()["data"]["columns"]
    detected_email = next(column for column in detected_columns if column["name"] == "email")
    detected_status = next(column for column in detected_columns if column["name"] == "status")
    assert detected_email["standard_format"] == "valid email address"
    assert detected_status["standard_format"] == "controlled vocabulary: active, inactive, pending"

    saved_column = client.patch(
        f"/api/v1/assets/{asset['id']}/columns/{email['id']}",
        headers=admin_headers,
        json={"description": "Customer email address", "standard_format": "lowercase valid email address"},
    )
    assert saved_column.status_code == 200
    assert saved_column.json()["data"]["standard_format"] == "lowercase valid email address"

    scores = client.get("/api/v1/dq/scores", headers=admin_headers)
    assert scores.status_code == 200
    assert scores.json()["meta"]["count"] == 1

    coverage = client.get("/api/v1/governance/coverage", headers=admin_headers)
    assert coverage.status_code == 200
    assert coverage.json()["data"]["pii_columns"] == 1

    sample = client.get(f"/api/v1/assets/{asset['id']}/sample", headers=viewer_headers)
    assert sample.status_code == 200
    assert sample.json()["data"][0]["email"] == "*****"
    assert sample.json()["meta"]["masked_columns"] == ["email"]
    assert sample.json()["meta"]["column_samples"]["email"] == ["*****"]
    assert sample.json()["meta"]["column_samples"]["status"] == ["active", "inactive", "pending"]

    with sqlite3.connect(db_path) as connection:
        connection.execute("update customers set email = null where id in (1, 2, 3)")
        connection.execute("update customers set age = 200 where id in (1, 2)")
        connection.commit()

    degraded_scan = _run_scan(client, admin_headers, connector_id)
    assert degraded_scan["dq_issues_raised"] >= 1

    issues = client.get("/api/v1/dq/issues", headers=admin_headers, params={"status_filter": "open"})
    assert issues.status_code == 200
    open_issues = issues.json()["data"]
    assert open_issues

    resolved = client.patch(
        f"/api/v1/dq/issues/{open_issues[0]['id']}",
        headers=admin_headers,
        json={"status": "resolved", "resolution_note": "Accepted for Phase 2 regression test"},
    )
    assert resolved.status_code == 200
    assert resolved.json()["data"]["status"] == "resolved"

    audit = client.get("/api/v1/audit-log", headers=admin_headers)
    assert audit.status_code == 200
    actions = {entry["action"] for entry in audit.json()["data"]}
    assert {"policy_created", "sample_viewed", "dq_issue_updated"}.issubset(actions)
    assert any(entry["user_email"] == "admin@test.local" for entry in audit.json()["data"])
