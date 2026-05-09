# DataGov MVP Launch Readiness

## Localhost Runtime

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- Health check: `http://localhost:8000/health`
- Login: `admin@datagov.local` / `admin123`

Start both services from the repository root:

```powershell
.\start-localhost.ps1
```

Stop recorded localhost processes:

```powershell
.\start-localhost.ps1 -Stop
```

## Metadata Databases

DataGov stores its own metadata separately from scanned source data:

- `backend/datagov_admin.db`: users, connectors, scans, notifications
- `backend/datagov_catalogue.db`: assets, columns, lineage references
- `backend/datagov_classification.db`: labels and assignments
- `backend/datagov_quality.db`: DQ issues
- `backend/datagov_policy.db`: policies
- `backend/datagov_glossary.db`: glossary terms
- `backend/datagov_audit.db`: audit trail

The sample source connector reads `sample_business.db` plus attached schemas `sales`, `hr`, and `finance`.

## Verification Commands

```powershell
cd backend
$env:PYTHONPATH='.'
.\.venv\Scripts\ruff.exe check app tests
.\.venv\Scripts\pytest.exe tests -q
```

```powershell
cd frontend
npm run lint
npm run build
npm run test:e2e
```

## Operational Checks

- Login redirects unauthenticated users to `/login`.
- Run Scan lets users choose connector schema/table scope before writing catalogue metadata.
- PII and masking policies are enforced through API sample endpoints.
- Recent audit logs are visible on core pages and include user/time/action.
- Notification settings can be created, tested, disabled, and deleted from Settings.
- Scan completion dispatches enabled localhost notification events into the audit log.
- SQLite performance indexes are created automatically at backend startup.

## Known Production Follow-Ups

- Replace localhost notification audit stubs with real SMTP and Slack webhook delivery workers.
- Move module database URLs from SQLite to PostgreSQL connection strings.
- Add hosted secret management for connector credentials and webhook URLs.
- Replace development `SECRET_KEY` before any shared environment use.
