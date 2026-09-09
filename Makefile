# PY defaults to whatever `python` resolves to; activate backend/.venv first, or
# override it:  make dev PY=backend/.venv/Scripts/python.exe
PY ?= python

.PHONY: up down testdb check worker worker-once migrate seed dev web mobile test gen-api

up:
	docker compose up -d

down:
	docker compose down

# The compose stack now runs the whole system, not just a database.
testdb:
	docker compose exec -T db psql -U sunrise -d sunrise -c "CREATE DATABASE sunrise_test" || true

# Everything CI runs, locally, in the same order.
check:
	cd backend && $(PY) -m ruff check app seed.py worker.py tests || true
	cd backend && $(PY) -m pytest -q

worker:
	cd backend && $(PY) worker.py

worker-once:
	cd backend && $(PY) worker.py --once

migrate:
	cd backend && $(PY) -m alembic upgrade head

seed:
	cd backend && $(PY) seed.py

dev:
	cd backend && $(PY) -m uvicorn app.main:app --reload --port 8000

web:
	npm --prefix web run dev

mobile:
	npx expo start --cwd mobile

test: testdb
	cd backend && $(PY) -m pytest -q

gen-api:
	npx openapi-typescript http://localhost:8000/openapi.json -o packages/api-types/schema.d.ts
