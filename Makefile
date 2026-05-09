.PHONY: dev backend frontend celery redis test migrate seed lint format

dev:
	powershell -ExecutionPolicy Bypass -File scripts/dev.ps1

backend:
	cd backend && uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

celery:
	cd backend && celery -A app.workers.celery_app worker --loglevel=info

redis:
	docker compose up redis

test:
	cd backend && pytest tests/ -v
	cd frontend && npm run test

migrate:
	cd backend && alembic upgrade head

seed:
	cd backend && python -m app.scripts.seed_dev

lint:
	cd backend && ruff check app tests
	cd frontend && npm run lint

format:
	cd backend && ruff format app tests
