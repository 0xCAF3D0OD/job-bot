## Notes de l'éventail sur une ligne (Kevin, 16.11.2026, 8 h 56 et 14 h 19)

- Chaque carte garde ses 3 notes, sur 1 ligne chacune avec « … », qu'elle ait une forme courte (score-v9) ou non
  (PR #755).
- Entre la dernière note et le poste : 24 px au moins (`--space-6`), le même écart qu'entre l'en-tête et les notes.
- Les notes restent centrées. Une note coupée garde une marge de chaque côté, comme une note courte : Kevin avait
  demandé « environ 88 % de la largeur de la carte ».
- Écart retenu, validé par Kevin à 14 h 19 : 16 px de chaque côté (`--space-4`), soit une ligne de 240 px sur les
  272 px de la zone de texte (88 %). Raisons :
  - 88 % de la carte entière (282 px) dépasserait la zone de texte, qui fait 272 px à cause du padding de 24 px ;
  - `max-width: 88%` donnait des marges de 16,3 px, hors de la grille de 4 (l'audit grille relevait 48 écarts).
