import threading

from sqlalchemy import select

from app.models.worker import Worker
from tests.conftest import TestingSessionLocal, auth_headers


def _register(client, headers, site_id, full_name, national_id, phone="0712345678"):
    return client.post(
        "/api/v1/workers",
        headers=headers,
        json={
            "site_id": str(site_id),
            "full_name": full_name,
            "national_id": national_id,
            "phone_number": phone,
        },
    )


def test_register_worker_assigns_sequential_store_number(client, storekeeper_user, site):
    headers = auth_headers(client, storekeeper_user.email)
    r1 = _register(client, headers, site.id, "John Kamau", "10000001", "0712000001")
    r2 = _register(client, headers, site.id, "Peter Otieno", "10000002", "0712000002")
    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r1.json()["store_number"] == "0001"
    assert r2.json()["store_number"] == "0002"


def test_national_id_masked_in_response(client, storekeeper_user, site):
    headers = auth_headers(client, storekeeper_user.email)
    r = _register(client, headers, site.id, "Jane Doe", "99998888")
    assert r.status_code == 201
    assert r.json()["national_id_masked"] == "*****888"
    assert "99998888" not in r.text


def test_duplicate_active_worker_rejected(client, storekeeper_user, site):
    headers = auth_headers(client, storekeeper_user.email)
    _register(client, headers, site.id, "John Kamau", "10000001", "0712000001")
    r2 = _register(client, headers, site.id, "John Kamau Duplicate", "10000001", "0712000009")
    assert r2.status_code == 409


def test_deactivated_worker_number_never_reused(client, storekeeper_user, site):
    headers = auth_headers(client, storekeeper_user.email)
    r1 = _register(client, headers, site.id, "Worker One", "10000001", "0712000001")
    worker_id = r1.json()["id"]
    assert r1.json()["store_number"] == "0001"

    # Deactivate worker 0001
    patch = client.patch(f"/api/v1/workers/{worker_id}", headers=headers, json={"status": "INACTIVE"})
    assert patch.status_code == 200

    # Register a brand new worker - must get 0002, not 0001
    r2 = _register(client, headers, site.id, "Worker Two", "20000002", "0712000002")
    assert r2.status_code == 201
    assert r2.json()["store_number"] == "0002"


def test_reactivating_same_national_id_restores_original_number(client, storekeeper_user, site):
    headers = auth_headers(client, storekeeper_user.email)
    r1 = _register(client, headers, site.id, "Worker One", "10000001", "0712000001")
    worker_id = r1.json()["id"]
    client.patch(f"/api/v1/workers/{worker_id}", headers=headers, json={"status": "INACTIVE"})

    # Re-register with the same National ID -> should reactivate with SAME store number
    r2 = _register(client, headers, site.id, "Worker One", "10000001", "0712000001")
    assert r2.status_code == 201
    assert r2.json()["store_number"] == "0001"
    assert r2.json()["status"] == "ACTIVE"


def test_search_by_name_store_number_and_phone(client, storekeeper_user, site):
    headers = auth_headers(client, storekeeper_user.email)
    _register(client, headers, site.id, "John Kamau", "10000001", "0712000001")

    by_name = client.get(f"/api/v1/workers/search?site_id={site.id}&q=John", headers=headers)
    assert len(by_name.json()) == 1

    by_store_number = client.get(f"/api/v1/workers/search?site_id={site.id}&q=0001", headers=headers)
    assert len(by_store_number.json()) == 1

    by_phone = client.get(f"/api/v1/workers/search?site_id={site.id}&q=712000001", headers=headers)
    assert len(by_phone.json()) == 1


def test_invalid_phone_number_rejected(client, storekeeper_user, site):
    headers = auth_headers(client, storekeeper_user.email)
    resp = _register(client, headers, site.id, "Bad Phone", "10000099", phone="12345")
    assert resp.status_code == 422


def test_concurrent_registrations_never_collide_on_store_number(site):
    """
    Directly exercises the service-layer store-number allocator with real
    concurrent DB transactions (bypassing the HTTP layer/TestClient, which
    is not thread-safe) to prove SELECT ... FOR UPDATE serializes allocation.
    """
    from app.schemas.worker import WorkerCreate
    from app.services.worker_service import register_worker

    results: list[str] = []
    errors: list[Exception] = []
    lock = threading.Lock()

    def _worker(i: int):
        session = TestingSessionLocal()
        try:
            payload = WorkerCreate(
                site_id=site.id,
                full_name=f"Concurrent Worker {i}",
                national_id=f"CONC{i:04d}",
                phone_number=f"07120{i:05d}",
            )
            w = register_worker(session, payload)
            session.commit()
            with lock:
                results.append(w.store_number)
        except Exception as exc:  # pragma: no cover - failure path surfaced via assertion
            session.rollback()
            with lock:
                errors.append(exc)
        finally:
            session.close()

    threads = [threading.Thread(target=_worker, args=(i,)) for i in range(15)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Unexpected errors during concurrent registration: {errors}"
    assert len(results) == 15
    assert len(set(results)) == 15, f"Store numbers collided: {results}"
