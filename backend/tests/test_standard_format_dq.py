import sqlite3

from fastapi.testclient import TestClient

from app.models import Column
from app.services.standard_format_rules import matcher_from_standard_format
from app.services.upload_service import _consistency_score


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_standard_format_matchers_validate_expected_values() -> None:
    email_matcher = matcher_from_standard_format("valid email address")
    assert email_matcher is not None
    assert email_matcher("ana@example.com") is True
    assert email_matcher("not-email") is False

    vocabulary_matcher = matcher_from_standard_format("controlled vocabulary: Male, Female")
    assert vocabulary_matcher is not None
    assert vocabulary_matcher("female") is True
    assert vocabulary_matcher("Unknown") is False

    decimal_matcher = matcher_from_standard_format("decimal number")
    assert decimal_matcher is not None
    assert decimal_matcher("12") is True
    assert decimal_matcher("12.50") is True
    assert decimal_matcher("twelve") is False

    assert matcher_from_standard_format("business-specific display rule") is None


def test_uploaded_consistency_uses_standard_format_only_when_auto_rule_missing() -> None:
    neutral_column = Column(name="Contact", data_type="TEXT", standard_format="valid email address")
    assert _consistency_score(neutral_column, ["ana@example.com", "bad-value"]) == 50.0

    vocabulary_column = Column(name="ApplicantType", data_type="TEXT", standard_format="controlled vocabulary: New, Returning")
    assert _consistency_score(vocabulary_column, ["new", "Returning", "Unknown"]) == 66.7

    auto_email_column = Column(name="email", data_type="TEXT", standard_format="free text")
    assert _consistency_score(auto_email_column, ["ana@example.com", "bad-value"]) == 50.0

    custom_format_column = Column(name="Reference", data_type="TEXT", standard_format="business-specific display rule")
    assert _consistency_score(custom_format_column, ["A-1", "B-2"]) == 100.0


def test_scanned_consistency_uses_standard_format_after_next_scan(
    client: TestClient,
    admin_token: str,
    tmp_path,
) -> None:
    db_path = tmp_path / "standard_format_source.db"
    with sqlite3.connect(db_path) as connection:
        connection.execute("create table prospects (id integer primary key, contact text)")
        connection.executemany(
            "insert into prospects (contact) values (?)",
            [("ana@example.com",), ("not-email",)],
        )
        connection.commit()

    headers = _headers(admin_token)
    connector = client.post(
        "/api/v1/connectors",
        headers=headers,
        json={"name": "Standard Format SQLite", "connector_type": "sqlite", "config": {"database_path": str(db_path)}},
    )
    assert connector.status_code == 200
    connector_id = connector.json()["data"]["id"]

    first_scan = client.post("/api/v1/scans", headers=headers, json={"connector_ids": [connector_id], "scan_type": "full"})
    assert first_scan.status_code == 200

    asset = client.get("/api/v1/assets", headers=headers).json()["data"][0]
    first_detail = client.get(f"/api/v1/assets/{asset['id']}", headers=headers)
    contact = next(column for column in first_detail.json()["data"]["columns"] if column["name"] == "contact")
    assert contact["consistency_score"] == 100.0

    patched = client.patch(
        f"/api/v1/assets/{asset['id']}/columns/{contact['id']}",
        headers=headers,
        json={"standard_format": "valid email address"},
    )
    assert patched.status_code == 200

    second_scan = client.post("/api/v1/scans", headers=headers, json={"connector_ids": [connector_id], "scan_type": "full"})
    assert second_scan.status_code == 200

    second_detail = client.get(f"/api/v1/assets/{asset['id']}", headers=headers)
    rescored_contact = next(column for column in second_detail.json()["data"]["columns"] if column["name"] == "contact")
    assert rescored_contact["standard_format"] == "valid email address"
    assert rescored_contact["consistency_score"] == 50.0

    issues = client.get("/api/v1/dq/issues", headers=headers, params={"asset_id": asset["id"], "status_filter": "open"})
    assert issues.status_code == 200
    assert any(issue["metric_name"] == "consistency" for issue in issues.json()["data"])
