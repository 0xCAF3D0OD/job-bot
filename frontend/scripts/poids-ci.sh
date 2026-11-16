#!/bin/sh
# Le budget de poids pour la CI et make audits-ci (Kevin, 16.11 : docs/decisions/2026-11-16-1425-audit-poids-main-depasse.md).
# Construit la branche et la mesure. Si une mesure dépasse sa limite, construit aussi la base (POIDS_BASE, origin/main
# par défaut ; HEAD^1 dans la CI, le main sur lequel la PR est fusionnée) et la remesure avec --base : une mesure
# que main dépassait déjà passe si la branche ne l'alourdit pas. Une branche qui ajoute du poids reste bloquée.
cd "$(dirname "$0")/.." || exit 1
npx vite build --logLevel error || exit 1
node scripts/poids.mjs && exit 0
BASE="${POIDS_BASE:-origin/main}"
TMP="$(mktemp -d)"
trap 'git worktree remove --force "$TMP/base" >/dev/null 2>&1; rm -rf "$TMP"' EXIT
[ "$BASE" = "origin/main" ] && git fetch -q origin main 2>/dev/null
echo "Au moins une mesure dépasse : comparaison avec $BASE."
git worktree add -q --detach "$TMP/base" "$BASE" || { echo "poids : $BASE introuvable"; exit 1; }
ln -s "$PWD/node_modules" "$TMP/base/frontend/node_modules"
(cd "$TMP/base/frontend" && npx vite build --logLevel error >/dev/null) || { echo "poids : build de $BASE impossible"; exit 1; }
# Les tailles de la base, avec le script de la branche (mêmes mesures des deux côtés).
node scripts/poids.mjs --dist "$TMP/base/frontend/dist/" --json "$TMP/base.json" || exit 1
node scripts/poids.mjs --base "$TMP/base.json"
