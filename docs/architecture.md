# Architecture

## Overview

Company → Site → (Departments, Workers, Inventory, Transactions). A worker
belongs to exactly one site in this MVP. Store numbers are sequential and
unique **within a site**, never reused even after deactivation.

## Data model

- **Company** — top-level tenant.
- **Site** — a physical construction site, belongs to a Company.
- **Department** — optional grouping of workers within a Site.
- **User** — login account with a role (ADMIN, STOREKEEPER, MANAGER),
  optionally scoped to a Company and/or Site.
- **Worker** — a person who can be issued items. Permanent `store_number`
  (zero-padded, e.g. "0001"), National ID, phone, status (ACTIVE/INACTIVE).
- **WorkerStoreNumberSequence** — one row per site; the counter that
  generates the next store number, allocated under `SELECT ... FOR UPDATE`
  so concurrent registrations can never collide.
- **InventoryItem** — a type of stocked item at a site. For CONSUMABLE
  items this row's `total/available/issued_quantity` is authoritative. For
  ASSET items it's a fast-path summary; the individual physical units live
  in `Asset`.
- **Asset** — one physical, individually tracked unit of an ASSET-type
  InventoryItem (a specific cutting machine, a specific generator), with
  its own status (AVAILABLE, ISSUED, DAMAGED, NEEDS_REPAIR, LOST, RETIRED).
- **Transaction** — one issue/return record for one item (one line of a
  multi-item visit). Never deleted; transitions ISSUED → RETURNED.
- **StockAdjustment** — an audited manual change to a consumable's stock.
- **TransactionCorrection** — a controlled request to flag a mistaken
  transaction for admin review; the original Transaction is never edited.
- **AuditLog** — append-only record of who did what, when, to which entity.

## Concurrency-safe store numbers

Two workers registering at the same site at the same instant must never get
the same number. `worker_service._allocate_store_number`:

1. Locks the site's `WorkerStoreNumberSequence` row with
   `SELECT ... FOR UPDATE` inside the same DB transaction as the worker
   insert. Postgres serializes concurrent lockers, so the second request
   blocks until the first commits, then sees the updated `last_number`.
2. For a brand-new site (no sequence row yet), a `SAVEPOINT` handles the
   race where two requests both try to INSERT the first row: the loser's
   insert is rolled back to the savepoint and it re-selects (and locks) the
   row the winner created, instead of erroring out.

This is exercised by a real multi-threaded test with 15 concurrent database
sessions (`tests/test_workers.py`), not a mock.

## Timezones

All timestamp columns are `TIMESTAMP WITH TIME ZONE`, written in UTC
(`datetime.now(timezone.utc)`). Conversion to `Africa/Nairobi` for display
happens only at the API/presentation boundary (`app/utils/formatting.py`),
never in the database.

## Multi-site readiness

Every domain row that matters (`Worker`, `InventoryItem`, `Transaction`)
carries a `site_id`. Store numbers, inventory, and transactions are scoped
per site. A worker transfer feature (moving a worker's site while
preserving or reissuing their number) can be added later without a schema
change — it's a deliberate MVP scope cut, not an architectural gap.

## Why services, not fat routes

Routes in `app/api/routes/` only: (1) enforce auth/RBAC via FastAPI
dependencies, (2) parse/validate via Pydantic schemas, (3) call a function
in `app/services/`, (4) write an audit log entry, (5) commit and return.
All business rules (availability checks, quantity math, status
transitions) live in `app/services/`, which is what the test suite exercises
directly for the concurrency test and indirectly (via the API) for
everything else.
