#!/bin/sh
# Le poids de la branche comparé à main (make audits-ci, Kevin 15.11) : une ligne par mesure, en octets gzip (brut
# pour les images). Construit main dans un dossier à part (git worktree) ; la branche doit déjà être construite
# (npm run poids). N'échoue jamais : c'est une information, la limite reste vérifiée par npm run poids.
# Règle (README, Limites de poids) : plus de 0,5 Ko de JS ou de CSS en plus se justifie dans la description de la PR.
cd "$(dirname "$0")/.." || exit 0
BASE="${POIDS_BASE:-origin/main}"
TMP="$(mktemp -d)"
trap 'git worktree remove --force "$TMP/main" >/dev/null 2>&1; rm -rf "$TMP"' EXIT
git fetch -q origin main 2>/dev/null
git worktree add -q --detach "$TMP/main" "$BASE" 2>/dev/null || { echo "poids : $BASE introuvable, pas de comparaison"; exit 0; }
ln -s "$PWD/node_modules" "$TMP/main/frontend/node_modules"
(cd "$TMP/main/frontend" && npx vite build --logLevel error >/dev/null 2>&1) || { echo "poids : build de $BASE impossible"; exit 0; }
node scripts/poids.mjs --dist "$TMP/main/frontend/dist/" --json "$TMP/main.json" || exit 0
node scripts/poids.mjs --json "$TMP/branche.json" || exit 0
BASE="$BASE" node -e '
const [base, head] = process.argv.slice(1).map((f) => JSON.parse(require("fs").readFileSync(f, "utf8")));
console.log(`Poids de la branche par rapport à ${process.env.BASE} (octets) :`);
let big = false;
for (const name of Object.keys(head)) {
  const d = head[name] - (base[name] ?? 0);
  if (/^(js|css)-total$/.test(name) && d > 500) big = true;
  console.log(`  ${name.padEnd(17)}${String(base[name] ?? "-").padStart(9)} → ${String(head[name]).padStart(9)}  ${d > 0 ? "+" : ""}${d}`);
}
if (big) console.log("Plus de 0,5 Ko de JS ou de CSS en plus : justifie-le dans la description de la PR (README, Limites de poids).");
' "$TMP/main.json" "$TMP/branche.json"
