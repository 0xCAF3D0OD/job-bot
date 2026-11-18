#!/bin/sh
# Le test d'affichage (frontend/e2e, décision de Kevin du 18.11.2026) : une démo à heure figée, puis Playwright.
#   - la base E2E_DB (créée si besoin) est vidée et remplie par `jobbot demo-seed`, horloge arrêtée à E2E_TIME ;
#   - le serveur tourne lui aussi à cette heure (frontend/scripts/serveur_fige.py), l'interface en `vite` ;
#   - Playwright compare chaque écran à sa capture de référence et lance le script de contrôle (a à h).
# Arguments : passés à `playwright test` (ex. --update-snapshots, --project=telephone-clair, -g envoyees).
# Variables : E2E_DATABASE_URL (rôle propriétaire de la base), E2E_TIME, E2E_API_PORT, E2E_WEB_PORT, CHROME.
set -eu
cd "$(dirname "$0")/.."

E2E_TIME=${E2E_TIME:-2026-11-18T10:00:00+01:00}
E2E_DATABASE_URL=${E2E_DATABASE_URL:-postgresql+psycopg://localhost:5432/jobbot_e2e}
E2E_API_PORT=${E2E_API_PORT:-8300}
E2E_WEB_PORT=${E2E_WEB_PORT:-5300}
export E2E_TIME CAPTURES_TIME="$E2E_TIME"
# Comme la démo en ligne : migration et remplissage avec le rôle propriétaire, l'API avec le rôle restreint jobbot_app.
E2E_APP_PASSWORD=${E2E_APP_PASSWORD:-e2e-app}
app_url=$(printf '%s' "$E2E_DATABASE_URL" | sed -E "s#://([^@/]*@)?#://jobbot_app:$E2E_APP_PASSWORD@#")
export JOBBOT_DEMO=true JOBBOT_MIGRATE_DATABASE_URL="$E2E_DATABASE_URL" JOBBOT_DATABASE_URL="$app_url" JOBBOT_API_PORT="$E2E_API_PORT" \
  JOBBOT_ANTHROPIC_API_KEY= JOBBOT_IMAP_USER= JOBBOT_IMAP_PASSWORD= JOBBOT_NTFY_TOPIC= \
  JOBBOT_STORAGE_PATH=../data/e2e

base=${E2E_DATABASE_URL##*/}
admin=$(printf '%s' "${E2E_DATABASE_URL%/*}/postgres" | sed 's/+psycopg//')
psql "$admin" -Atc "SELECT 1 FROM pg_database WHERE datname = '$base'" | grep -q 1 \
  || psql "$admin" -qc "CREATE DATABASE $base"

fige="uv run --with time-machine python ../frontend/scripts/serveur_fige.py"
(cd backend && uv run jobbot migrate >/dev/null)
psql "$(printf '%s' "$E2E_DATABASE_URL" | sed 's/+psycopg//')" -qc "ALTER ROLE jobbot_app WITH LOGIN PASSWORD '$E2E_APP_PASSWORD'"
(cd backend && $fige demo-seed)

pids=""
trap 'kill $pids 2>/dev/null || true' EXIT INT TERM
(cd backend && exec $fige api) > /tmp/e2e-api.log 2>&1 &
pids="$pids $!"
(cd frontend && JOBBOT_DEV_API_URL="http://127.0.0.1:$E2E_API_PORT" exec npx vite --strictPort --port "$E2E_WEB_PORT") > /tmp/e2e-web.log 2>&1 &
pids="$pids $!"

for _ in $(seq 1 90); do
  curl -sf -o /dev/null "http://localhost:$E2E_WEB_PORT/api/offers?limit=1" && break
  sleep 1
done
curl -sf -o /dev/null "http://localhost:$E2E_WEB_PORT/api/offers?limit=1" || { tail -n 30 /tmp/e2e-api.log /tmp/e2e-web.log; exit 1; }

cd frontend && E2E_URL="http://localhost:$E2E_WEB_PORT" npx playwright test "$@"
