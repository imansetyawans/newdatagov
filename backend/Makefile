.PHONY: dev test migrate seed lint format

dev:
	uvicorn app.main:app --reload --port 8000

test:
	pytest tests/ -v

migrate:
	alembic upgrade head

seed:
	python -m app.scripts.seed_dev

lint:
	ruff check app tests

format:
	ruff format app tests

