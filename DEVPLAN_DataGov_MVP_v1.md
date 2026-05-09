# DataGov MVP — Comprehensive Development Plan

> **Stack:** Next.js 16 · FastAPI (Python) · modular SQLite (localhost dev) · SQLAlchemy · Celery + Redis · Tailwind CSS  
> **Environment:** Localhost development → production-ready structure  
> **Design system:** Clean Enterprise Light (Option B) — teal primary, Inter + JetBrains Mono  
> **Timeline:** 10 weeks · 2 full-stack engineers  
> **Reference documents:** BRD-DataGov-MVP-v1.0 · TSD-DataGov-MVP-v1.0 · UIUX-Brief-DataGov-MVP-v1.0

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Repository Structure](#2-repository-structure)
3. [Local Development Setup](#3-local-development-setup)
4. [Database Strategy — SQLite First](#4-database-strategy--sqlite-first)
5. [Phase 0 — Project Scaffold (Days 1–3)](#5-phase-0--project-scaffold-days-13)
6. [Phase 1 — Foundation (Week 1–3)](#6-phase-1--foundation-weeks-13)
7. [Phase 2 — Quality & Governance (Weeks 4–6)](#7-phase-2--quality--governance-weeks-46)
8. [Phase 3 — Glossary & Lineage (Weeks 7–8)](#8-phase-3--glossary--lineage-weeks-78)
9. [Phase 4 — Polish & Launch Readiness (Weeks 9–10)](#9-phase-4--polish--launch-readiness-weeks-910)
10. [API Contract Reference](#10-api-contract-reference)
11. [Component Library Checklist](#11-component-library-checklist)
12. [Testing Strategy](#12-testing-strategy)
13. [Environment Configuration](#13-environment-configuration)
14. [Migration Path — SQLite → PostgreSQL](#14-migration-path--sqlite--postgresql)
15. [Definition of Done](#15-definition-of-done)

---

## 1. Project Overview

### What we are building

DataGov MVP is a **web-based data governance platform** that gives data teams a single place to:

- **Discover** every data asset (table, view, schema) across connected sources at table and column level
- **Measure** data quality automatically using four metrics: completeness, uniqueness, consistency, accuracy
- **Govern** data with classification policies, PII/GDPR tagging, and an audit trail
- **Understand** data through a shared business glossary and table-level lineage

### Six core features (from BRD §3)

| # | Feature | BRD Section | Phase |
|---|---------|-------------|-------|
| 1 | Metadata Management & Data Catalogue | §3.1 | Phase 1 |
| 2 | Data Quality — Automated Metrics | §3.2 | Phase 2 |
| 3 | Data Governance & Policy Management | §3.3 | Phase 2 |
| 4 | Business Glossary | §3.4 | Phase 3 |
| 5 | Basic Data Lineage (table-level) | §3.5 | Phase 3 |
| 6 | User & Role Management | §3.6 | Phase 1 |
| + | Run Scan Flow (cross-cutting) | §3.7 | Phase 2 |

### Explicitly out of scope for MVP

- ML anomaly detection
- Column-level lineage
- Data contracts
- Claude Premium AI copilot
- Pipeline observability / ETL monitoring
- Data products & mesh architecture

---

## 2. Repository Structure

```
datagov/
├── backend/                        # FastAPI application
│   ├── app/
│   │   ├── main.py                 # FastAPI app entry point
│   │   ├── config.py               # Settings via pydantic-settings
│   │   ├── database.py             # SQLAlchemy engine + session (SQLite)
│   │   ├── models/                 # SQLAlchemy ORM models
│   │   │   ├── __init__.py
│   │   │   ├── asset.py
│   │   │   ├── column.py
│   │   │   ├── dq_issue.py
│   │   │   ├── policy.py
│   │   │   ├── glossary.py
│   │   │   ├── lineage.py
│   │   │   ├── scan.py
│   │   │   ├── audit_log.py
│   │   │   ├── user.py
│   │   │   └── connector.py
│   │   ├── schemas/                # Pydantic request/response schemas
│   │   │   ├── asset.py
│   │   │   ├── dq.py
│   │   │   ├── governance.py
│   │   │   ├── glossary.py
│   │   │   ├── lineage.py
│   │   │   ├── scan.py
│   │   │   └── user.py
│   │   ├── routers/                # API route handlers (one per module)
│   │   │   ├── catalogue.py        # /api/v1/assets, /api/v1/search
│   │   │   ├── quality.py          # /api/v1/dq, /api/v1/scans
│   │   │   ├── governance.py       # /api/v1/policies, /api/v1/audit-log
│   │   │   ├── glossary.py         # /api/v1/glossary
│   │   │   ├── lineage.py          # /api/v1/lineage
│   │   │   └── identity.py         # /api/v1/auth, /api/v1/users
│   │   ├── services/               # Business logic layer
│   │   │   ├── catalogue_service.py
│   │   │   ├── dq_engine.py        # DQ metric calculation
│   │   │   ├── scan_service.py     # Scan orchestration
│   │   │   ├── policy_engine.py    # Policy evaluation
│   │   │   ├── lineage_service.py
│   │   │   └── auth_service.py
│   │   ├── connectors/             # Data source connector framework
│   │   │   ├── base.py             # BaseConnector abstract class
│   │   │   ├── sqlite_connector.py # SQLite (for local dev testing)
│   │   │   ├── bigquery_connector.py
│   │   │   ├── snowflake_connector.py
│   │   │   ├── postgres_connector.py
│   │   │   └── dbt_connector.py
│   │   ├── workers/                # Celery background tasks
│   │   │   ├── celery_app.py
│   │   │   ├── scan_tasks.py
│   │   │   └── notification_tasks.py
│   │   ├── middleware/
│   │   │   ├── auth.py             # JWT validation middleware
│   │   │   └── audit.py            # Audit log middleware
│   │   └── utils/
│   │       ├── security.py         # Password hashing, JWT helpers
│   │       ├── patterns.py         # Consistency pattern regex map
│   │       └── pagination.py
│   ├── alembic/                    # Database migrations
│   │   ├── env.py
│   │   └── versions/
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_catalogue.py
│   │   ├── test_dq_engine.py
│   │   ├── test_governance.py
│   │   ├── test_auth.py
│   │   └── test_connectors.py
│   ├── alembic.ini
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── Makefile
│
├── frontend/                       # Next.js 14 application
│   ├── src/
│   │   ├── app/                    # App Router pages
│   │   │   ├── layout.tsx          # Root layout (sidebar + topbar)
│   │   │   ├── page.tsx            # Dashboard /
│   │   │   ├── login/
│   │   │   │   └── page.tsx
│   │   │   ├── scan/
│   │   │   │   └── page.tsx        # 4-step scan flow
│   │   │   ├── catalogue/
│   │   │   │   ├── page.tsx        # Asset list
│   │   │   │   └── [id]/
│   │   │   │       └── page.tsx    # Asset detail
│   │   │   ├── quality/
│   │   │   │   ├── page.tsx        # DQ scores overview
│   │   │   │   └── issues/
│   │   │   │       └── page.tsx
│   │   │   ├── governance/
│   │   │   │   ├── page.tsx        # Policies list
│   │   │   │   └── glossary/
│   │   │   │       └── page.tsx
│   │   │   ├── lineage/
│   │   │   │   └── page.tsx        # Lineage canvas
│   │   │   └── settings/
│   │   │       ├── connectors/
│   │   │       │   └── page.tsx
│   │   │       └── users/
│   │   │           └── page.tsx
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   ├── Topbar.tsx
│   │   │   │   └── Breadcrumb.tsx
│   │   │   ├── ui/                 # Design system primitives
│   │   │   │   ├── Button.tsx
│   │   │   │   ├── Badge.tsx       # Classification + status pills
│   │   │   │   ├── DQScoreRing.tsx
│   │   │   │   ├── MetricCard.tsx
│   │   │   │   ├── DataTable.tsx
│   │   │   │   ├── StatusDot.tsx
│   │   │   │   ├── SearchInput.tsx
│   │   │   │   ├── FilterBar.tsx
│   │   │   │   ├── Toast.tsx
│   │   │   │   ├── Modal.tsx
│   │   │   │   ├── ProgressBar.tsx
│   │   │   │   └── SkeletonRow.tsx
│   │   │   ├── catalogue/
│   │   │   │   ├── AssetTable.tsx
│   │   │   │   ├── AssetDetailHeader.tsx
│   │   │   │   ├── ColumnTable.tsx
│   │   │   │   └── SchemaHistoryTab.tsx
│   │   │   ├── quality/
│   │   │   │   ├── DQBreakdownPanel.tsx
│   │   │   │   ├── IssueRow.tsx
│   │   │   │   └── DQSparkline.tsx
│   │   │   ├── governance/
│   │   │   │   ├── PolicyRow.tsx
│   │   │   │   ├── PolicyRuleBuilder.tsx
│   │   │   │   └── ClassificationCoverage.tsx
│   │   │   ├── glossary/
│   │   │   │   ├── GlossaryTermCard.tsx
│   │   │   │   └── TermLinkPanel.tsx
│   │   │   ├── lineage/
│   │   │   │   ├── LineageCanvas.tsx
│   │   │   │   └── LineageMiniPanel.tsx
│   │   │   └── scan/
│   │   │       ├── ScanStepper.tsx
│   │   │       ├── SourceSelectStep.tsx
│   │   │       ├── ConfigureStep.tsx
│   │   │       ├── RunningStep.tsx
│   │   │       └── ResultsStep.tsx
│   │   ├── lib/
│   │   │   ├── api.ts              # Axios client with auth interceptor
│   │   │   ├── auth.ts             # Session helpers
│   │   │   └── utils.ts            # cn(), formatDate(), formatScore()
│   │   ├── hooks/
│   │   │   ├── useAssets.ts
│   │   │   ├── useDQScores.ts
│   │   │   ├── usePolicies.ts
│   │   │   ├── useScan.ts
│   │   │   └── useUser.ts
│   │   ├── store/
│   │   │   └── appStore.ts         # Zustand global store
│   │   └── styles/
│   │       ├── globals.css         # CSS variables (design tokens)
│   │       └── fonts.css
│   ├── public/
│   ├── tests/
│   │   ├── components/
│   │   └── e2e/                    # Playwright specs
│   ├── next.config.js
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── package.json
│
├── .env.example                    # All env vars documented
├── .env.local                      # Local dev values (gitignored)
├── docker-compose.yml              # Redis for Celery (SQLite needs no container)
├── Makefile                        # Top-level dev commands
└── README.md
```

---

## 3. Local Development Setup

### Prerequisites

```bash
# Required
node >= 20.x
python >= 3.12
pip
redis-server   # for Celery task queue (brew install redis / apt install redis)

# Optional but recommended
pyenv          # Python version management
nvm            # Node version management
```

### First-time setup

```bash
# 1. Clone and enter project
git clone https://github.com/your-org/datagov.git
cd datagov

# 2. Backend setup
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 3. Create local env file
cp ../.env.example ../.env.local

# 4. Seed local module databases and sample source data
alembic upgrade head
python -m app.scripts.seed_dev

# 5. Seed initial admin user
python -m app.scripts.seed_dev

# 6. Start backend (terminal 1)
uvicorn app.main:app --reload --port 8000

# 7. Start Celery worker (terminal 2) — needed for scans
redis-server &
celery -A app.workers.celery_app worker --loglevel=info

# 8. Frontend setup (terminal 3)
cd ../frontend
npm install
npm run dev    # starts on http://localhost:3000

# 9. Visit the app
open http://localhost:3000
# Login: admin@datagov.local / password: admin123
```

### Daily development commands

```bash
# From project root Makefile
make dev          # Start all services (backend + frontend + celery)
make test         # Run all tests (backend pytest + frontend vitest)
make migrate      # Run pending Alembic migrations
make seed         # Re-seed development data
make lint         # ESLint + ruff (Python)
make format       # Prettier + black
```

---

## 4. Database Strategy — SQLite First

### Phase 2.5 update — modular metadata repositories

DataGov now uses separate SQLite database files for its own metadata and a separate SQLite file for scanned demo/source data. This prevents the system from cataloguing its own internal tables as business assets.

Local module databases:

- `datagov_admin.db` — users, connectors, scans, auth/admin state
- `datagov_catalogue.db` — assets, columns, table-level lineage references
- `datagov_classification.db` — classification labels and classification assignments
- `datagov_quality.db` — DQ issues and quality state
- `datagov_policy.db` — policy definitions
- `datagov_glossary.db` — glossary terms and term links
- `datagov_audit.db` — audit log events
- `sample_business.db` — scanned localhost source data only

Cross-module relationships use UUID references and service-layer validation. SQLite cross-file foreign keys are intentionally avoided. Connector creation, connector testing, and scans must reject DataGov metadata DB paths.

### Phase 2.5 update — scoped connector catalogue ingestion

DataGov's catalogue remains an internal metadata repository. Source systems such as SQLite today and BigQuery later are treated as connectors that expose available schema/dataset and table choices. A scan writes only the selected connector scope into `datagov_catalogue.db`.

For localhost development:

- SQLite exposes schema `main` with selectable tables and views.
- The dev seed also attaches `sales`, `hr`, and `finance` SQLite database files to simulate multiple warehouse datasets/schemas from one connector.
- `GET /api/v1/connectors/:id/schemas` discovers available schema/table scope from the source connector.
- `PATCH /api/v1/connectors/:id/scope` stores the selected catalogue scope on the connector for future scans and schedules.
- `POST /api/v1/scans` accepts `connector_scopes` so a run can catalogue only selected schema tables.
- Assets from the same connector that are outside the selected scope are marked deleted in the DataGov catalogue, not removed from the source database.

### Why SQLite for localhost

SQLite requires zero configuration, no running database server, and produces a single portable `.db` file. For a localhost development environment with one developer at a time, it is the ideal choice. The SQLAlchemy ORM abstracts the database entirely — swapping to PostgreSQL for production requires only a connection string change.

### SQLite configuration (`backend/app/database.py`)

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings

# Modular SQLite for local dev; PostgreSQL modules for production
# Set ADMIN_DATABASE_URL, CATALOGUE_DATABASE_URL, QUALITY_DATABASE_URL, etc. in .env.local
engines = {
    "admin": create_engine(settings.admin_database_url, connect_args={"check_same_thread": False}),
    "catalogue": create_engine(settings.catalogue_database_url, connect_args={"check_same_thread": False}),
    "quality": create_engine(settings.quality_database_url, connect_args={"check_same_thread": False}),
}

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Environment config (`backend/app/config.py`)

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Modular SQLite metadata repositories for local development
    admin_database_url: str = "sqlite:///./datagov_admin.db"
    catalogue_database_url: str = "sqlite:///./datagov_catalogue.db"
    classification_database_url: str = "sqlite:///./datagov_classification.db"
    quality_database_url: str = "sqlite:///./datagov_quality.db"
    policy_database_url: str = "sqlite:///./datagov_policy.db"
    glossary_database_url: str = "sqlite:///./datagov_glossary.db"
    audit_database_url: str = "sqlite:///./datagov_audit.db"
    sample_source_path: str = "sample_business.db"

    # Auth
    secret_key: str = "dev-secret-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480  # 8 hours

    # Redis / Celery
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    # App
    debug: bool = True
    cors_origins: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env.local"

settings = Settings()
```

### SQLite-specific notes for development

- **No connection pool needed** — SQLite handles single-file access; `check_same_thread=False` allows FastAPI's async threads
- **WAL mode** — enable Write-Ahead Logging for better concurrent read performance: `PRAGMA journal_mode=WAL;` (run once after DB creation)
- **Audit log append-only** — enforced via application logic (no DELETE route), not DB trigger (SQLite triggers are limited)
- **UUID columns** — stored as `VARCHAR(36)` in SQLite; use `uuid.uuid4()` in Python, not `gen_random_uuid()` (PostgreSQL-specific)
- **JSONB columns** — stored as `TEXT` + `JSON()` type in SQLAlchemy; works identically in SQLite

### SQLite dev database file

```
backend/
├── datagov_admin.db
├── datagov_catalogue.db
├── datagov_classification.db
├── datagov_quality.db
├── datagov_policy.db
├── datagov_glossary.db
├── datagov_audit.db
└── sample_business.db  # scanned source DB, not a DataGov metadata DB
```

---

## 5. Phase 0 — Project Scaffold (Days 1–3)

> Goal: Both engineers have a running hello-world on localhost with the correct project structure before writing any feature code.

### Day 1 — Backend scaffold

**Tasks:**
- [ ] Create `backend/` directory with the structure in §2
- [ ] Set up Python virtual environment and `requirements.txt`
- [ ] Implement `config.py`, `database.py`, `models/__init__.py`
- [ ] Write all 10 SQLAlchemy models (empty, schema only — no logic yet)
- [ ] Configure Alembic: `alembic init alembic`, write `env.py` to use `Base.metadata`
- [ ] Run `alembic revision --autogenerate -m "initial schema"` and `alembic upgrade head`
- [ ] Verify modular DataGov DB files are created and `sample_business.db` is the only default scanned source
- [ ] Write `main.py` with health check endpoint: `GET /health → { status: ok }`
- [ ] Configure CORS for `http://localhost:3000`

**SQLAlchemy model skeletons to create:**

```python
# Example: backend/app/models/asset.py
from sqlalchemy import Column, String, Text, Float, BigInteger, DateTime, JSON, Boolean
from sqlalchemy.orm import relationship
from app.database import Base
import uuid
from datetime import datetime, timezone

class Asset(Base):
    __tablename__ = "assets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    connector_id = Column(String(36), nullable=True)
    external_id = Column(String(512), nullable=False, index=True)
    asset_type = Column(String(32), nullable=False, index=True)  # table, view, schema
    name = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(String(36), nullable=True)
    dq_score = Column(Float, nullable=True)
    schema_hash = Column(String(64), nullable=True)
    row_count = Column(BigInteger, nullable=True)
    tags = Column(JSON, default=list)
    classifications = Column(JSON, default=list)
    last_scanned_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    columns = relationship("AssetColumn", back_populates="asset", cascade="all, delete-orphan")
```

**Deliverable:** `GET http://localhost:8000/health` returns `{"status": "ok"}` and `GET http://localhost:8000/docs` shows Swagger UI.

---

### Day 2 — Frontend scaffold

**Tasks:**
- [ ] `npx create-next-app@latest frontend --typescript --tailwind --app --no-src-dir` (adjust to use `src/`)
- [ ] Install dependencies:

```bash
npm install axios zustand @tanstack/react-query react-hook-form zod
npm install lucide-react @tanstack/react-table reactflow recharts
npm install -D vitest @testing-library/react playwright
```

- [ ] Configure `tailwind.config.js` with Inter and JetBrains Mono fonts
- [ ] Create `src/styles/globals.css` with all CSS design tokens from UIUX Brief §9:

```css
/* src/styles/globals.css */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
  --color-brand: #0F766E;
  --color-brand-light: #CCFBF1;
  --color-brand-surface: #F0FDFA;

  --color-success-text: #166534;
  --color-success-bg: #F0FDF4;
  --color-success-border: #BBF7D0;

  --color-warning-text: #92400E;
  --color-warning-bg: #FFFBEB;
  --color-warning-border: #FDE68A;

  --color-danger-text: #991B1B;
  --color-danger-bg: #FEF2F2;
  --color-danger-border: #FECACA;

  --color-page-bg: #F8FAFC;
  --color-sidebar-bg: #FFFFFF;
  --color-card-bg: #FFFFFF;
  --color-surface: #F8FAFC;
  --color-border: #E2E8F0;
  --color-border-strong: #CBD5E1;

  --color-text-primary: #0F172A;
  --color-text-secondary: #475569;
  --color-text-muted: #94A3B8;

  --font-ui: 'Inter', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', ui-monospace, monospace;

  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 10px;
  --sidebar-width: 220px;
  --topbar-height: 48px;
}

body {
  font-family: var(--font-ui);
  background-color: var(--color-page-bg);
  color: var(--color-text-primary);
}
```

- [ ] Create `src/app/layout.tsx` with the app shell (sidebar + topbar placeholders)
- [ ] Create `src/lib/api.ts` Axios client pointing to `http://localhost:8000`
- [ ] Add `QueryClientProvider` and `Zustand` store wrappers to `layout.tsx`

**Deliverable:** `http://localhost:3000` renders the app shell with sidebar, topbar, and "Hello DataGov" in the content area.

---

### Day 3 — Integration + shared tooling

**Tasks:**
- [ ] Confirm frontend can reach `GET http://localhost:8000/health` (test CORS)
- [ ] Set up `Makefile` at root with `make dev`, `make test`, `make migrate`
- [ ] Configure `docker-compose.yml` for Redis only (SQLite needs no container):

```yaml
# docker-compose.yml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

- [ ] Set up `backend/Makefile`:

```makefile
dev:
    uvicorn app.main:app --reload --port 8000

worker:
    celery -A app.workers.celery_app worker --loglevel=info

migrate:
    alembic upgrade head

seed:
    python -m app.scripts.seed_dev

test:
    pytest tests/ -v --cov=app --cov-report=term-missing

lint:
    ruff check app/
    ruff format --check app/

format:
    ruff format app/
    black app/
```

- [ ] Write `backend/app/scripts/seed_dev.py` to create default admin user:

```python
# Creates: admin@datagov.local / admin123
# Creates: editor@datagov.local / editor123
# Creates: viewer@datagov.local / viewer123
```

- [ ] Create `.env.example` with all required variables documented
- [ ] Add `datagov*.db`, `sample_business.db`, `.env.local`, `__pycache__/`, `.next/`, `node_modules/` to `.gitignore`

**Deliverable:** `make dev` starts all three processes. `make test` runs with 0 failures (empty test suite passes).

---

## 6. Phase 1 — Foundation (Weeks 1–3)

> **BRD coverage:** Feature 6 (Users & Roles), Feature 1 start (Catalogue — scan + discovery), Connector framework  
> **Goal:** A working app where an admin can log in, add a connector, run a scan, and see discovered assets in the catalogue.

---

### Week 1 — Authentication & User Management

**BRD requirements:** USR-001, USR-002, USR-003, USR-004, USR-005

#### Backend tasks

- [ ] **User model** (`models/user.py`): id, email, hashed_password, full_name, role (admin/editor/viewer), is_active, created_at
- [ ] **Auth service** (`services/auth_service.py`):
  - `hash_password(password)` → bcrypt hash (cost factor 12)
  - `verify_password(plain, hashed)` → bool
  - `create_access_token(user_id, role)` → JWT (HS256, 8-hour expiry)
  - `decode_token(token)` → user_id + role
- [ ] **RBAC dependency** (`middleware/auth.py`):
  ```python
  def require_role(*roles):
      # FastAPI dependency — inject into any route
      # Raises 403 if current user role not in roles
  ```
- [ ] **Identity router** (`routers/identity.py`):
  - `POST /api/v1/auth/login` — email + password → access_token
  - `POST /api/v1/auth/refresh` — refresh_token → new access_token
  - `POST /api/v1/auth/logout`
  - `GET /api/v1/users` — admin only
  - `POST /api/v1/users/invite` — admin only; creates inactive user + sends invite email
  - `PATCH /api/v1/users/:id` — admin only; change role or deactivate
  - `GET /api/v1/users/me` — current user profile
- [ ] **Session expiry** (USR-004): JWT `exp` claim set to 8 hours; no refresh grants new tokens after 8h idle

#### Frontend tasks

- [ ] **Login page** (`app/login/page.tsx`):
  - Email + password form (React Hook Form + Zod validation)
  - "Sign in with Google" button (placeholder for Phase 4)
  - Error state: "Invalid credentials" below form
  - Redirect to `/` on success
- [ ] **Auth store** (`store/appStore.ts`): Zustand slice holding `user`, `token`, `setUser`, `logout`
- [ ] **API interceptor** (`lib/api.ts`): inject Bearer token on all requests; redirect to `/login` on 401
- [ ] **Sidebar footer** (USR-005): avatar circle (initials), name, role label
- [ ] **Settings / Users page** (`app/settings/users/page.tsx`):
  - Table: name, email, role badge, status dot, last active
  - "Invite user" button → modal (email + role select)
  - Role change dropdown per row (admin only)
  - Deactivate toggle (admin only)

#### Tests

```python
# backend/tests/test_auth.py
def test_login_success(client, seed_admin):
    response = client.post("/api/v1/auth/login", json={"email": "admin@datagov.local", "password": "admin123"})
    assert response.status_code == 200
    assert "access_token" in response.json()["data"]

def test_login_wrong_password(client):
    response = client.post("/api/v1/auth/login", json={"email": "admin@datagov.local", "password": "wrong"})
    assert response.status_code == 401

def test_viewer_cannot_invite(client, viewer_token):
    response = client.post("/api/v1/users/invite",
                           json={"email": "new@test.com", "role": "editor"},
                           headers={"Authorization": f"Bearer {viewer_token}"})
    assert response.status_code == 403
```

**Milestone check:** Admin logs in → sees dashboard skeleton → can navigate to Settings → Users.

---

### Week 2 — Connector Framework & Asset Discovery

**BRD requirements:** CAT-001, CAT-002, CAT-003 (schema only)

#### Backend tasks

- [ ] **Connector model** (`models/connector.py`): id, name, connector_type, config_encrypted (JSON), status, last_tested_at
- [ ] **BaseConnector** (`connectors/base.py`):

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterator
from datetime import datetime

@dataclass
class AssetMetadata:
    external_id: str
    name: str
    asset_type: str  # table, view
    schema_name: str
    description: str | None = None
    row_count: int | None = None

@dataclass
class ColumnMetadata:
    column_name: str
    data_type: str
    is_nullable: bool
    ordinal_position: int
    description: str | None = None

@dataclass
class LineageEdge:
    source_external_id: str
    target_external_id: str
    edge_type: str
    sql_fragment: str | None = None

class BaseConnector(ABC):
    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    def connect(self) -> None: ...

    @abstractmethod
    def test_connection(self) -> dict: ...

    @abstractmethod
    def list_assets(self, since: datetime | None = None) -> Iterator[AssetMetadata]: ...

    @abstractmethod
    def get_schema(self, asset_id: str) -> list[ColumnMetadata]: ...

    def get_sample_rows(self, asset_id: str, limit: int = 10) -> list[dict]:
        return []  # Optional — override in connectors that support it

    def extract_lineage(self, since: datetime | None = None) -> Iterator[LineageEdge]:
        return iter([])  # Optional — override in connectors with query log access
```

- [ ] **SQLite connector** (`connectors/sqlite_connector.py`) — for local dev testing against `sample_business.db` or another source SQLite file; DataGov metadata DB files must be blocked from scanning
- [ ] **PostgreSQL connector** (`connectors/postgres_connector.py`) — using `psycopg2`
- [ ] **Catalogue service** (`services/catalogue_service.py`):
  - `run_discovery(connector, db_session)` → upsert assets and columns
  - `compute_schema_hash(columns)` → detect schema changes
  - `upsert_asset(metadata, db)` → create or update asset record
- [ ] **Catalogue router** (`routers/catalogue.py`):
  - `GET /api/v1/assets` — paginated list with filters (q, type, source, dq_min, dq_max)
  - `GET /api/v1/assets/:id` — full asset detail
  - `PATCH /api/v1/assets/:id` — update description, owner, tags (editor+)
  - `GET /api/v1/assets/:id/columns` — paginated column list
  - `GET /api/v1/search?q=` — full-text search across name + description
- [ ] **Connector router** (`routers/connectors.py`):
  - `GET /api/v1/connectors`
  - `POST /api/v1/connectors` — create + encrypt credentials
  - `POST /api/v1/connectors/:id/test` — test connection + return status
  - `DELETE /api/v1/connectors/:id`

#### Frontend tasks

- [ ] **Connectors settings page** (`app/settings/connectors/page.tsx`):
  - List of configured connectors with status dots
  - "Add connector" button → modal (connector type select + credentials form)
  - "Test connection" button per connector row
- [ ] **Catalogue page** (`app/catalogue/page.tsx`):
  - Full-width table with: asset name + source path (mono), classification pills, DQ score ring (null state), owner chip, last updated
  - Search bar, filter sidebar stub (hooked up in Phase 2)
  - Skeleton rows while loading
- [ ] **Asset detail page** (`app/catalogue/[id]/page.tsx`):
  - Header: asset name, source badge, type badge, DQ ring (null state)
  - Tabs: Overview | Columns | Lineage | History
  - Overview tab: description (editable inline for editor+), owner, tags, last scanned
  - Columns tab: table with name (mono), type (mono), nullable badge

**Milestone check:** Add SQLite connector pointing at a test `.db` file → run `POST /api/v1/connectors/:id/test` → gets success → catalogue page shows discovered assets.

---

### Week 3 — Scan Engine (Basic) & Scan Flow UI

**BRD requirements:** SCN-001, SCN-002, SCN-003, SCN-004, SCN-005

#### Backend tasks

- [ ] **Scan model** (`models/scan.py`): id, connector_ids (JSON), scan_type, status, started_at, finished_at, assets_scanned, errors (JSON)
- [ ] **Scan stages model** / in-memory progress tracking via Redis pub/sub
- [ ] **Celery app** (`workers/celery_app.py`):

```python
from celery import Celery
from app.config import settings

celery_app = Celery(
    "datagov",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)
celery_app.config_from_object("app.workers.celery_config")
```

- [ ] **Scan task** (`workers/scan_tasks.py`):

```python
@celery_app.task(bind=True)
def run_scan(self, scan_id: str, config: dict):
    # Stage 1: Connect
    # Stage 2: Discover assets & schema
    # Stage 3: Calculate DQ (Phase 2 — stub for now)
    # Stage 4: Apply policies (Phase 2 — stub for now)
    # Stage 5: Extract lineage (Phase 3 — stub for now)
    # Publish progress to Redis channel f"scan:{scan_id}"
```

- [ ] **Scan router** (`routers/quality.py`):
  - `POST /api/v1/scans` → enqueue Celery task → return `{ scan_id, status: queued }`
  - `GET /api/v1/scans/:id` → return scan record with stages
  - `GET /api/v1/scans/:id/log` → cursor-paginated log lines from Redis
- [ ] **Server-Sent Events endpoint** for live scan progress:
  ```
  GET /api/v1/scans/:id/stream → SSE stream of stage progress events
  ```

#### Frontend tasks

- [ ] **Scan flow** (`app/scan/page.tsx`) — full 4-step stepper as designed in the run scan mockup:
  - **Step 1 — Source select:** connector cards, toggle select, count badge
  - **Step 2 — Configure:** scan type radio, asset scope table, DQ metric toggles
  - **Step 3 — Running:** SSE-driven live progress bars (5 stages), live log stream in mono font, cancel button
  - **Step 4 — Results:** summary stat cards, DQ score change table, findings list
- [ ] **Stepper component** (`components/scan/ScanStepper.tsx`): completed steps show teal check, active step shows teal ring, pending steps gray
- [ ] **RunningStep** (`components/scan/RunningStep.tsx`): connects to SSE stream via `EventSource`, appends log lines, animates progress bars
- [ ] **"Run scan" button** on dashboard topbar → navigates to `/scan`

**Milestone check:** Dashboard → Run scan → select SQLite connector → Full scan → watch live progress → see results with discovered assets listed.

---

## 7. Phase 2 — Quality & Governance (Weeks 4–6)

> **BRD coverage:** Feature 2 (DQ engine), Feature 3 (Governance + Policies), Scan flow fully wired  
> **Goal:** Running a scan calculates real DQ scores, applies policies, and raises issues automatically.

---

### Week 4 — Data Quality Engine

**BRD requirements:** DQ-001, DQ-002, DQ-003, DQ-004, DQ-005, DQ-006, DQ-008

#### Backend tasks

- [ ] **DQ engine** (`services/dq_engine.py`):

```python
class DQEngine:
    """Calculates the four DQ metrics for every column in an asset."""

    def calculate_completeness(self, conn, table: str, column: str) -> float:
        """COUNT(col) * 100.0 / COUNT(*) — ratio of non-null values."""

    def calculate_uniqueness(self, conn, table: str, column: str) -> float:
        """COUNT(DISTINCT col) * 100.0 / COUNT(*) — ratio of distinct values."""

    def calculate_consistency(self, conn, table: str, column: str, pattern: str) -> float:
        """Percentage of values matching the pattern regex."""

    def calculate_accuracy(self, conn, table: str, column: str, rule: dict) -> float:
        """Percentage of values passing the accuracy rule (range, enum, regex)."""

    def infer_pattern(self, column_name: str, data_type: str) -> str | None:
        """Map column name to regex pattern using the pattern detection table (TSD §5.2)."""

    def compute_asset_dq_score(self, column_scores: list[dict]) -> float:
        """Weighted average: completeness*0.3 + uniqueness*0.25 + consistency*0.25 + accuracy*0.2"""
```

- [ ] **Pattern detection map** (`utils/patterns.py`) — exact mappings from TSD §5.2:
  - `email` → email regex
  - `phone`, `mobile`, `tel` → phone regex
  - `uuid` → UUID v4 regex
  - `_at`, `_on`, `date` → ISO 8601 date regex
  - `url`, `link`, `href` → URL regex
  - `zip`, `postcode` → postcode regex

- [ ] **Issue detection** (`services/dq_engine.py`):
  - Compare new scores to previous scan scores per column
  - Raise `DQIssue` if delta >= 10 percentage points
  - Severity logic from TSD §5.3:
    - Critical: delta >= 25 OR completeness < 50%
    - Medium: delta 10–24 OR metric < 70%
    - Low: delta exactly 10

- [ ] **Wire DQ into scan task** (`workers/scan_tasks.py`) — Stage 3 now calls `DQEngine` for every column in every scanned asset

- [ ] **DQ router** (`routers/quality.py`):
  - `GET /api/v1/dq/scores` — all assets sorted by score
  - `GET /api/v1/dq/scores/:asset_id` — asset DQ detail with per-column breakdown
  - `GET /api/v1/dq/issues` — open issues with filters
  - `PATCH /api/v1/dq/issues/:id` — resolve issue with note

#### Frontend tasks

- [ ] **DQ score ring** (`components/ui/DQScoreRing.tsx`) — 32px circle, color-coded: ≥80 green, 60–79 amber, <60 red
- [ ] **DQ breakdown panel** (`components/quality/DQBreakdownPanel.tsx`) — 4 horizontal bars with metric name, score, color-coded fill
- [ ] **Dashboard DQ metric card** — overall score with bar + delta badge
- [ ] **Quality / DQ scores page** (`app/quality/page.tsx`) — all assets table ranked by score, metric breakdown columns
- [ ] **Quality / Issues page** (`app/quality/issues/page.tsx`) — issues table with severity badge, asset name, metric, delta, age, resolve button
- [ ] **Column table DQ columns** (`components/catalogue/ColumnTable.tsx`) — add 4 DQ metric score columns + warning indicator (amber/red dot) for scores below threshold
- [ ] **Resolve issue modal** — input for resolution note + confirm button

---

### Week 5 — Governance Policy Engine

**BRD requirements:** GOV-001, GOV-002, GOV-003, GOV-004, GOV-005, GOV-006, GOV-007

#### Backend tasks

- [ ] **Policy engine** (`services/policy_engine.py`):

```python
class PolicyEngine:
    """Evaluates all active policies against all assets and columns."""

    def evaluate_all(self, db_session, scan_id: str):
        """Run after discovery + DQ. Apply matching policies."""

    def evaluate_policy(self, policy: Policy, assets: list[Asset], columns: list[Column]):
        """For each rule in policy, find matching assets/columns and apply action."""

    def apply_tag(self, target, tag: str, source: str = "policy"):
        """Add tag to asset or column tags JSON field."""

    def apply_classification(self, target, label: str):
        """Add classification label to classifications JSON field."""

    def _matches_rule(self, rule: dict, target) -> bool:
        """
        rule = { field: "column_name", operator: "contains", value: "email", action: "tag:PII" }
        Supported operators: contains, equals, starts_with, ends_with, regex_match
        """
```

- [ ] **Built-in classification labels**: PII, GDPR, Finance, Internal, Public, Sensitive, Restricted — seeded in DB on `alembic upgrade head`
- [ ] **Masking middleware**: for Viewer role, replace classified column sample values with `[MASKED]` in API responses
- [ ] **Audit log middleware** (`middleware/audit.py`): FastAPI middleware that captures POST/PATCH/DELETE operations and writes to `audit_log` table
- [ ] **Policy router** (`routers/governance.py`):
  - `GET /api/v1/policies`
  - `POST /api/v1/policies` — editor+
  - `PATCH /api/v1/policies/:id` — editor+
  - `DELETE /api/v1/policies/:id` — admin
  - `GET /api/v1/audit-log` — admin only
- [ ] **Wire policy engine into scan** — Stage 4 in scan task calls `PolicyEngine.evaluate_all()`

#### Frontend tasks

- [ ] **Governance / Policies page** (`app/governance/page.tsx`):
  - Policy list table: name, type badge, status dot, asset count, created by, last run
  - "Create policy" button → opens policy builder modal
- [ ] **Policy rule builder** (`components/governance/PolicyRuleBuilder.tsx`):
  - Visual rule rows: [field dropdown] [operator dropdown] [value input] → [action/tag select]
  - "Add rule" button adds a new row
  - Preview of affected assets (live count query)
  - Save → activate immediately or save as draft
- [ ] **Classification coverage panel** (`components/governance/ClassificationCoverage.tsx`) — on dashboard: 4 colored stat cards (PII count, GDPR count, unclassified, fully governed)
- [ ] **Classification pills on asset detail** — teal/blue/red/amber pills per UIUX Brief §5.3 color rules
- [ ] **Column table masking** — Viewer role sees `[MASKED]` in sample data columns tagged PII

---

### Week 6 — Scan Flow Completion & DQ Integration

**BRD requirements:** SCN-004, SCN-005, DQ-007, DQ-009, DQ-010

#### Tasks

- [ ] **Scan results page fully wired**: DQ score changes pull real before/after scores from DB; findings list shows real issues
- [ ] **DQ trend sparkline** (DQ-007): `recharts` `<LineChart>` component showing metric values across last 10 scans; rendered on asset detail page Columns tab
- [ ] **Issue auto-detection** in scan: after DQ stage completes, compare to previous scan and write issues to DB
- [ ] **Issues count badge** on sidebar nav: live count of open issues, red background when > 0
- [ ] **Dashboard recent activity feed**: pull real events from audit log — policy applied, asset discovered, issue raised
- [ ] **Filter bar on catalogue** (`components/ui/FilterBar.tsx`): source, type, classification, DQ range sliders, owner — all wired to API query params
- [ ] **Scan scheduling stub** (SCN-006 — should have): add `schedule_cron` field to scan config form; store in DB; Celery Beat integration commented with `# TODO: enable Celery Beat for scheduled scans`

**Milestone check:** Full scan → DQ scores calculated → policies applied → classifications tagged → issues raised → dashboard shows real data everywhere.

---

## 8. Phase 3 — Glossary & Lineage (Weeks 7–8)

> **BRD coverage:** Feature 4 (Business Glossary), Feature 5 (Table-Level Lineage)  
> **Goal:** Governance managers can build a glossary; engineers can trace data flow.

---

### Week 7 — Business Glossary

**BRD requirements:** GLO-001, GLO-002, GLO-003, GLO-004, GLO-005

#### Backend tasks

- [ ] **Glossary service** (`services/glossary_service.py`):
  - `suggest_links(asset_id, db)` — compare column names to glossary term names and synonyms; return top matches with confidence score
- [ ] **Glossary router** (`routers/glossary.py`):
  - `GET /api/v1/glossary` — paginated list, supports `?q=` search
  - `GET /api/v1/glossary/:id` — full term detail with linked assets
  - `POST /api/v1/glossary` — editor+
  - `PATCH /api/v1/glossary/:id` — editor+
  - `DELETE /api/v1/glossary/:id` — admin
  - `POST /api/v1/glossary/:id/links` — link term to asset or column
  - `DELETE /api/v1/glossary/:id/links/:link_id`
  - `GET /api/v1/assets/:id/glossary-suggestions` — auto-suggestions for an asset

#### Frontend tasks

- [ ] **Governance / Glossary page** (`app/governance/glossary/page.tsx`):
  - Grid of term cards (not a table per UIUX Brief §6.6): term name, truncated definition, status badge, linked asset count
  - Search bar with real-time filter (debounced 300ms)
  - "New term" button → modal form
- [ ] **Term detail modal** (expand on click): full definition, synonyms list, related terms, steward avatar + name, linked assets list
- [ ] **Term form modal**: term name (required), definition (textarea), synonyms (tag-input: type + Enter), status select, steward select, link assets (async search input)
- [ ] **Glossary term badge on asset detail**: if the asset or its columns are linked to glossary terms, show a "Glossary" section with term pills on the Overview tab
- [ ] **Auto-suggestions panel**: on asset detail Overview tab, after scan, show "Suggested glossary links" with Accept/Dismiss per suggestion
- [ ] **Glossary search in catalogue**: global search bar also returns glossary terms (marked with a different icon)

---

### Week 8 — Data Lineage

**BRD requirements:** LIN-001, LIN-002, LIN-003, LIN-004, LIN-005

#### Backend tasks

- [ ] **Lineage extraction** in scan Stage 5 (`workers/scan_tasks.py`):
  - Call `connector.extract_lineage()` for each connector
  - Upsert `lineage_edges` records: source_asset_id → target_asset_id
  - dbt connector: parse `manifest.json` nodes for model dependencies
- [ ] **Lineage service** (`services/lineage_service.py`):

```python
def get_lineage_graph(asset_id: str, depth: int = 3, direction: str = "both", db) -> dict:
    """
    Traverse lineage_edges table up to `depth` hops.
    Returns { nodes: [{ id, name, asset_type, dq_score, source }],
              edges: [{ source, target, edge_type }] }
    Uses recursive CTE in SQLAlchemy for multi-hop traversal.
    """

def get_mini_lineage(asset_id: str, db) -> dict:
    """1-hop upstream + downstream only — for asset detail panel."""
```

- [ ] **Lineage router** (`routers/lineage.py`):
  - `GET /api/v1/lineage/:asset_id?depth=3&direction=both` — full graph data
  - `GET /api/v1/lineage/:asset_id/mini` — 1-hop for asset detail panel
  - `POST /api/v1/lineage/refresh` — trigger manual lineage re-extraction (editor+)

#### Frontend tasks

- [ ] **Lineage canvas** (`app/lineage/page.tsx`) using React Flow:
  - Custom `AssetNode` component: rounded rect 140×44px, teal fill for selected, gray for others, asset name (13px/500) + source badge (11px mono)
  - Edges: 1.5px arrows, `#94A3B8` color
  - Controls: zoom in/out, fit to screen (React Flow built-ins), search input to focus on an asset
  - Node click → show right-side detail panel: asset name, DQ score ring, classification pills, "Open detail →" link
- [ ] **Lineage mini-panel** (`components/lineage/LineageMiniPanel.tsx`):
  - Shows on asset detail Lineage tab
  - Simple upstream/downstream lists (not canvas) showing 1-hop assets as cards
  - "View in full canvas →" link
- [ ] **React Flow setup**:

```tsx
// components/lineage/LineageCanvas.tsx
import ReactFlow, { Controls, Background, useNodesState, useEdgesState } from 'reactflow';
import 'reactflow/dist/style.css';

const AssetNode = ({ data }) => (
  <div style={{
    padding: '8px 12px',
    background: data.selected ? 'var(--color-brand-surface)' : 'var(--color-card-bg)',
    border: `1.5px solid ${data.selected ? 'var(--color-brand)' : 'var(--color-border)'}`,
    borderRadius: 'var(--radius-md)',
    minWidth: 140,
  }}>
    <p style={{ fontWeight: 500, fontSize: 12, color: 'var(--color-text-primary)', margin: 0 }}>
      {data.name}
    </p>
    <p style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--color-text-muted)', margin: 0 }}>
      {data.source}
    </p>
  </div>
);
```

**Milestone check:** Add dbt `manifest.json` via dbt connector → run scan → lineage canvas shows model dependency graph → click node → opens asset detail.

---

## 9. Phase 4 — Polish & Launch Readiness (Weeks 9–10)

> **Goal:** Production-quality UX, full test coverage, performance validation, deployment-ready.

---

### Week 9 — Accessibility, Performance & Notifications

#### Accessibility (UIUX Brief §8 — WCAG 2.1 AA)

- [ ] **Color contrast audit**: run `axe-core` across all pages; fix any contrast failures
- [ ] **Keyboard navigation**: tab through dashboard → catalogue → asset detail → policies; verify logical order
- [ ] **Scan log live region**: add `aria-live="polite"` to the log stream container in `RunningStep`
- [ ] **Form labels**: ensure every input has an explicit `<label>` (not placeholder-only)
- [ ] **Status indicators**: add text alongside every status dot (never color alone)
- [ ] **Focus rings**: verify teal 2px outline visible on all interactive elements
- [ ] **Table headers**: add `scope="col"` to all `<th>` elements in `DataTable`
- [ ] Run full `axe-core` automated sweep → target Lighthouse Accessibility ≥ 90

#### Performance

- [ ] **Lighthouse CI** in GitHub Actions: block PR if Performance < 80 or Accessibility < 90
- [ ] **Catalogue page virtual list**: if asset count > 200, use `@tanstack/virtual` for row virtualization instead of pagination
- [ ] **React Query caching**: set appropriate `staleTime` (5 min for catalogue, 30s for DQ scores, 1 min for issues)
- [ ] **Bundle analysis**: run `next build && next analyze`; code-split any component > 50 KB
- [ ] **SQLite query optimization**: add indexes on `assets.name`, `assets.deleted_at`, `columns.asset_id`, `dq_issues.status`, `audit_log.created_at`

#### Notifications

- [ ] **Email notifications** (USR-002 invite + SCN-006 scan complete): integrate `fastapi-mail` with SMTP config
  - Templates: `invite_email.html`, `scan_complete_email.html`, `dq_issue_alert_email.html`
- [ ] **Slack webhook** (should have): `POST /api/v1/settings/notifications` to configure webhook URL; fire on scan complete + critical DQ issue
- [ ] **In-app toast system** (`components/ui/Toast.tsx`): success (teal), warning (amber), error (red); auto-dismiss 3–5 seconds; positioned bottom-right

---

### Week 10 — Testing, E2E & Launch Prep

#### Backend test coverage target: ≥ 80%

```bash
# Run with coverage report
pytest tests/ -v --cov=app --cov-report=html --cov-fail-under=80
```

Key test files to complete:
- [ ] `tests/test_dq_engine.py` — unit test all 4 metric calculations with known inputs
- [ ] `tests/test_policy_engine.py` — test rule matching for all 5 operators
- [ ] `tests/test_catalogue.py` — integration tests for all catalogue endpoints
- [ ] `tests/test_governance.py` — policy CRUD, audit log generation
- [ ] `tests/test_lineage.py` — graph traversal with multi-hop test fixtures
- [ ] `tests/test_auth.py` — all RBAC scenarios (admin, editor, viewer for each endpoint)

#### 10 critical E2E journeys (Playwright — from TSD §8.1)

```typescript
// frontend/tests/e2e/journeys.spec.ts

test('1. Login and see dashboard', async ({ page }) => { ... });
test('2. Admin invites editor; editor logs in and creates policy', async ({ page }) => { ... });
test('3. Run full scan; DQ scores update on catalogue', async ({ page }) => { ... });
test('4. Search catalogue for "customer"; find asset with DQ score', async ({ page }) => { ... });
test('5. Create PII policy; confirm applies on next scan', async ({ page }) => { ... });
test('6. Viewer cannot edit asset; PATCH returns 403', async ({ page }) => { ... });
test('7. Create glossary term and link to asset', async ({ page }) => { ... });
test('8. DQ issue raised; engineer marks resolved', async ({ page }) => { ... });
test('9. Lineage canvas renders; node-click navigates to detail', async ({ page }) => { ... });
test('10. Audit log shows all CRUD actions from session', async ({ page }) => { ... });
```

#### Empty states

- [ ] All 6 empty states implemented per UIUX Brief §7.2 (no data, no issues, no lineage, etc.)

#### Error boundaries

- [ ] Add React error boundary to each major page section to prevent full-page crashes
- [ ] Backend: global exception handler in `main.py` returning standard error envelope

#### Documentation

- [ ] `README.md`: complete setup guide (§3 of this plan), architecture diagram, env vars table
- [ ] API auto-docs: ensure all endpoints have docstrings (FastAPI auto-generates Swagger at `/docs`)
- [ ] `CHANGELOG.md`: document all features shipped per phase

---

## 10. API Contract Reference

Full endpoint summary for frontend↔backend integration. All under `http://localhost:8000`.

### Catalogue

| Method | Endpoint | Role | Notes |
|--------|----------|------|-------|
| `GET` | `/api/v1/assets` | All | `?q=&type=&source=&tag=&dq_min=&dq_max=&page=&limit=` |
| `GET` | `/api/v1/assets/:id` | All | Full detail with columns, DQ score, tags |
| `PATCH` | `/api/v1/assets/:id` | Editor+ | description, owner_id, tags |
| `GET` | `/api/v1/assets/:id/columns` | All | Paginated; includes per-column DQ scores |
| `GET` | `/api/v1/assets/:id/lineage` | All | Alias for lineage mini-panel |
| `GET` | `/api/v1/assets/:id/glossary-suggestions` | All | Auto-suggestions from column name matching |
| `GET` | `/api/v1/search` | All | `?q=&limit=20` — searches assets + glossary |
| `GET` | `/api/v1/connectors` | Admin | |
| `POST` | `/api/v1/connectors` | Admin | |
| `POST` | `/api/v1/connectors/:id/test` | Admin | Returns `{ success, latency_ms, error? }` |
| `DELETE` | `/api/v1/connectors/:id` | Admin | |

### Quality

| Method | Endpoint | Role | Notes |
|--------|----------|------|-------|
| `GET` | `/api/v1/dq/scores` | All | `?sort=score&order=asc` |
| `GET` | `/api/v1/dq/scores/:asset_id` | All | Metric breakdown + column scores |
| `GET` | `/api/v1/dq/issues` | All | `?status=open&severity=critical&asset_id=` |
| `PATCH` | `/api/v1/dq/issues/:id` | Editor+ | `{ status, resolution_note }` |
| `POST` | `/api/v1/scans` | Editor+ | Enqueues Celery task |
| `GET` | `/api/v1/scans/:id` | All | Scan record + stage progress |
| `GET` | `/api/v1/scans/:id/stream` | All | SSE stream for live progress |
| `GET` | `/api/v1/scans/:id/log` | All | `?cursor=` — paginated log lines |

### Governance

| Method | Endpoint | Role | Notes |
|--------|----------|------|-------|
| `GET` | `/api/v1/policies` | All | `?status=active&type=classification` |
| `POST` | `/api/v1/policies` | Editor+ | |
| `PATCH` | `/api/v1/policies/:id` | Editor+ | |
| `DELETE` | `/api/v1/policies/:id` | Admin | |
| `GET` | `/api/v1/glossary` | All | `?q=&status=active` |
| `POST` | `/api/v1/glossary` | Editor+ | |
| `PATCH` | `/api/v1/glossary/:id` | Editor+ | |
| `DELETE` | `/api/v1/glossary/:id` | Admin | |
| `POST` | `/api/v1/glossary/:id/links` | Editor+ | |
| `DELETE` | `/api/v1/glossary/:id/links/:lid` | Editor+ | |
| `GET` | `/api/v1/lineage/:asset_id` | All | `?depth=3&direction=both` |
| `GET` | `/api/v1/lineage/:asset_id/mini` | All | 1-hop upstream + downstream |
| `POST` | `/api/v1/lineage/refresh` | Editor+ | Manual re-extraction |
| `GET` | `/api/v1/audit-log` | Admin | `?from=&to=&user_id=&event_type=` |

### Identity

| Method | Endpoint | Role | Notes |
|--------|----------|------|-------|
| `POST` | `/api/v1/auth/login` | None | `{ email, password }` |
| `POST` | `/api/v1/auth/refresh` | None | `{ refresh_token }` |
| `POST` | `/api/v1/auth/logout` | JWT | |
| `GET` | `/api/v1/users/me` | JWT | Current user profile |
| `GET` | `/api/v1/users` | Admin | |
| `POST` | `/api/v1/users/invite` | Admin | `{ email, role }` |
| `PATCH` | `/api/v1/users/:id` | Admin | `{ role?, active? }` |
| `GET` | `/health` | None | Health check |

---

## 11. Component Library Checklist

All components needed before page work begins. Build these in Phase 0–1 as a shared library.

### Design system primitives (UIUX Brief §5)

- [ ] `Button` — primary (teal), secondary (gray), danger (red outline), disabled state
- [ ] `Badge` — classification pills: PII (red), GDPR (blue), Finance (amber), Internal (purple), Public (green), custom (gray)
- [ ] `StatusDot` — 6px circle: green (active), amber (warning), gray (inactive), red (error)
- [ ] `DQScoreRing` — 32px circle, color by threshold (≥80/60–79/<60/null)
- [ ] `MetricCard` — flat surface card: label (10px uppercase), value (24px/500), optional bar + badge
- [ ] `ProgressBar` — 4–6px height, track + animated fill, color prop
- [ ] `DataTable` — fixed layout, compact rows, sortable headers, skeleton loading state
- [ ] `SearchInput` — with debounce (300ms), clear button, loading spinner when searching
- [ ] `FilterBar` — horizontal row of filter triggers; active filter count badge
- [ ] `Toast` — bottom-right stack, success/warning/error variants, auto-dismiss
- [ ] `Modal` — focus trap, backdrop, close on Escape + backdrop click
- [ ] `SkeletonRow` — animated placeholder for table rows during load
- [ ] `EmptyState` — icon + message + optional CTA button; variant per page type

### Layout components

- [ ] `Sidebar` — 220px, logo, nav sections + items, active state, count badges, user footer
- [ ] `Topbar` — 48px, breadcrumb left, actions right (Run scan button + user avatar)
- [ ] `Breadcrumb` — "Parent › Current" with muted/primary colors

### Page-specific components

- [ ] `AssetTable` — catalogue list table with all required columns
- [ ] `ColumnTable` — schema table with DQ columns + warning indicators
- [ ] `DQBreakdownPanel` — 4-metric bar chart panel
- [ ] `DQSparkline` — recharts mini line chart for 10-scan trend
- [ ] `IssueRow` — severity-coded issue row with resolve action
- [ ] `PolicyRow` — policy list row with status dot + asset count
- [ ] `PolicyRuleBuilder` — visual rule editor (3 dropdowns + action)
- [ ] `ClassificationCoverage` — 4 colored stat panels (PII, GDPR, unclassified, governed)
- [ ] `GlossaryTermCard` — card with name, truncated definition, status badge, linked count
- [ ] `TermLinkPanel` — linked assets list with remove button
- [ ] `ScanStepper` — step indicator: done (check), active (ring), pending (gray)
- [ ] `SourceSelectStep` — connector card grid with toggle selection
- [ ] `ConfigureStep` — scan type radio + asset scope table + metric toggles
- [ ] `RunningStep` — live progress bars + SSE log stream
- [ ] `ResultsStep` — summary cards + score change table + findings list
- [ ] `LineageCanvas` — React Flow wrapper with custom node + controls
- [ ] `LineageMiniPanel` — 1-hop upstream/downstream list on asset detail

---

## 12. Testing Strategy

### Backend (pytest)

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=app --cov-report=term-missing --cov-fail-under=80

# Single module
pytest tests/test_dq_engine.py -v
```

**Key test fixtures** (`tests/conftest.py`):

```python
@pytest.fixture
def db():
    """In-memory SQLite for tests — never touches local module DB files."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture
def client(db):
    """FastAPI TestClient with test DB override."""
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app)

@pytest.fixture
def admin_token(client):
    resp = client.post("/api/v1/auth/login", json={"email": "admin@test.com", "password": "test"})
    return resp.json()["data"]["access_token"]
```

**DQ engine unit tests** (`tests/test_dq_engine.py`):

```python
def test_completeness_all_filled():
    # Table with 100 rows, 0 nulls → expect 100.0
    assert engine.calculate_completeness(...) == 100.0

def test_completeness_half_null():
    # Table with 100 rows, 50 nulls → expect 50.0
    assert engine.calculate_completeness(...) == 50.0

def test_uniqueness_all_distinct():
    assert engine.calculate_uniqueness(...) == 100.0

def test_consistency_email_pattern():
    # 80 valid emails, 20 invalid → expect 80.0
    assert engine.calculate_consistency(..., "email") == pytest.approx(80.0, 0.1)

def test_accuracy_range():
    # 90 values in range [0,120], 10 outside → expect 90.0
    assert engine.calculate_accuracy(..., {"type": "range", "min": 0, "max": 120}) == 90.0

def test_issue_detection_critical():
    prev = {"completeness": 95.0}
    curr = {"completeness": 40.0}  # Drop of 55 AND below 50%
    issue = engine.detect_issue(prev, curr, "completeness")
    assert issue.severity == "critical"
```

### Frontend (Vitest + React Testing Library)

```bash
# Unit tests
npm run test

# With coverage
npm run test:coverage

# Watch mode
npm run test:watch
```

**Component tests** (`tests/components/DQScoreRing.test.tsx`):

```typescript
describe('DQScoreRing', () => {
  it('renders green ring for score >= 80', () => {
    render(<DQScoreRing score={87.4} />);
    const ring = screen.getByTestId('dq-ring');
    expect(ring).toHaveStyle({ borderColor: '#22C55E' });
  });

  it('renders amber ring for score 60-79', () => {
    render(<DQScoreRing score={72} />);
    expect(screen.getByTestId('dq-ring')).toHaveStyle({ borderColor: '#F59E0B' });
  });

  it('renders red ring for score < 60', () => {
    render(<DQScoreRing score={45} />);
    expect(screen.getByTestId('dq-ring')).toHaveStyle({ borderColor: '#EF4444' });
  });

  it('renders dash for null score', () => {
    render(<DQScoreRing score={null} />);
    expect(screen.getByText('—')).toBeInTheDocument();
  });
});
```

### E2E (Playwright)

```bash
# Run all E2E tests
npx playwright test

# Run specific journey
npx playwright test journeys.spec.ts --grep "Run full scan"

# With UI mode (headed)
npx playwright test --ui
```

**Playwright config** (`playwright.config.ts`):

```typescript
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  baseURL: 'http://localhost:3000',
  use: {
    trace: 'on-first-retry',
  },
  webServer: [
    {
      command: 'npm run dev',
      url: 'http://localhost:3000',
      reuseExistingServer: true,
    },
    {
      command: 'cd ../backend && uvicorn app.main:app --port 8000',
      url: 'http://localhost:8000/health',
      reuseExistingServer: true,
    },
  ],
});
```

---

## 13. Environment Configuration

### `.env.example` (commit this — documents all variables)

```bash
# ── Database ──────────────────────────────────────────────────────
# SQLite for local dev (no server needed)
ADMIN_DATABASE_URL=sqlite:///./datagov_admin.db
CATALOGUE_DATABASE_URL=sqlite:///./datagov_catalogue.db
CLASSIFICATION_DATABASE_URL=sqlite:///./datagov_classification.db
QUALITY_DATABASE_URL=sqlite:///./datagov_quality.db
POLICY_DATABASE_URL=sqlite:///./datagov_policy.db
GLOSSARY_DATABASE_URL=sqlite:///./datagov_glossary.db
AUDIT_DATABASE_URL=sqlite:///./datagov_audit.db
SAMPLE_SOURCE_PATH=sample_business.db

# ── Auth ──────────────────────────────────────────────────────────
SECRET_KEY=your-secret-key-change-in-production-minimum-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480

# ── Redis / Celery ────────────────────────────────────────────────
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# ── App ───────────────────────────────────────────────────────────
DEBUG=true
CORS_ORIGINS=http://localhost:3000

# ── Email (Phase 4) ───────────────────────────────────────────────
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@email.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=DataGov <noreply@datagov.local>

# ── Notifications (Phase 4) ───────────────────────────────────────
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx/yyy/zzz

# ── OAuth (Phase 4) ───────────────────────────────────────────────
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
```

### `.env.local` (gitignored — actual local values)

```bash
ADMIN_DATABASE_URL=sqlite:///./datagov_admin.db
CATALOGUE_DATABASE_URL=sqlite:///./datagov_catalogue.db
SECRET_KEY=dev-secret-key-not-for-production
DEBUG=true
CORS_ORIGINS=http://localhost:3000
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
```

### Frontend environment (`frontend/.env.local`)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=DataGov
```

---

## Phase 4 update — quality gate completion

Phase 4 hardens the localhost MVP for handoff:

- Accessibility: app shell skip link, active navigation semantics, table captions, and error/not-found boundaries.
- Performance: automatic SQLite indexes for common catalogue, DQ, audit, scan, notification, and glossary queries.
- Notifications: admin-managed email and Slack notification targets with local test actions and scan-completion audit dispatch.
- Tests: backend integration coverage for scoped connectors and notification dispatch, plus Playwright smoke coverage for the main journey.
- Launch docs: `LAUNCH_READINESS.md` captures runtime, verification commands, metadata DB split, and production follow-ups.

## 14. Migration Path — SQLite → PostgreSQL

When ready to deploy to a real server or staging environment, switch each module URL from SQLite to its PostgreSQL database.

### Step 1 — Update connection string

```bash
# .env.local or server environment
ADMIN_DATABASE_URL=postgresql://datagov_user:your_password@localhost:5432/datagov_admin
CATALOGUE_DATABASE_URL=postgresql://datagov_user:your_password@localhost:5432/datagov_catalogue
QUALITY_DATABASE_URL=postgresql://datagov_user:your_password@localhost:5432/datagov_quality
```

### Step 2 — Update `database.py`

```python
# Remove SQLite-specific connect_args for each module engine and add pool settings.
engine = create_engine(module_url, pool_size=10, max_overflow=20, echo=settings.debug)
```

### Step 3 — Update column types in models (optional improvements)

```python
# These work in both SQLite and PostgreSQL — but can be enhanced:
# UUID: SQLite stores as VARCHAR(36), PostgreSQL can use native UUID type
# JSON: SQLite stores as TEXT, PostgreSQL can use native JSONB for indexing

# For full PostgreSQL optimisation (optional):
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
tags = Column(JSONB, default=list)  # enables GIN index for fast JSON queries
```

### Step 4 — Regenerate migrations

```bash
# Generate a new migration that handles type differences
alembic revision --autogenerate -m "postgres_type_upgrades"
alembic upgrade head
```

### What does NOT change

- All SQLAlchemy ORM queries — 100% portable
- All Pydantic schemas — database-agnostic
- All service and business logic — no SQL dialect dependencies
- All API routes — completely unaffected
- All tests — switch `conftest.py` fixture to PostgreSQL URL for CI

> **Estimated migration effort: 1–2 hours** for a single developer.

---

## 15. Definition of Done

A feature is **Done** when all of the following are true:

### Code quality

- [ ] All linting passes: `ruff check` (Python), `eslint` (TypeScript)
- [ ] All formatting passes: `ruff format` (Python), `prettier` (TypeScript)
- [ ] No `TODO` comments left in production code paths (move to GitHub Issues)
- [ ] No hardcoded credentials, URLs, or secrets

### Tests

- [ ] Backend unit tests written for all new service methods (≥ 80% line coverage maintained)
- [ ] Integration tests cover all new API endpoints (happy path + at least one error case)
- [ ] Frontend component tests written for all new UI components
- [ ] Relevant E2E journey passes in Playwright

### API

- [ ] All new endpoints have FastAPI docstrings (appear in Swagger at `/docs`)
- [ ] All new endpoints enforce correct RBAC (tested with wrong-role request returning 403)
- [ ] All new endpoints return standard response envelope `{ data, meta }`

### Frontend

- [ ] All color values use CSS variables from `globals.css` — no hardcoded hex in component code
- [ ] All displayed numbers rounded appropriately (score to 1 decimal, counts to integer)
- [ ] Loading state (skeleton) implemented for all data-fetching components
- [ ] Empty state implemented for all list/table views
- [ ] Error state handled for failed API calls (toast notification shown)

### Design system compliance (UIUX Brief)

- [ ] Sentence case on all visible text labels and buttons
- [ ] Font: Inter for UI text, JetBrains Mono for column names / data types / source paths
- [ ] Classification pills use the correct color from the UIUX Brief §5.3 (no exceptions)
- [ ] DQ score rings use the correct threshold colors: ≥80 green, 60–79 amber, <60 red
- [ ] Status dots paired with text label — never color alone

### BRD acceptance criteria

- [ ] All Must Have BRD requirements for this feature pass their acceptance criteria
- [ ] Manually verified against the BRD acceptance criteria table before PR is opened

---

## Quick Reference — Week-by-Week Summary

| Week | Phase | Primary Focus | BRD Features |
|------|-------|---------------|--------------|
| Days 1–3 | 0 | Scaffold, DB, tooling | All (foundation) |
| 1 | 1 | Auth, users, RBAC | USR-001–005 |
| 2 | 1 | Connectors, asset discovery | CAT-001–003 |
| 3 | 1 | Scan engine, scan flow UI | SCN-001–005 |
| 4 | 2 | DQ engine, 4 metrics | DQ-001–008 |
| 5 | 2 | Policy engine, governance | GOV-001–007 |
| 6 | 2 | Integration, DQ issues, dashboard | DQ-009–010, SCN-004–005 |
| 7 | 3 | Business glossary | GLO-001–005 |
| 8 | 3 | Table-level lineage, canvas | LIN-001–005 |
| 9 | 4 | Accessibility, performance, notifications | NFR-001–014 |
| 10 | 4 | Test coverage, E2E, launch prep | All acceptance criteria |

---

*Document version 1.0 — DataGov MVP Development Plan*  
*Last updated: March 29, 2026*  
*References: BRD-DataGov-MVP-v1.0 · TSD-DataGov-MVP-v1.0 · UIUX-Brief-DataGov-MVP-v1.0*
