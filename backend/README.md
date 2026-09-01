# Construction Site Store & Tool Accountability System — Backend

Replaces a storekeeper's paper log book with a fast digital system for
issuing and returning tools/equipment on a construction site. Every worker
gets a permanent, sequential **Store Number** (0001, 0002, ...) instead of
a number that changes every day on paper.

## Architecture

```
backend/
├── app/
│   ├── main.py            # FastAPI app, CORS, error handlers
│   ├── core/               # settings, JWT/password security
│   ├── db/                 # SQLAlchemy engine/session, seed script
│   ├── models/              # SQLAlchemy ORM models (source of truth schema)
│   ├── schemas/             # Pydantic request/response models
│   ├── repositories/        # (reserved for future direct-query helpers)
│   ├── services/            # business logic: workers, inventory, transactions, audit
│   ├── api/routes/          # FastAPI routers (thin — delegate to services)
│   ├── auth/                # current-user + RBAC dependencies
│   └── utils/               # PII masking, timezone helpers
├── alembic/                 # DB migrations
├── tests/                   # pytest suite (runs against a real Postgres DB)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

Key design decisions (see the original spec for full rationale):

- **No QR/barcode/NFC.** Workers are found by searching store number, name,
  National ID, or phone.
- **Store numbers never change and are never reused**, even if a worker is
  deactivated. Concurrent registrations are serialized with
  `SELECT ... FOR UPDATE` on a per-site sequence row (see
  `app/services/worker_service.py::_allocate_store_number`), and a
  `SAVEPOINT`-based retry handles the race on the very first worker at a
  new site. This is covered by a real multi-threaded test
  (`tests/test_workers.py::test_concurrent_registrations_never_collide_on_store_number`).
- **Timestamps** are stored in UTC (`timezone=True` columns) and converted
  to `Africa/Nairobi` only at the presentation layer (`app/utils/formatting.py`).
- **Multi-item visits**: issuing/returning several items in one store visit
  creates one `Transaction` row per item — never one opaque combined record.
- **Consumables vs. individually tracked assets** are both modelled:
  `InventoryItem` is the source of truth for consumables; `Asset` rows track
  individually numbered equipment (cutting machines, generators, etc.).
- **Audit log** is append-only; there is no update/delete endpoint for it.

## Requirements

- Python 3.11+
- PostgreSQL 14+ (both for local dev and production)

## Local setup — general (Linux/macOS/Windows/WSL)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edit .env if your Postgres credentials differ from the defaults

# Create the database (adjust to your local Postgres setup):
psql -c "CREATE USER csuser WITH PASSWORD 'devpassword' CREATEDB;"
psql -c "CREATE DATABASE construction_store OWNER csuser;"
psql -c "CREATE DATABASE construction_store_test OWNER csuser;"

alembic upgrade head
python -m app.db.seed          # optional: creates demo company/site/users/workers/inventory

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Visit `http://localhost:8000/api/v1/docs` for interactive OpenAPI docs.

## Local setup — Termux / Acode (Android)

Postgres itself is heavy to run well inside Termux's proot environment. The
recommended workflow on a phone is:

