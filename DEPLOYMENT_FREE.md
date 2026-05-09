# Free Deployment Guide

This project can be deployed with a free-friendly split:

- Frontend: Vercel Hobby
- Backend API: Render Free Web Service
- Metadata database: Supabase Free or Neon Free PostgreSQL

Railway is not used for the free deployment path because its free trial is credit-based, not a permanent free hosting tier.

## 1. Database

Create or restore a Supabase/Neon PostgreSQL project and copy the connection string.

Use the SQLAlchemy psycopg format in Render:

```text
postgresql+psycopg://USER:PASSWORD@HOST:5432/postgres
```

The backend supports a single shared `DATABASE_URL` for all DataGov metadata modules. Localhost still defaults to the modular SQLite files.

## 2. Backend on Render

Create a Render Blueprint from this repository or create a Web Service manually.

Blueprint file:

```text
render.yaml
```

Required Render environment variables:

```text
DATABASE_URL=postgresql+psycopg://...
CORS_ORIGINS=["https://your-datagov-app.vercel.app"]
DEBUG=false
SECRET_KEY=<long random secret>
```

Build command:

```bash
pip install -r requirements.txt && python -m app.scripts.seed_dev
```

Start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## 3. Frontend on Vercel

Create a Vercel project from the `frontend` directory.

Set:

```text
NEXT_PUBLIC_API_URL=https://your-datagov-api.onrender.com
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

- Render Free may sleep after idle time; the first request after sleep can be slow.
- The sample SQLite source is seeded for demo scans. Production connectors should use cloud databases such as BigQuery, PostgreSQL, MySQL, Snowflake, or a local agent.
- Do not use SQLite metadata databases as production cloud storage.
