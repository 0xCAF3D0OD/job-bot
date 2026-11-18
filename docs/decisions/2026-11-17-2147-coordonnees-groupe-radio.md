## Choix Permis, Disponibilité et Préavis : motif « Radio Group » (Kevin, 17.11.2026, 21 h 47)

- Les choix des feuilles Coordonnées sont dans un `role="radiogroup"` : chaque choix a `role="radio"` et
  `aria-checked`, jamais `aria-pressed` (ARIA APG, motif « Radio Group »). Le `aria-pressed` de la maquette §66 était
  une erreur ; Kevin corrige les deux planches Coordonnées (claire et sombre).
- Clavier : Tab entre dans le groupe sur le choix actif (ou le premier) puis en sort ; les flèches passent d'un choix à
  l'autre et le cochent, Début et Fin vont aux extrémités (FormAnswerSheet.vue, test FormAnswerSheet.test.ts).
- Inchangé : la coche sur le choix actif, et un second appui qui retire le choix (la réponse peut redevenir vide).
