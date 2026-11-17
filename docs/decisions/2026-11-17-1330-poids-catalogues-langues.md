## Poids des catalogues de langue (Kevin, 17.11.2026, 13 h 30)

- La limite de chaque page reste celle d'aujourd'hui, mesurée en français (docs/decisions/2026-11-16-1518-limites-par-page.md). Elle ne change pas avec les traductions.
- Chaque catalogue (une page × une langue) reçoit sa propre limite dans la PR qui le crée : sa mesure gzip + 5 %, arrondie à la centaine d'octets inférieure, jamais relevée ensuite, comme les autres limites.
- Le code d'une page et son catalogue le plus lourd restent ensemble sous le budget public de 365 Kio gzip (téléphone moyen en 4G, The Performance Inequality Gap 2024).
- `poids.mjs` mesure les catalogues à partir de la PR 1 ; chaque PR d'écran affiche le poids avant et après de la page et de ses catalogues.
