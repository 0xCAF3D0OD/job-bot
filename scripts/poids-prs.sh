#!/bin/sh
# Mesure chaque PR ouverte fusionnée à blanc avec main (workflow poids-prs.yml) et pose le statut
# « Poids avec le main actuel » sur son dernier commit. Argument : les tailles de main (poids.mjs --json).
# Une PR qui ne touche pas frontend/ a le poids de main : statut vert sans mesure.
set -u
MAIN_JSON="$1"
REPO="${GITHUB_REPOSITORY:?}"
CONTEXTE="${CONTEXTE:-Poids avec le main actuel}"
RUN_URL="${GITHUB_SERVER_URL:-https://github.com}/$REPO/actions/runs/${GITHUB_RUN_ID:-}"
git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
MAIN_SHA="$(git rev-parse HEAD)"
statut() { # statut <sha> <state> <description>
  gh api -X POST "repos/$REPO/statuses/$1" -f state="$2" -f context="$CONTEXTE" \
    -f description="$(printf '%s' "$3" | cut -c1-140)" -f target_url="$RUN_URL" > /dev/null
}
echec=0
for n in $(gh api "repos/$REPO/pulls?state=open&base=main&per_page=100" --jq '.[] | select(.head.repo.full_name == "'"$REPO"'") | .number'); do
  sha="$(gh api "repos/$REPO/pulls/$n" --jq .head.sha)"
  echo "::group::#$n ($sha)"
  git checkout -q --detach "$MAIN_SHA"
  git fetch -q origin "pull/$n/head"
  if git diff --quiet "$(git merge-base "$MAIN_SHA" FETCH_HEAD)" FETCH_HEAD -- frontend/; then
    statut "$sha" success "Ne touche pas l'interface : poids de main."
    echo "::endgroup::"; continue
  fi
  if ! git merge -q --no-edit FETCH_HEAD > /dev/null 2>&1; then
    git merge --abort 2>/dev/null
    statut "$sha" failure "Conflit avec main : fusionner main dans la branche, puis le poids sera mesuré."
    echec=1; echo "::endgroup::"; continue
  fi
  sortie="$(cd frontend && npx vite build --logLevel error 2>&1 && node scripts/poids.mjs --base "$MAIN_JSON" 2>&1)"
  code=$?
  echo "$sortie"
  if [ "$code" -eq 0 ]; then
    statut "$sha" success "Sous les limites de poids, fusionnée avec main ${MAIN_SHA%"${MAIN_SHA#???????}"}."
  else
    trop="$(printf '%s\n' "$sortie" | grep -m1 '^TROP' || echo 'Une limite de poids dépassée')"
    statut "$sha" failure "Avec le main actuel : $trop"
    echo "::error::#$n : $trop"; echec=1
  fi
  echo "::endgroup::"
done
git checkout -q --detach "$MAIN_SHA"
exit 0
