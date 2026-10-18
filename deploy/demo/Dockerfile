# Démo en ligne de jobA1 (docs/77) : deux images construites depuis la racine du dépôt.
#   api : le serveur jobA1 (API et commandes), en mode démo par ses réglages.
#   web : Caddy, avec l'interface déjà construite ; HTTPS automatique.

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
COPY --from=ghcr.io/astral-sh/uv:0.8 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/opt/venv PATH=/opt/venv/bin:$PATH
WORKDIR /app
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY backend/ ./
RUN uv sync --frozen --no-dev
COPY deploy/demo/nightly.py /app/nightly.py
ARG VERSION=dev
ENV JOBBOT_VERSION=$VERSION
# Aucun droit particulier : un utilisateur sans mot de passe, qui n'écrit que dans /data.
RUN useradd --create-home --uid 10001 jobbot && mkdir -p /data && chown jobbot /data
USER jobbot
EXPOSE 8000
CMD ["jobbot", "api"]

# --- Le site -------------------------------------------------------------------------------
FROM caddy:2-alpine AS web
COPY deploy/demo/Caddyfile /etc/caddy/Caddyfile
COPY --from=frontend /app/frontend/dist /srv
