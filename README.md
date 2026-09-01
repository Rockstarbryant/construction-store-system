# Construction Site Store & Tool Accountability System

Replaces a construction site's paper storekeeper log with a fast digital
system: register a worker once, get a permanent Store Number, then issue
and return tools in a few taps — with full transaction history, outstanding
items tracking, and audit logging.

## Status

- **Phase 1 (Backend): complete.** FastAPI + PostgreSQL + SQLAlchemy +
  Alembic. 25 automated tests passing against a real Postgres database,
  including a genuine multi-threaded concurrency test for store-number
  allocation. See `backend/README.md`.
- **Phase 2 (Frontend): complete.** Next.js + TypeScript + Tailwind CSS,
  mobile-first (bottom tab nav, large touch targets). Verified with a real
  headless-browser (Playwright) walkthrough against the live backend:
  login, worker search, worker registration, issuing items, the
  outstanding-items list, and returning items. See `frontend/README.md`.

Both include Termux/Acode-specific setup notes since this was built from
a phone.

## Repository layout

```
construction-store-system/
├── backend/            # FastAPI backend (complete)
├── frontend/            # Next.js frontend (complete)
├── docs/
│   ├── architecture.md
│   ├── api.md
│   └── deployment.md
└── README.md             # this file
```

## Quick start

Backend first (see `backend/README.md` for full detail):

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then edit DATABASE_URL for your Postgres
alembic upgrade head
python -m app.db.seed
uvicorn app.main:app --reload
```

Then the frontend (see `frontend/README.md`):

```bash
cd frontend
npm install
cp .env.example .env.local   # NEXT_PUBLIC_API_URL, defaults to http://localhost:8000
npm run dev
```

Open `http://localhost:3000` and log in with a seeded demo account
(printed by the seed script, also documented in `backend/README.md`).

## Demo accounts (after seeding)

| Role | Email | Password |
|---|---|---|
| Admin | admin@demo-construction.example.com | AdminPass123! |
| Storekeeper | storekeeper@demo-construction.example.com | StorePass123! |
| Manager | manager@demo-construction.example.com | ManagerPass123! |

All fake data — no real people's National IDs or phone numbers.
