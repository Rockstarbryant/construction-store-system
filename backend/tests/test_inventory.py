from tests.conftest import auth_headers


def _create_item(client, headers, site_id, name="Spade", item_type="CONSUMABLE", qty=10):
    return client.post(
        "/api/v1/inventory",
        headers=headers,
        json={"site_id": str(site_id), "name": name, "item_type": item_type, "initial_quantity": qty},
    )


def test_create_and_list_item(client, admin_user, site):
    headers = auth_headers(client, admin_user.email)
    r = _create_item(client, headers, site.id)
    assert r.status_code == 201
    assert r.json()["available_quantity"] == 10

    listing = client.get(f"/api/v1/inventory?site_id={site.id}", headers=headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1


def test_duplicate_item_name_rejected(client, admin_user, site):
    headers = auth_headers(client, admin_user.email)
    _create_item(client, headers, site.id, name="Bucket")
    r2 = _create_item(client, headers, site.id, name="Bucket")
    assert r2.status_code == 409


def test_stock_adjustment_updates_quantities(client, admin_user, site):
    headers = auth_headers(client, admin_user.email)
    item = _create_item(client, headers, site.id, name="Nails", qty=100).json()

    r = client.post(
        f"/api/v1/inventory/{item['id']}/adjust",
        headers=headers,
        json={"delta": -20, "reason": "Used on formwork"},
    )
    assert r.status_code == 200
    assert r.json()["new_quantity"] == 80

    updated_item = client.get(f"/api/v1/inventory/{item['id']}", headers=headers).json()
    assert updated_item["available_quantity"] == 80


def test_stock_adjustment_cannot_go_negative(client, admin_user, site):
    headers = auth_headers(client, admin_user.email)
    item = _create_item(client, headers, site.id, name="Gloves", qty=5).json()

    r = client.post(
        f"/api/v1/inventory/{item['id']}/adjust",
        headers=headers,
        json={"delta": -10, "reason": "Too many"},
    )
    assert r.status_code == 400
