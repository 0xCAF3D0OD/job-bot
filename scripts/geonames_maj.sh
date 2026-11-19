#!/bin/sh
# Mise à jour manuelle des numéros postaux suisses (filtre « Distance », issue #468), une fois par an.
# Lancée à la main seulement (`make geonames-maj COMMIT=<commit>`) : l'application ne télécharge jamais rien.
# Source : https://github.com/zauberware/postal-codes-json-xml-csv (données GeoNames, CC BY 4.0).
# Après la commande : mettre à jour le commit, la date et l'empreinte dans backend/src/jobbot/data/geonames/README.md,
# relancer les tests (backend/tests/test_geo.py) et vérifier les distances de quelques villes.
set -eu
COMMIT="${1:?usage : scripts/geonames_maj.sh <commit du dépôt zauberware>}"
DEST="$(cd "$(dirname "$0")/.." && pwd)/backend/src/jobbot/data/geonames/zipcodes.ch.csv"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
git clone --quiet --filter=blob:none --no-checkout https://github.com/zauberware/postal-codes-json-xml-csv.git "$WORK/depot"
git -C "$WORK/depot" checkout --quiet "$COMMIT" -- data/CH.zip
unzip -q -o "$WORK/depot/data/CH.zip" zipcodes.ch.csv -d "$WORK"
head -1 "$WORK/zipcodes.ch.csv" | grep -q '^country_code,zipcode,place,state,state_code,province,province_code,community,community_code,latitude,longitude' \
  || { echo "colonnes inattendues : rien n'est remplacé" >&2; exit 1; }
cp "$WORK/zipcodes.ch.csv" "$DEST"
echo "Remplacé : $DEST"
echo "Lignes : $(($(wc -l < "$DEST") - 1))  Empreinte : $(sha256sum "$DEST" | cut -d' ' -f1)"
echo "Commit : $(git -C "$WORK/depot" rev-parse "$COMMIT")  Date du commit : $(git -C "$WORK/depot" log -1 --format=%cs "$COMMIT")"
