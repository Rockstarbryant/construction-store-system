# Construction Site Store & Tool Accountability System — Frontend

Next.js (App Router) + TypeScript + Tailwind CSS v4. Mobile-first UI built
for a storekeeper standing in a site store, phone in hand — bottom tab
navigation, large touch targets, and a flat concrete/steel/safety-amber
design language rather than a generic admin dashboard look.

## Stack

- Next.js 16 (App Router, Turbopack)
- TypeScript, strict mode
- Tailwind CSS v4 (CSS-first `@theme` config in `app/globals.css`)
- Self-hosted fonts via `@fontsource/*` (Space Grotesk, IBM Plex Sans, IBM
  Plex Mono) — no Google Fonts CDN dependency, works fully offline
- No external UI kit; small hand-rolled primitives in `components/ui.tsx`

## Project structure

```
frontend/
├── app/
│   ├── layout.tsx            # root layout: providers, fonts
│   ├── page.tsx               # redirects to /login or /dashboard
│   ├── login/page.tsx
│   └── (app)/                 # authenticated shell (top bar + bottom nav)
│       ├── layout.tsx
│       ├── dashboard/
│       ├── workers/           # list+search, new, [id] profile
│       ├── inventory/         # list, new, [id] detail
│       ├── transactions/      # issue flow, outstanding/
│       ├── reports/
│       ├── audit-logs/
│       ├── settings/
│       └── sites/             # list, new, [id]
├── components/
│   ├── ui.tsx                 # Button, Input, Select, StripedRow, etc.
│   ├── bottom-nav.tsx
│   └── top-bar.tsx
├── lib/
│   ├── api.ts                 # fetch wrapper, token refresh, error typing
│   ├── auth-context.tsx        # login/logout, current user, active site
│   ├── toast-context.tsx
│   ├── format.ts               # Africa/Nairobi display formatting
│   └── types.ts                 # mirrors backend Pydantic schemas
└── .env.example
```

## Local setup

Requires the backend running first (see `../backend/README.md`).

```bash
cd frontend
npm install
cp .env.example .env.local   # NEXT_PUBLIC_API_URL, defaults to http://localhost:8000
npm run dev
```

Open `http://localhost:3000`. Log in with a seeded demo account (see
`../backend/README.md` for credentials).

## Termux / Acode notes

Same general approach as the backend: write code in Acode, run commands in
Termux.

```bash
pkg install nodejs
cd frontend
npm install
cp .env.example .env.local
# point NEXT_PUBLIC_API_URL at your backend (e.g. your Render URL, or
# http://localhost:8000 if the backend is also running in Termux)
npm run dev
```

Then open `http://localhost:3000` in Chrome on the same phone. For a
closer-to-production check, `npm run build && npm run start` runs the
production server instead of the dev server.

## How auth works

- `lib/api.ts` stores the JWT access/refresh token pair in
  `localStorage` and attaches `Authorization: Bearer <token>` to every
  authenticated request.
- On a 401, it automatically tries `/auth/refresh` once before giving up
  and redirecting to `/login`.
- `lib/auth-context.tsx` wraps the app, exposing `user`, `sites`, and
  `activeSiteId` (persisted in `localStorage`, defaults to the first site
  the user has access to — most deployments only have one site).

## Design notes

- Colors and fonts are defined once in `app/globals.css` under `:root`
  and re-exposed to Tailwind via `@theme inline` — change a hex value
  there to re-theme the whole app.
- Status is always shown via a colored left-edge stripe
  (`components/ui.tsx::StripedRow`) plus text, not a badge/pill — amber
  for issued/out, moss green for returned/available, rust red for
  damaged/lost.
- All quantities, store numbers, and timestamps use `font-data` (IBM Plex
  Mono, tabular figures) so columns of numbers stay visually aligned when
  scanning a list quickly.
- Times are always converted to `Africa/Nairobi` for display
  (`lib/format.ts`) — the backend sends UTC ISO timestamps.

## Testing

This phase was verified with a real headless-browser walkthrough
(Playwright) against the actual running backend — login, worker search,
worker profile, issuing an item, the outstanding-items list, and
returning an item — not just a production build check. If you have
Playwright available:

```bash
pip install playwright && playwright install chromium
# then run a script that drives http://localhost:3000 the way a user would
```

No component/unit test suite is included yet (the spec calls this out as
optional/"where practical" for the frontend) — the highest-value coverage
for a UI this size was the end-to-end flow, which is what was actually run.

## Production build

```bash
npm run build
npm run start -- -p 3000
```

## Deployment (Vercel)

Import this `frontend/` directory as a Vercel project. Set
`NEXT_PUBLIC_API_URL` in Vercel's environment variables to your deployed
backend URL (e.g. the Render service URL), and set `CORS_ORIGINS` on the
backend to include your Vercel domain.