1. **Write code in Acode** (this repo folder), keep Termux for running commands.
2. **Use a remote/managed Postgres for actual running**, even in development —
   the free tier of [Neon](https://neon.tech) works well and matches the
   production target. Create a database there, copy the connection string
   into `.env` as `DATABASE_URL` (Neon gives you a `postgresql://...` URL —
   change the prefix to `postgresql+psycopg://...`).
3. From Termux:

   ```bash
   pkg update && pkg install python postgresql-client
   cd backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   # paste your Neon DATABASE_URL into .env
   alembic upgrade head
   python -m app.db.seed
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

4. Open `http://localhost:8000/api/v1/docs` in Chrome on the same phone.

If you'd rather run Postgres locally inside Termux, `pkg install postgresql`
works, but you'll need to `initdb`, start it with `pg_ctl`, and Termux's
proot filesystem can be slow for disk-heavy workloads — a hosted Postgres is
simpler for day-to-day development from a phone.

## Running tests

Tests run against a **real Postgres database** (not mocks/SQLite) — this is
what actually exercises the row-locking concurrency guarantees.

```bash
# uses construction_store_test by default, see tests/conftest.py
pytest -q
```

25 tests currently cover: login/auth/RBAC, worker registration + store
number sequencing + concurrency, worker search, inventory CRUD + stock
adjustments, and the full issue/return transaction workflow (including
duplicate-return prevention and over-issue prevention).

## Docker

```bash
docker compose up --build
```

This starts Postgres + the backend together, running migrations
automatically on container start. The app is then not tied to Docker,
though — the same code runs with `uvicorn app.main:app` against any
reachable Postgres instance.

## Database migrations

```bash
alembic revision --autogenerate -m "describe your change"
alembic upgrade head
```

Always review autogenerated migrations before applying them, especially
for column type changes or drops.

## Seed data

`python -m app.db.seed` creates (idempotently — safe to re-run):

- Company: "Demo Construction Ltd", Site: "Westlands Construction Site"
- Users: `admin@demo-construction.example.com` / `AdminPass123!` (ADMIN),
  `storekeeper@demo-construction.example.com` / `StorePass123!` (STOREKEEPER),
  `manager@demo-construction.example.com` / `ManagerPass123!` (MANAGER)
- 3 demo workers, 8 demo inventory items (6 consumable, 2 asset-type)

All fake data — no real National IDs or phone numbers.

## API overview

Full interactive docs at `/api/v1/docs`. Highlights:

- `POST /api/v1/auth/login`, `POST /api/v1/auth/refresh`, `GET /api/v1/auth/me`
- `POST /api/v1/workers`, `GET /api/v1/workers/search?site_id=&q=`, `PATCH /api/v1/workers/{id}`
- `POST /api/v1/inventory`, `GET /api/v1/inventory?site_id=`, `POST /api/v1/inventory/{id}/adjust`
- `POST /api/v1/transactions/issue`, `POST /api/v1/transactions/return`, `GET /api/v1/transactions/outstanding?site_id=`
- `GET /api/v1/dashboard?site_id=`, `GET /api/v1/reports/daily?site_id=`, `GET /api/v1/reports/inventory?site_id=`
- `GET /api/v1/audit-logs` (ADMIN only)
- `POST /api/v1/sites`, `POST /api/v1/companies`, `POST /api/v1/departments`, `POST /api/v1/users`

## Production deployment (Vercel + Render + Neon)

- **Database**: create a Neon Postgres project, copy its connection string
  into `DATABASE_URL` (use the pooled connection string for the app, and
  run `alembic upgrade head` once against the direct connection string).
- **Backend**: deploy this `backend/` folder to Render as a Web Service.
  Build command: `pip install -r requirements.txt`. Start command:
  `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
  Set `DATABASE_URL`, `SECRET_KEY` (generate a real one), and `CORS_ORIGINS`
  (your Vercel frontend URL) as environment variables in Render's dashboard
  — never commit them.
- **Frontend**: deploys to Vercel separately (see `frontend/README.md` once
  Phase 2 is built), pointed at the Render backend URL.

## Security notes

- Passwords are hashed with bcrypt (via passlib); never stored or logged in
  plaintext.
- JWT access tokens expire in 8 hours (one shift); refresh tokens in 7 days.
- National ID numbers are masked in all API responses
  (`app/utils/formatting.py::mask_national_id`) — only the last 3 characters
  are shown.
- All list/detail endpoints require authentication; write endpoints are
  further restricted by role (`app/auth/dependencies.py::require_roles`).
- Unhandled exceptions never leak stack traces to clients — they're logged
  server-side and a generic message is returned (`app/main.py`).
- All financial-adjacent state changes (stock adjustments, issues, returns,
  worker/user/item CRUD) write an audit log entry with actor, action, entity,
  and metadata.

## Troubleshooting

- **`connection to server ... failed`**: Postgres isn't running, or
  `DATABASE_URL` in `.env` doesn't match your actual host/port/credentials.
- **`email-validator is not installed`**: re-run `pip install -r requirements.txt`
  — this is a required (not optional) dependency of the Pydantic `EmailStr` type.
- **Alembic can't find models / empty migrations**: make sure `app/models/__init__.py`
  imports every model module — Alembic's autogenerate only sees models that
  have actually been imported before `Base.metadata` is inspected.
- **`value is not a valid email address ... reserved name`**: don't use
  `.test`, `.example`, `.invalid`, or `.localhost` TLDs for seed/test users —
  `email-validator` rejects IANA-reserved TLDs. Use `@example.com` instead.
