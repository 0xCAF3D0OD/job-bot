# Commandes de développement local. Ne construit aucune image et ne déploie rien :
# l'infrastructure (conteneurs, CI, Kubernetes…) se branche sur docs/exploitation.md.

SHELL := /bin/bash
PG_BIN ?= $(shell brew --prefix postgresql@17 2>/dev/null)/bin

.PHONY: setup migrate dev test lint openapi check-openapi check

setup: ## installe les dépendances et crée les bases jobbot et jobbot_test
	@command -v uv >/dev/null || { echo "uv manquant : brew install uv"; exit 1; }
	@test -x "$(PG_BIN)/psql" || { echo "PostgreSQL manquant : brew install postgresql@17 && brew services start postgresql@17"; exit 1; }
	@test -f .env || cp .env.example .env
	cd backend && uv sync
	cd frontend && npm install
	@for db in jobbot jobbot_test; do \
		"$(PG_BIN)/psql" -d postgres -Atc "SELECT 1 FROM pg_database WHERE datname = '$$db'" | grep -q 1 \
			|| { "$(PG_BIN)/createdb" $$db && echo "base $$db créée"; }; \
	done
	@mkdir -p data

migrate: ## applique les migrations
	cd backend && uv run jobbot migrate

check: ## vérifie configuration et base
	cd backend && uv run jobbot check

dev: ## lance api + worker + frontend (http://localhost:5173), Ctrl-C arrête tout
	@trap 'kill 0' INT TERM EXIT; \
	(cd backend && uv run jobbot api) & \
	(cd backend && uv run jobbot worker) & \
	(cd frontend && npm run dev) & \
	wait

test: ## tests backend (base jobbot_test) et frontend
	cd backend && uv run pytest
	cd frontend && npm run -s test && npm run -s typecheck

lint: ## ruff, mypy, eslint
	cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy src tests
	cd frontend && npm run -s lint

openapi: ## régénère le contrat OpenAPI et les types du frontend
	cd backend && uv run jobbot openapi > ../frontend/src/api/openapi.json
	cd frontend && npm run -s openapi

check-openapi: openapi ## échoue si les types du frontend ne correspondent plus au backend
	git diff --exit-code -- frontend/src/api
