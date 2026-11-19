## K5 amendée : « Écarter » fait exception (Kevin, 19.11.2026, 13 h 35)

Amende [la décision K5 du 17.11](2026-11-17-2150-offre-reste-en-place.md) (une offre qui change d'état reste à sa place jusqu'au changement de liste).

1. « Écarter » retire tout de suite l'offre de la liste, dans Nouvelles, Gardées et En préparation (et Toutes). Les cartes du dessous remontent avec la sortie du mouvement des éléments (`--motion-exit`, 180 ms).
2. Le message « Offre écartée · Annuler » ne change pas. « Annuler » remet l'offre à sa place exacte.
3. K5 reste valable pour les autres changements d'état qui gardent l'offre dans la liste : Garder, statut, note refaite.
4. Même comportement pour « Écarter N offres » de la sélection multiple : les N cartes sortent ensemble, avec un seul message.
5. Rien ne change côté serveur.
