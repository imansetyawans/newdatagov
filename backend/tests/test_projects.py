from fastapi.testclient import TestClient


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_project_category_crud_and_asset_assignment(client: TestClient, admin_token: str) -> None:
    headers = _headers(admin_token)

    project_response = client.post(
        "/api/v1/projects",
        headers=headers,
        json={"name": "Loan Origination", "code": "loan_origination", "description": "Loan data governance"},
    )
    assert project_response.status_code == 200
    project = project_response.json()["data"]

    category_response = client.post(
        "/api/v1/project-categories",
        headers=headers,
        json={
            "project_id": project["id"],
            "name": "Credit Risk",
            "code": "credit_risk",
            "description": "Loan approval and risk assets",
        },
    )
    assert category_response.status_code == 200
    category = category_response.json()["data"]

    upload_response = client.post(
        "/api/v1/uploads/datasets",
        headers=headers,
        data={
            "schema_name": "loan",
            "table_name": "loan_project_test",
            "project_id": project["id"],
            "category_id": category["id"],
        },
        files={"file": ("loan.csv", b"id,email\n1,a@test.local\n", "text/csv")},
    )
    assert upload_response.status_code == 200
    asset = upload_response.json()["data"]
    assert asset["project_id"] == project["id"]
    assert asset["category_id"] == category["id"]
    assert asset["project_name"] == "Loan Origination"
    assert asset["category_name"] == "Credit Risk"

    filtered = client.get(f"/api/v1/assets?project_id={project['id']}&category_id={category['id']}", headers=headers)
    assert filtered.status_code == 200
    assert filtered.json()["meta"]["count"] == 1

    unassigned = client.get("/api/v1/assets?unassigned=true", headers=headers)
    assert unassigned.status_code == 200
    assert unassigned.json()["meta"]["count"] == 0

    project_detail = client.get(f"/api/v1/projects/{project['id']}", headers=headers)
    assert project_detail.status_code == 200
    assert project_detail.json()["data"]["asset_count"] == 1
    assert project_detail.json()["data"]["categories"][0]["asset_count"] == 1


def test_category_must_belong_to_selected_project(client: TestClient, admin_token: str) -> None:
    headers = _headers(admin_token)
    project_one = client.post("/api/v1/projects", headers=headers, json={"name": "Project One", "code": "project_one"}).json()["data"]
    project_two = client.post("/api/v1/projects", headers=headers, json={"name": "Project Two", "code": "project_two"}).json()["data"]
    category = client.post(
        "/api/v1/project-categories",
        headers=headers,
        json={"project_id": project_one["id"], "name": "Category One", "code": "category_one"},
    ).json()["data"]

    response = client.post(
        "/api/v1/uploads/datasets",
        headers=headers,
        data={
            "schema_name": "bad",
            "table_name": "bad_assignment",
            "project_id": project_two["id"],
            "category_id": category["id"],
        },
        files={"file": ("bad.csv", b"id\n1\n", "text/csv")},
    )
    assert response.status_code == 400
    assert "category" in response.json()["detail"].lower()
