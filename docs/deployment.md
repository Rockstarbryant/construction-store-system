# Deployment

Target stack: **Vercel** (frontend, Phase 2) + **Render** (backend) +
**Neon** (Postgres). None of these are hard-coded into the app — everything
is environment-variable driven, so any equivalent host works too.

## 1. Database — Neon

1. Create a Neon project and a database (e.g. `construction_store`).
2. Copy the connection string. Neon gives you something like
   `postgresql://user:pass@ep-xxxx.region.aws.neon.tech/dbname?sslmode=require`.
   Change the scheme to `postgresql+psycopg://` for SQLAlchemy:
   `postgresql+psycopg://user:pass@ep-xxxx.region.aws.neon.tech/dbname?sslmode=require`
3. Run migrations once against this URL from your machine or CI:
   ```bash
   DATABASE_URL="postgresql+psycopg://...neon..." alembic upgrade head
   ```

## 2. Backend — Render

1. New Web Service → point at the `backend/` directory of this repo.
2. Build command: `pip install -r requirements.txt`
3. Start command:
   ```
   alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
4. Environment variables (set in Render's dashboard, never committed):
   - `DATABASE_URL` — the Neon connection string
   - `SECRET_KEY` — generate with `python -c "import secrets; print(secrets.token_urlsafe(64))"`
   - `CORS_ORIGINS` — JSON array containing your Vercel frontend URL, e.g.
     `["https://your-app.vercel.app"]`
   - `ENVIRONMENT=production`
   - `DEBUG=false`
5. After first deploy, hit `https://<your-render-service>.onrender.com/health`
   to confirm it's up, and `/api/v1/docs` for the interactive API docs.

## 3. Frontend — Vercel (Phase 2)

Once the Next.js frontend is built: import the `frontend/` directory as a
Vercel project, set `NEXT_PUBLIC_API_URL` to your Render backend URL as an
environment variable, and deploy.

## Rotating secrets

If `SECRET_KEY` is ever rotated, every existing access/refresh token
becomes invalid immediately (users are logged out) — there's no token
revocation list needed for that scenario.

## Zero-downtime migrations

Render restarts the service on deploy, running `alembic upgrade head`
before the new process starts serving traffic. For additive migrations
(new nullable columns, new tables) this is safe with no special handling.
For anything destructive (dropping/renaming a column in use), do it in two
deploys: (1) stop writing to the old column, (2) drop it in a later
migration once you've confirmed nothing reads it.
