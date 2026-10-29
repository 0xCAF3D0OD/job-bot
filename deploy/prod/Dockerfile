# La vraie plateforme jobA1 sur le serveur (docs/136). Construit par GitHub Actions
# (.github/workflows/images.yml), jamais sur le serveur : il n'a qu'un processeur et 2 Go.
#   api : le serveur jobA1 (API, worker, commandes). Sert aussi à la démo du serveur.
#   web : Caddy, l'interface déjà construite, HTTPS pour la plateforme et pour la démo.

# --- L'interface ---------------------------------------------------------------------------
FROM node:22-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
# La vérification des types lit aussi les fichiers de l'extension (tests du remplissage).
COPY extension/ /app/extension/
RUN npm run build

# --- Le serveur ----------------------------------------------------------------------------
FROM python:3.13-slim AS api
# pg_dump et pg_restore de la même version que la base (PostgreSQL 17) : les sauvegardes du
# worker et `jobbot restore` en ont besoin (docs/82).
RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-client-17 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:0.8 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/opt/venv PATH=/opt/venv/bin:$PATH
WORKDIR /app
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY backend/ ./
RUN uv sync --frozen --no-dev
# La remise à neuf de nuit de la démo, qui tourne sur le même serveur avec cette image.
COPY deploy/demo/nightly.py /app/nightly.py
ARG VERSION=dev
ENV JOBBOT_VERSION=$VERSION
# Aucun droit particulier : un utilisateur sans mot de passe, qui n'écrit que dans /data et
# /sauvegardes.
RUN useradd --create-home --uid 10001 jobbot && mkdir -p /data /sauvegardes \
    && chown jobbot /data /sauvegardes
USER jobbot
EXPOSE 8000 8001
CMD ["jobbot", "api"]

# --- Le site -------------------------------------------------------------------------------
FROM caddy:2-alpine AS web
COPY deploy/prod/Caddyfile /etc/caddy/Caddyfile
COPY --from=frontend /app/frontend/dist /srv
