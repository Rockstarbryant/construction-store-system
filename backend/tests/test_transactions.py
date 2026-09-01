from tests.conftest import auth_headers


def _setup_worker_and_item(client, headers, site_id, qty=5, admin_headers=None):
    worker = client.post(
        "/api/v1/workers",
        headers=headers,
        json={
            "site_id": str(site_id),
            "full_name": "John Kamau",
            "national_id": "10000001",
            "phone_number": "0712000001",
        },
    ).json()
    item = client.post(
        "/api/v1/inventory",
        headers=admin_headers or headers,
        json={"site_id": str(site_id), "name": "Safety Belt", "item_type": "CONSUMABLE", "initial_quantity": qty},
    ).json()
    return worker, item


def test_issue_then_return_workflow(client, storekeeper_user, admin_user, site):
    headers = auth_headers(client, storekeeper_user.email)
    admin_headers = auth_headers(client, admin_user.email)
    worker, item = _setup_worker_and_item(client, headers, site.id, admin_headers=admin_headers)

    issue = client.post(
        "/api/v1/transactions/issue",
        headers=headers,
        json={"worker_id": worker["id"], "items": [{"inventory_item_id": item["id"], "quantity": 1}]},
    )
    assert issue.status_code == 200
    txn = issue.json()[0]
    assert txn["status"] == "ISSUED"

    outstanding = client.get(f"/api/v1/transactions/outstanding?site_id={site.id}", headers=headers)
    assert len(outstanding.json()) == 1

    ret = client.post(
        "/api/v1/transactions/return",
        headers=headers,
        json={"items": [{"transaction_id": txn["id"], "condition_on_return": "GOOD"}]},
    )
    assert ret.status_code == 200
    assert ret.json()[0]["status"] == "RETURNED"

    outstanding_after = client.get(f"/api/v1/transactions/outstanding?site_id={site.id}", headers=headers)
    assert len(outstanding_after.json()) == 0


def test_cannot_return_already_returned_transaction(client, storekeeper_user, admin_user, site):
    headers = auth_headers(client, storekeeper_user.email)
    admin_headers = auth_headers(client, admin_user.email)
    worker, item = _setup_worker_and_item(client, headers, site.id, admin_headers=admin_headers)
    txn = client.post(
        "/api/v1/transactions/issue",
        headers=headers,
        json={"worker_id": worker["id"], "items": [{"inventory_item_id": item["id"], "quantity": 1}]},
    ).json()[0]

    r1 = client.post(
        "/api/v1/transactions/return", headers=headers, json={"items": [{"transaction_id": txn["id"]}]}
    )
    assert r1.status_code == 200

    r2 = client.post(
        "/api/v1/transactions/return", headers=headers, json={"items": [{"transaction_id": txn["id"]}]}
    )
    assert r2.status_code == 400
    assert "already been returned" in r2.json()["detail"]


def test_cannot_issue_more_than_available(client, storekeeper_user, admin_user, site):
    headers = auth_headers(client, storekeeper_user.email)
    admin_headers = auth_headers(client, admin_user.email)
    worker, item = _setup_worker_and_item(client, headers, site.id, qty=2, admin_headers=admin_headers)

    r = client.post(
        "/api/v1/transactions/issue",
        headers=headers,
        json={"worker_id": worker["id"], "items": [{"inventory_item_id": item["id"], "quantity": 5}]},
    )
    assert r.status_code == 400
    assert "available" in r.json()["detail"].lower()


def test_multiple_items_issued_in_one_visit_have_separate_transactions(client, storekeeper_user, admin_user, site):
    headers = auth_headers(client, storekeeper_user.email)
    admin_headers = auth_headers(client, admin_user.email)
    worker, item1 = _setup_worker_and_item(client, headers, site.id, admin_headers=admin_headers)
    item2 = client.post(
        "/api/v1/inventory",
        headers=admin_headers,
        json={"site_id": str(site.id), "name": "Spade", "item_type": "CONSUMABLE", "initial_quantity": 5},
    ).json()

    r = client.post(
        "/api/v1/transactions/issue",
        headers=headers,
        json={
            "worker_id": worker["id"],
            "items": [
                {"inventory_item_id": item1["id"], "quantity": 1},
                {"inventory_item_id": item2["id"], "quantity": 1},
            ],
        },
    )
    assert r.status_code == 200
    txns = r.json()
    assert len(txns) == 2
    assert {t["id"] for t in txns}.__len__() == 2  # distinct transaction records


def test_inactive_worker_cannot_be_issued_items(client, storekeeper_user, admin_user, site):
    headers = auth_headers(client, storekeeper_user.email)
    admin_headers = auth_headers(client, admin_user.email)
    worker, item = _setup_worker_and_item(client, headers, site.id, admin_headers=admin_headers)
    client.patch(f"/api/v1/workers/{worker['id']}", headers=headers, json={"status": "INACTIVE"})

    r = client.post(
        "/api/v1/transactions/issue",
        headers=headers,
        json={"worker_id": worker["id"], "items": [{"inventory_item_id": item["id"], "quantity": 1}]},
    )
    assert r.status_code == 400
