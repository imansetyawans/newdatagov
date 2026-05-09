from fastapi.testclient import TestClient


def test_login_returns_token_and_user(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.local", "password": "admin123"},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["access_token"]
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 28_800
    assert data["user"]["role"] == "admin"


def test_login_rejects_invalid_password(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.local", "password": "wrong"},
    )

    assert response.status_code == 401


def test_users_me_requires_valid_bearer_token(client: TestClient) -> None:
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.local", "password": "admin123"},
    )
    token = login.json()["data"]["access_token"]

    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["email"] == "admin@test.local"


def test_users_me_rejects_missing_token(client: TestClient) -> None:
    response = client.get("/api/v1/users/me")

    assert response.status_code == 401


def test_admin_can_invite_and_update_user(client: TestClient, admin_token: str) -> None:
    headers = {"Authorization": f"Bearer {admin_token}"}
    invite = client.post(
        "/api/v1/users/invite",
        headers=headers,
        json={
            "email": "editor@test.local",
            "full_name": "Test Editor",
            "role": "editor",
            "password": "editor123",
        },
    )
    assert invite.status_code == 200
    user_id = invite.json()["data"]["id"]

    update = client.patch(
        f"/api/v1/users/{user_id}",
        headers=headers,
        json={"role": "viewer", "is_active": False},
    )
    assert update.status_code == 200
    assert update.json()["data"]["role"] == "viewer"
    assert update.json()["data"]["is_active"] is False


def test_viewer_cannot_invite_user(client: TestClient, viewer_token: str) -> None:
    response = client.post(
        "/api/v1/users/invite",
        headers={"Authorization": f"Bearer {viewer_token}"},
        json={"email": "x@test.local", "full_name": "X User", "role": "viewer"},
    )
    assert response.status_code == 403
