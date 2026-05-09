# DataGov MVP

Localhost-first data governance platform scaffolded from the approved BRD, TSD, UI/UX brief, and development plan.

## Stack

- Frontend: Next.js 16, React, Tailwind CSS
- Backend: FastAPI, SQLAlchemy, Alembic
- Local databases: modular SQLite metadata repositories plus a separate sample source SQLite database
- Background jobs: Celery with Redis

## Phase 0 Scope

- Backend application shell with `GET /health`
- SQLite-ready modular SQLAlchemy database layer
- Initial ORM schema for users, connectors, assets, columns, DQ issues, policies, glossary, lineage, scans, and audit log
- Alembic migration wiring
- Frontend app shell with sidebar, topbar, dashboard placeholders, design tokens, React Query, and Zustand
- Root developer tooling and environment templates
- Standalone `kanban.html` tracker

## Phase 1 Scope

- Email/password login with JWT bearer authentication
- Admin, Editor, and Viewer RBAC dependency for protected API routes
- Users & Roles settings page with invite, role update, and deactivate actions
- Local SQLite connector framework with connection testing
- Asset catalogue API and UI with asset detail and column metadata
- Basic scan flow that discovers SQLite tables/views and writes catalogue metadata
- Four-step Run scan UI with source selection, configuration, running, and results states
- AI-assisted column metadata generation with a localhost fallback when no API key is configured
- Playwright E2E smoke test covering login, scan, catalogue, connectors, and users

## Phase 2.5 Architecture Hardening

- DataGov metadata is split into module databases for admin, catalogue, classification, quality, policy, glossary, and audit data.
- The default scanned source is `sample_business.db`, separate from DataGov's metadata databases.
- SQLite source connectors reject DataGov metadata database paths so internal system tables are not catalogued as business data.
- Connector scans support explicit catalogue scope selection. For localhost, the SQLite connector exposes schema `main` and its tables; DataGov stores only the selected schema/table metadata in `datagov_catalogue.db`.
- The development seed also creates attached SQLite dataset schemas `sales`, `hr`, and `finance` so connector scope selection can be tested like a multi-dataset warehouse.
- Cross-module relationships use UUID references and service-layer validation instead of cross-file SQLite foreign keys.

## Phase 4 Quality Gate

- SQLite performance indexes are created automatically for active catalogue, DQ issue, scan, glossary, and audit log queries.
- App shell includes skip-link navigation, active-page semantics, table captions, and error/not-found boundaries.
- Settings includes localhost email/Slack notification targets with test actions and audit-backed scan completion dispatch.
- Launch readiness notes live in `LAUNCH_READINESS.md`.

## Local Setup

```bash
# Backend
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
python -m app.scripts.seed_dev
uvicorn app.main:app --reload --port 8000
```

```bash
# Frontend
cd frontend
npm install
npm run dev
```

```bash
# One-command local startup from the repo root
make dev
```

Open:

- Frontend: http://localhost:3000
- Backend health: http://localhost:8000/health
- API docs: http://localhost:8000/docs
- Kanban tracker: `kanban.html`
- Launch checklist: `LAUNCH_READINESS.md`

## Verification

```bash
cd backend
.venv\Scripts\python.exe -m pytest tests -v
.venv\Scripts\python.exe -m ruff check app tests
```

```bash
cd frontend
npm run lint
npx tsc --noEmit
npm run build
npm run test:e2e
```

## Development Notes

- Modular SQLite files are the source of truth for localhost metadata during MVP development.
- `sample_business.db` is the local scanned source database; DataGov metadata databases are protected from scanning.
- Use the Run scan configure step to choose which connector schema tables should become active catalogue assets.
- Redis is used for Celery scan jobs and progress streaming, not as the primary data store.
- Keep SQLAlchemy models database-portable so PostgreSQL migration remains simple later.
- The default development admin created by the seed script is `admin@datagov.local` with password `admin123`.
- To use OpenAI for column metadata, set `OPENAI_API_KEY` and optionally `AI_METADATA_MODEL`; otherwise local fallback descriptions are generated.
