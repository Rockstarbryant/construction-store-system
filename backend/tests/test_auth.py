from tests.conftest import auth_headers


def test_login_success(client, storekeeper_user):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": storekeeper_user.email, "password": "Password123!"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password(client, storekeeper_user):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": storekeeper_user.email, "password": "WrongPassword!"},
    )
    assert resp.status_code == 401


def test_login_unknown_email(client):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "whatever123"},
    )
    assert resp.status_code == 401


def test_me_requires_token(client):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401


def test_me_returns_current_user(client, storekeeper_user):
    headers = auth_headers(client, storekeeper_user.email)
    resp = client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == storekeeper_user.email
    assert resp.json()["role"] == "STOREKEEPER"


def test_storekeeper_cannot_create_inventory_item(client, storekeeper_user, site):
    headers = auth_headers(client, storekeeper_user.email)
    resp = client.post(
        "/api/v1/inventory",
        headers=headers,
        json={"site_id": str(site.id), "name": "Drill", "item_type": "CONSUMABLE", "initial_quantity": 5},
    )
    assert resp.status_code == 403


def test_admin_can_create_inventory_item(client, admin_user, site):
    headers = auth_headers(client, admin_user.email)
    resp = client.post(
        "/api/v1/inventory",
        headers=headers,
        json={"site_id": str(site.id), "name": "Drill", "item_type": "CONSUMABLE", "initial_quantity": 5},
    )
    assert resp.status_code == 201


def test_manager_cannot_register_worker(client, manager_user, site):
    headers = auth_headers(client, manager_user.email)
    resp = client.post(
        "/api/v1/workers",
        headers=headers,
        json={
            "site_id": str(site.id),
            "full_name": "Test Worker",
            "national_id": "12345678",
            "phone_number": "0712345678",
        },
    )
    assert resp.status_code == 403
