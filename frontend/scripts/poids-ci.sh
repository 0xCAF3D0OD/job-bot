#!/bin/sh
# Le budget de poids pour la CI et make audits-ci (Kevin, 16.11 : docs/decisions/2026-11-16-1425-audit-poids-main-depasse.md
# et 2026-11-16-1518-limites-par-page.md). Construit la branche et la base (POIDS_BASE, origin/main par défaut ;
# HEAD^1 dans la CI, le main sur lequel la PR est fusionnée), puis mesure la branche avec --base :
#   - l'avant/après des pages que la branche change (dans la CI : résumé de l'exécution et note sur la PR) ;
#   - une mesure que main dépassait déjà passe si la branche ne l'alourdit pas ; une branche qui ajoute du poids
#     au-delà d'une limite reste bloquée.
cd "$(dirname "$0")/.." || exit 1
npx vite build --logLevel error || exit 1
BASE="${POIDS_BASE:-origin/main}"
TMP="$(mktemp -d)"
trap 'git worktree remove --force "$TMP/base" >/dev/null 2>&1; rm -rf "$TMP"' EXIT
[ "$BASE" = "origin/main" ] && git fetch -q origin main 2>/dev/null
if git worktree add -q --detach "$TMP/base" "$BASE" 2>/dev/null; then
  ln -s "$PWD/node_modules" "$TMP/base/frontend/node_modules"
  # Les tailles de la base, avec le script de la branche (mêmes mesures des deux côtés).
  if (cd "$TMP/base/frontend" && npx vite build --logLevel error >/dev/null 2>&1) &&
    node scripts/poids.mjs --dist "$TMP/base/frontend/dist/" --json "$TMP/base.json"; then
    exec node scripts/poids.mjs --base "$TMP/base.json"
  fi
fi
echo "poids : pas de comparaison possible avec $BASE, mesure de la branche seule."
node scripts/poids.mjs
