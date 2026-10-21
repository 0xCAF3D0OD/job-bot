# Commandes de développement local. Ne construit aucune image et ne déploie rien :
# l'infrastructure (conteneurs, CI, Kubernetes…) se branche sur docs/exploitation.md.

SHELL := /bin/bash
PG_BIN ?= $(shell brew --prefix postgresql@17 2>/dev/null)/bin

.PHONY: setup migrate update dev demo demo-image demo-image-stop test lint openapi check-openapi check extension

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

update: ## met la plateforme à jour : maintenance annoncée, git pull, dépendances, migrations (docs/79)
	@cd backend && uv run jobbot maintenance on "Mise à jour de jobA1" \
		|| echo "(maintenance pas annoncée : version d'avant 0.65)"
	git pull --ff-only
	cd backend && uv sync
	cd frontend && npm install --no-audit --no-fund
	cd backend && uv run jobbot migrate
	cd backend && uv run jobbot maintenance off
	@echo "Mise à jour faite. Redémarre make dev (Ctrl-C, puis make dev) pour charger la nouvelle version ; si la base a changé, la page de maintenance reste affichée jusque-là."
	@echo "En cas d'échec d'une étape : la maintenance reste annoncée ; « cd backend && uv run jobbot maintenance off » la lève."

dev: ## lance api + worker + frontend (http://localhost:5173), Ctrl-C arrête tout
	@trap 'kill 0' INT TERM EXIT; \
	(cd backend && uv run jobbot api) & \
	(cd backend && uv run jobbot worker) & \
	(cd frontend && npm run dev) & \
	wait

# Démo en local (docs/72, complément 0.59.1) : sa propre base, des données fictives recalées
# sur le jour, et ses propres ports (API 8200, interface 5200), à côté de make dev. Ni IA, ni
# boîte e-mail, ni notifications, ni worker.
DEMO_DB := jobbot_demo
DEMO_ENV := JOBBOT_DEMO=true JOBBOT_DATABASE_URL=postgresql+psycopg://localhost:5432/$(DEMO_DB) \
	JOBBOT_API_PORT=8200 JOBBOT_ANTHROPIC_API_KEY= JOBBOT_IMAP_USER= JOBBOT_IMAP_PASSWORD= \
	JOBBOT_NTFY_TOPIC= JOBBOT_STORAGE_PATH=../data/demo
DEMO_OPEN ?= open

demo: ## démo en local, données fictives (http://localhost:5200), Ctrl-C arrête tout
	@"$(PG_BIN)/psql" -d postgres -Atc "SELECT 1 FROM pg_database WHERE datname = '$(DEMO_DB)'" \
		| grep -q 1 || { "$(PG_BIN)/createdb" $(DEMO_DB) && echo "base $(DEMO_DB) créée"; }
	cd backend && $(DEMO_ENV) uv run jobbot migrate && $(DEMO_ENV) uv run jobbot demo-seed
	@trap 'kill 0' INT TERM EXIT; \
	(cd backend && $(DEMO_ENV) uv run jobbot api) & \
	(cd frontend && JOBBOT_DEV_API_URL=http://127.0.0.1:8200 npm run dev -- --port 5200) & \
	(until curl -sf -o /dev/null http://localhost:5200; do sleep 1; done; $(DEMO_OPEN) http://localhost:5200) & \
	wait

# La démo en ligne (docs/77) essayée sur ton ordinateur, dans Docker, comme sur le serveur.
DEMO_LOCAL := cd deploy/demo && DEMO_DOMAIN=http://localhost DEMO_HTTP_PORT=8280 DEMO_HTTPS_PORT=8643 \
	DEMO_PUBLIC_URL=http://localhost:8280 docker compose -p joba1-demo-local

demo-image: ## la démo en ligne dans Docker, sur http://localhost:8280 (make demo-image-stop pour l'arrêter)
	$(DEMO_LOCAL) up -d --build --wait
	@echo "Démo : http://localhost:8280"

demo-image-stop: ## arrête la démo Docker locale et efface ses données
	$(DEMO_LOCAL) down -v

test: ## tests backend (base jobbot_test) et frontend
	cd backend && uv run pytest
	cd frontend && npm run -s test && npm run -s typecheck && npm run -s poids

poids: ## le budget de poids des pages (docs/117 §3)
	cd frontend && npm run -s poids

lint: ## ruff, mypy, eslint
	cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy src tests
	cd frontend && npm run -s lint

openapi: ## régénère le contrat OpenAPI et les types du frontend
	cd backend && uv run jobbot openapi > ../frontend/src/api/openapi.json
	cd frontend && npm run -s openapi

check-openapi: openapi ## échoue si les types du frontend ne correspondent plus au backend
	git diff --exit-code -- frontend/src/api

# Seulement ce que l'extension utilise : ni le relevé de Job-Room, ni le script de relevé, ni
# les textes de la boutique (docs/71 §6).
EXTENSION_FILES := manifest.json background.js popup.html popup.css popup.js fill.js fill-job-room.js icons

extension: ## paquet de l'extension pour la boutique de Mozilla (extension/web-ext-artifacts/)
	cd extension && mkdir -p web-ext-artifacts \
		&& version=$$(node -p "require('./manifest.json').version") \
		&& rm -f web-ext-artifacts/joba1-$$version.zip \
		&& zip -q -X -r web-ext-artifacts/joba1-$$version.zip $(EXTENSION_FILES) \
		&& echo "extension/web-ext-artifacts/joba1-$$version.zip"
