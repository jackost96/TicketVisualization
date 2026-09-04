# Ticket System

Prototype Jira-replacement app: projects, issues, custom workflows, permissions, issue linking,
comments, boards, dashboards, saved filters, and a Jira migration script — with a React web UI on
top. Python (FastAPI) + PostgreSQL backend, React + Vite + TypeScript frontend.

## Quick start: run everything with Docker

The whole stack — PostgreSQL, backend, frontend — runs from one `docker-compose.yml`. This is the
easiest way to get the app running and doesn't need Python, Node, or a local PostgreSQL install.

```bash
docker compose up --build
```

- Frontend: `http://localhost:3000`
- Backend API / docs: `http://localhost:8000/docs`
- PostgreSQL: exposed on host port **5433** (mapped from the container's 5432, to avoid clashing
  with a native Postgres install already using 5432 — see below)

The backend container runs `alembic upgrade head` and seeds reference data automatically on every
startup (idempotent, safe to re-run) before starting `uvicorn`. The frontend is a multi-stage
build: compiled to static files by Vite, then served by nginx, which also reverse-proxies `/api/*`
to the backend container — so the browser only ever talks to one origin and CORS never comes into
play in this setup.

Override the JWT secret by setting `JWT_SECRET` in a `.env` file at the repo root (docker compose
reads it automatically for variable substitution); otherwise it falls back to the same
`change-me-in-production` default as native dev.

To stop everything: `docker compose down` (add `-v` to also drop the `pgdata` volume and start
fresh next time).

This is a **production-style** build — no hot reload. For active development with instant reload
on save, use the native setup below instead (optionally still using the dockerized Postgres, see
step 2).

## Native dev setup (hot reload)

### Prerequisites

- Python 3.11+
- Node.js 18+ (for the frontend)
- PostgreSQL 14+ (either a local install, or via Docker — see step 2)

### Setup

1. **Create a virtualenv and install dependencies**

   ```bash
   python -m venv .venv
   .venv/Scripts/activate        # Windows
   # source .venv/bin/activate   # macOS/Linux
   pip install -e ".[dev]"
   ```

2. **Start PostgreSQL**

   Either via Docker (exposed on host port **5433**, not 5432, so it doesn't clash with a native
   install — use `postgresql+psycopg://ticketsystem:ticketsystem@localhost:5433/ticketsystem` in
   `.env` if you go this route):

   ```bash
   docker compose up -d db
   ```

   or point at a local PostgreSQL install on the standard 5432 port. Either way, create the app
   database and role:

   ```sql
   CREATE ROLE ticketsystem WITH LOGIN PASSWORD 'ticketsystem' CREATEDB;
   CREATE DATABASE ticketsystem OWNER ticketsystem;
   CREATE DATABASE ticketsystem_test OWNER ticketsystem;  -- used by the test suite
   ```

   (`docker-compose.yml` already creates `ticketsystem`/`ticketsystem` this way automatically —
   you only need the manual `CREATE DATABASE ticketsystem_test` extra for running tests, and only
   the full manual setup above if you're using a local install instead of Docker.)

3. **Configure environment**

   ```bash
   cp .env.example .env
   ```

   Defaults in `.env.example` already match the setup above
   (`postgresql+psycopg://ticketsystem:ticketsystem@localhost:5432/ticketsystem`). Adjust if your
   database, role, or password differ.

4. **Run migrations**

   ```bash
   alembic upgrade head
   ```

5. **Seed reference data**

   Statuses, the default workflow, system issue-link types, and the permission catalog. Safe to
   re-run — every insert is a get-or-create.

   ```bash
   python -m app.seeds.seed_defaults
   ```

6. **Run the API**

   ```bash
   uvicorn app.main:app --reload
   ```

   Interactive API docs at `http://localhost:8000/docs`.

## Frontend setup

The web UI lives in `frontend/` (React + Vite + TypeScript + Tailwind + shadcn/ui). It talks to
the backend over HTTP, so the two run as separate processes in development.

```bash
cd frontend
npm install
cp .env.example .env   # VITE_API_BASE_URL defaults to http://localhost:8000/api/v1
npm run dev
```

Open `http://localhost:5173`. The backend must already be running (see above) and its CORS
`cors_origins` setting (`app/core/config.py`) must include the frontend's origin — it defaults to
`http://localhost:5173`, matching Vite's default port.

Register an account from the login screen (`POST /users` is open — there's no invite flow in this
prototype), then sign in. Creating a project auto-creates its default Kanban board; your first
dashboard is created automatically the first time you visit Home.

`npm run build` produces a static production build in `frontend/dist/`; `npx tsc -b --noEmit`
type-checks the whole frontend without emitting.

## Running tests

Tests run against a real PostgreSQL database (`ticketsystem_test` by default — see step 2), not
SQLite, since the schema uses Postgres-specific features (arrays, JSONB, generated `tsvector`
columns).

```bash
pytest -v
```

Override the test database with `TEST_DATABASE_URL` if needed.

## Migrating data from Jira

```bash
python -m scripts.migrate_from_jira.run_migration --project ENG --project OPS
python -m scripts.migrate_from_jira.run_migration --dry-run   # extract + cache only, no DB writes
```

Requires `JIRA_BASE_URL`, `JIRA_EMAIL`, and `JIRA_API_TOKEN` set in `.env`, and
`python -m app.seeds.seed_defaults` to have already been run against the target database. See the
module docstring in `scripts/migrate_from_jira/run_migration.py` for the full load order and
known limitations (notably: workflow reconstruction is a degraded fallback — every migrated
project is assigned this app's single default workflow rather than a reconstruction of Jira's
real per-project workflow graph).

## Project structure

```
Dockerfile              backend image (multi-stage: pip install -> slim runtime, non-root user)
docker-entrypoint.sh    runs alembic upgrade + seed_defaults, then starts uvicorn
docker-compose.yml      db + backend + frontend, full stack
app/
  main.py              FastAPI app + router registration + CORS
  core/                config, security (JWT/password hashing), request dependencies
  db/                  SQLAlchemy engine/session setup
  models/              SQLAlchemy ORM models (one file per table group)
  schemas/             Pydantic request/response models
  api/routers/         auth, users, projects, issues, metadata, permissions, boards, dashboards,
                       saved_filters
  services/            business logic (issue CRUD, workflow state machine, permission checks,
                       board/dashboard services)
  seeds/               reference-data seeding
migrations/            Alembic migrations
scripts/migrate_from_jira/   Jira REST API -> Postgres ETL
tests/                 pytest suite (real Postgres, no mocking)
frontend/
  Dockerfile           multi-stage: vite build -> nginx (proxies /api to the backend container)
  nginx.conf           SPA fallback + /api reverse proxy
  src/api/             typed fetch client, one module per backend resource area
  src/auth/            AuthContext, ProtectedRoute, LoginPage
  src/components/      nav (app shell, dropdowns, global search), issues (shared table, create
                       dialog), board (Kanban view + drag-and-drop), dashboard (panels)
  src/pages/           one component per route (dashboards, projects, issues views, board, issue
                       detail)
  src/hooks/           useRecentlyViewed (localStorage), useDebouncedValue
```
