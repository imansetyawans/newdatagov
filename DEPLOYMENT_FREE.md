# Free Deployment Guide

This project can be deployed with a free-friendly split:

- Frontend: Vercel Hobby
- Backend API: Vercel FastAPI serverless
- Metadata database: Supabase Free or Neon Free PostgreSQL

Railway is not used for the free deployment path because its free trial is credit-based, not a permanent free hosting tier.
Render can still be used with `render.yaml`, but Render API service creation currently requires billing details on this account even for a free web service.

## 1. Database

Create or restore a Supabase/Neon PostgreSQL project and copy the connection string.

Use the SQLAlchemy psycopg format:

```text
postgresql+psycopg://USER:PASSWORD@HOST:5432/postgres
```

The backend supports a single shared `DATABASE_URL` for all DataGov metadata modules. Localhost still defaults to the modular SQLite files.

For Supabase transaction/session poolers, the backend disables psycopg prepared statements automatically to avoid pooler prepared-statement conflicts.

## 2. Backend on Vercel

Create a Vercel project from the `backend` directory. The backend uses:

```text
backend/vercel.json
backend/pyproject.toml
backend/app/index.py
```

Required Vercel production environment variables:

```text
DATABASE_URL=postgresql+psycopg://...
CORS_ORIGINS=["https://your-datagov-app.vercel.app"]
DEBUG=false
SECRET_KEY=<long random secret>
ACCESS_TOKEN_EXPIRE_MINUTES=480
AI_METADATA_MODEL=gpt-5-mini
```

The Vercel FastAPI build command is defined in `pyproject.toml` and seeds the cloud database:

```bash
python -m app.scripts.seed_dev
```

Production backend URL used for the current deployment:

```text
https://newdatagov-api.vercel.app
```

## 3. Frontend on Vercel

Create a Vercel project from the `frontend` directory.

Set:

```text
NEXT_PUBLIC_API_URL=https://your-datagov-api.vercel.app
```

Build command:

```bash
npm run build
```

## 4. Final Smoke Test

After both deployments are live:

1. Open the Vercel URL.
2. Login with `admin@datagov.local` / `admin123`.
3. Open Settings > Connectors and test the sample connector.
4. Run a scan.
5. Check Catalogue, Quality, Policies, Glossary, and Lineage.

## Notes

- Vercel serverless functions can have a cold start after idle time; the first request after a quiet period can be slower.
- The sample SQLite source is seeded for demo scans. Production connectors should use cloud databases such as BigQuery, PostgreSQL, MySQL, Snowflake, or a local agent.
- Do not use SQLite metadata databases as production cloud storage.
