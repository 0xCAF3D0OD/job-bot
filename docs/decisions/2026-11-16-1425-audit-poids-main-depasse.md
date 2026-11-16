## Audit de poids quand main dépasse déjà (Kevin, 16.11.2026, 14 h 25)

- Quand main dépasse déjà une limite de poids (JS ou CSS), une PR dont la mesure baisse ou reste égale passe en vert ; seule une PR qui ajoute du poids à cette mesure reste bloquée.
- Mise en œuvre : `frontend/scripts/poids-ci.sh` (CI et `make audits-ci`) mesure la branche ; si une mesure dépasse, il construit la base (HEAD^1 dans la CI, le main sur lequel la PR est fusionnée ; origin/main en local) et compare avec `poids.mjs --base`.
- Les limites ne changent pas, et la règle des illustrations en WebP reste bloquante.
- Suite : issue « Budget JS et CSS » (JS et CSS du premier écran par page, limite par page, 5 plus gros modules avec des pistes chiffrées, écarts expliqués). Plus aucun relèvement de css-total ou de js-total sans passer par cette issue.
