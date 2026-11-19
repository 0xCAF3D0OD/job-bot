#!/bin/sh
# Installe le Chromium de Playwright puis ses dépendances système, sans dépendre d'un seul passage du miroir apt.
# Le 19.11.2026, le miroir apt des runners GitHub a répondu « 503 Service Unavailable » pendant plus de vingt
# minutes : `playwright install --with-deps chromium` sortait en code 100 avant même de télécharger le navigateur,
# et tous les tests d'affichage et audits échouaient sans rapport avec la PR.
#   1. le navigateur (téléchargé depuis le CDN de Playwright, pas depuis apt) : trois essais ;
#   2. les dépendances système (apt) : cinq essais, une minute d'écart. Si apt ne répond toujours pas, on continue
#      avec un avertissement : l'image ubuntu-24.04 contient déjà les bibliothèques de Chromium. Aucun faux vert
#      possible : une bibliothèque absente empêche le lancement, une police absente change les captures.
# Les paquets demandés ne changent pas : les captures de référence restent valables.
# Usage : sh scripts/installer-chromium.sh <commande playwright>
#   ex. sh scripts/installer-chromium.sh npx playwright
#       sh scripts/installer-chromium.sh uv run --with playwright playwright
set -u
essayer() { # essayer <essais> <pause> <commande…>
  max=$1; pause=$2; shift 2; n=1
  while [ "$n" -le "$max" ]; do
    "$@" && return 0
    echo "Essai $n sur $max échoué : $*"
    [ "$n" -lt "$max" ] && sleep "$pause"
    n=$((n + 1))
  done
  return 1
}
essayer 3 20 "$@" install chromium || exit 1
if ! essayer 5 60 "$@" install-deps chromium; then
  echo "::warning::Dépendances système de Chromium non installées (miroir apt indisponible) : on continue avec celles de l'image du runner."
fi
exit 0
