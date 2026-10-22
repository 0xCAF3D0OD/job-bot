# 134 — Le Suivi : la colonne à la hauteur du calendrier, l'état des preuves en bandeau (version 1.5.1)

> Statut : **correction demandée** le 2026-10-22 (« pourquoi tu n'as pas gardé le système de défilement d'avant dans le calendrier pour garder la hauteur fixe ? … "en cours, remise" ce n'est pas très bien structuré, ça ne respecte pas nos règles »).

## Pourquoi c'était arrivé

- **Le défilement** : en 1.3.0 (docs/130 §A), j'ai remplacé la colonne défilante à la hauteur du calendrier, demandée le 7 octobre, par « 5 lignes, puis Voir les N autres », et j'ai écrit dans `docs/interface.md` « jamais une liste défilante dans la page ». C'était contraire à ton retour validé ; une fois dépliée, la colonne dépassait largement le calendrier.
- **L'état des preuves** : « En cours · remise avant le 5 novembre 2026 » et « Compléter 3 lignes » étaient serrés dans la rangée du compte, à côté des onglets, au lieu d'un bandeau daté (docs/95 §2, la forme des choses datées).

## Ce qui change

1. **La colonne de droite** reprend la hauteur du calendrier : les onglets « À relancer » et « À déclarer » restent en haut, la liste défile dessous, estompée en haut et en bas là où il reste des lignes ; plus de « Voir les N autres ». Sur téléphone, la liste défile dans 70 % de la hauteur de l'écran.
2. **L'état des preuves** devient un bandeau daté sous le compte du mois, comme sur Aujourd'hui : une phrase et une action.
   - « Preuves d'octobre : 3 lignes à compléter, remise avant le 5 novembre 2026. » · Compléter
   - « Preuves d'octobre prêtes : à remettre avant le 5 novembre 2026. » · Marquer comme remis
   - « Preuves d'octobre remises le 3 novembre 2026. » · Annuler la remise
3. **La règle** de `docs/interface.md` (Les listes) est corrigée : la liste à côté du calendrier du Suivi prend sa hauteur et défile dedans.

## Vérifié

- Tests de l'interface : la colonne avec toutes les lignes, l'estompage, les onglets hors de la partie qui défile ; le bandeau et ses trois états. 449 tests, lint, vue-tsc.
- Captures en sombre à 1440 et 390 px : la colonne mesure la hauteur du calendrier (498 px) ; le bandeau sur un mois remis.
- Les trois audits, avec exploration, sur la démo et sur un compte neuf ; l'accessibilité aussi en sombre.
