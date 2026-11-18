## Poids de la fiche d'une offre : blocs chargés à part, mesurés un à un (Kevin, 18.11.2026, 13 h 37)

- « Autres offres chez … » (planche Offre) et la feuille de la compatibilité se chargent à part de Candidatures.
- Chaque bloc est mesuré avec la page, sous les limites de Candidatures (175 500 o en JS, 72 500 o en CSS) : pages candidatures-autres-offres et candidatures-compatibilite de frontend/scripts/poids.mjs. Aucune limite n'est relevée.
- Les deux blocs ouverts ensemble dépassent la limite de la page (176 727 o mesurés le 18.11) : accepté, parce que la page s'ouvre plus légère et que le surplus ne se charge qu'après un geste sur la fiche.
