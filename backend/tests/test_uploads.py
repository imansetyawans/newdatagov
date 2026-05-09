from fastapi.testclient import TestClient


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _loan_csv() -> bytes:
    return (
        "Loan_ID,Gender,Married,Dependents,Education,Self_Employed,ApplicantIncome,CoapplicantIncome,"
        "LoanAmount,Loan_Amount_Term,Credit_History,Property_Area\n"
        "LP001015,Male,Yes,0,Graduate,No,5720,0,110,360,1,Urban\n"
        "LP001022,Male,Yes,1,Graduate,No,3076,1500,126,360,1,Urban\n"
        "LP001031,Male,Yes,2,Graduate,No,5000,1800,208,360,1,Urban\n"
        "LP001035,Male,Yes,2,Graduate,No,2340,2546,100,360,,Urban\n"
        "LP001051,Male,No,0,Not Graduate,No,3276,0,78,360,1,Urban\n"
        "LP001054,Male,Yes,0,Not Graduate,Yes,2165,3422,152,360,1,Semiurban\n"
    ).encode("utf-8")


def test_upload_csv_processes_catalogue_quality_samples_and_policies(client: TestClient, admin_token: str, viewer_token: str) -> None:
    admin_headers = _headers(admin_token)
    viewer_headers = _headers(viewer_token)
    policy = client.post(
        "/api/v1/policies",
        headers=admin_headers,
        json={
            "name": "Loan IDs are restricted",
            "policy_type": "classification",
            "status": "active",
            "rules": [{"field": "column_name", "operator": "contains", "value": "Loan_ID"}],
            "action": {"classification": "Restricted"},
        },
    )
    assert policy.status_code == 200

    response = client.post(
        "/api/v1/uploads/datasets",
        headers=admin_headers,
        data={
            "schema_name": "loan",
            "table_name": "loan_sanction_test",
            "description": "Loan sanction test dataset",
        },
        files={"file": ("loan_sanction_test.csv", _loan_csv(), "text/csv")},
    )
    assert response.status_code == 200
    payload = response.json()
    asset = payload["data"]
    assert asset["source_path"] == "upload.loan.loan_sanction_test"
    assert asset["row_count"] == 6
    assert asset["dq_score"] is not None
    assert payload["meta"]["columns"] == 12
    assert payload["meta"]["policies_applied"] == 1

    columns = asset["columns"]
    loan_id = next(column for column in columns if column["name"] == "Loan_ID")
    credit_history = next(column for column in columns if column["name"] == "Credit_History")
    property_area = next(column for column in columns if column["name"] == "Property_Area")
    applicant_income = next(column for column in columns if column["name"] == "ApplicantIncome")

    assert loan_id["sample_values"][:2] == ["LP001015", "LP001022"]
    assert "Restricted" in loan_id["classifications"]
    assert credit_history["completeness_score"] == 83.3
    assert property_area["standard_format"] == "controlled vocabulary: Urban, Semiurban"
    assert applicant_income["data_type"] == "INTEGER"
    assert applicant_income["accuracy_score"] == 100.0

    sample = client.get(f"/api/v1/assets/{asset['id']}/sample", headers=viewer_headers)
    assert sample.status_code == 200
    assert sample.json()["data"] == []
    assert sample.json()["meta"]["source"] == "stored_column_samples"
    assert sample.json()["meta"]["column_samples"]["Loan_ID"] == ["*****"]
    assert sample.json()["meta"]["column_samples"]["Property_Area"] == ["Urban", "Semiurban"]

    scores = client.get("/api/v1/dq/scores", headers=admin_headers)
    assert scores.status_code == 200
    assert scores.json()["meta"]["count"] == 1

    issues = client.get("/api/v1/dq/issues", headers=admin_headers)
    assert issues.status_code == 200
    assert any(issue["metric_name"] == "completeness" for issue in issues.json()["data"])

    audit = client.get("/api/v1/audit-log", headers=admin_headers)
    assert audit.status_code == 200
    actions = {entry["action"] for entry in audit.json()["data"]}
    assert {"dataset_uploaded", "uploaded_dataset_quality_processed", "uploaded_dataset_policies_applied"}.issubset(actions)


def test_upload_rejects_invalid_files(client: TestClient, admin_token: str) -> None:
    headers = _headers(admin_token)
    unsupported = client.post(
        "/api/v1/uploads/datasets",
        headers=headers,
        data={"schema_name": "bad", "table_name": "bad_file"},
        files={"file": ("bad.txt", b"hello", "text/plain")},
    )
    assert unsupported.status_code == 400
    assert "Unsupported file type" in unsupported.json()["detail"]

    duplicate_headers = client.post(
        "/api/v1/uploads/datasets",
        headers=headers,
        data={"schema_name": "bad", "table_name": "duplicate_headers"},
        files={"file": ("duplicate.csv", b"id,id\n1,2\n", "text/csv")},
    )
    assert duplicate_headers.status_code == 400
    assert "unique" in duplicate_headers.json()["detail"]
