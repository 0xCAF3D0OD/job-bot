#!/bin/sh
# Installe le Chromium de Playwright et ses dépendances système, avec trois essais.
# Le miroir apt des runners GitHub répond parfois « 503 Service Unavailable » (19.11.2026) : l'installation
# échoue alors avec le code 100 sans rapport avec la PR. On réessaie après une pause, sans rien changer
# à ce qui est installé (les captures de référence restent prises avec les mêmes paquets).
# Usage : sh scripts/installer-chromium.sh <commande playwright…>
#   ex. sh scripts/installer-chromium.sh npx playwright install --with-deps chromium
set -u
essai=1
while [ "$essai" -le 3 ]; do
  "$@" && exit 0
  echo "Installation du navigateur : essai $essai sur 3 échoué (miroir apt indisponible ?)."
  [ "$essai" -lt 3 ] && sleep 45
  essai=$((essai + 1))
done
exit 1
