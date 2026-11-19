## Mouvement des éléments : entrées et sorties douces dans toute l'app (Kevin, 19.11.2026, 11 h 15)

- Changer de page reste instantané, sans transition entre les routes. Seuls les éléments à l'intérieur d'une page s'animent (illustration, titre, cartes, boutons, pastilles, feuilles, menus ⋯, toasts, panneaux ordinateur, cartes de tri).
- Entrée : opacité 0 → 1 et translateY 8 px → 0, 320 ms, cubic-bezier(0.05, 0.7, 0.1, 1). Cascade de 40 ms entre deux éléments, sur les 5 premiers éléments visibles au plus ; les suivants entrent avec le 5e.
- Sortie : opacité 1 → 0 et translateY 0 → 4 px, 180 ms, cubic-bezier(0.3, 0, 0.8, 0.15).
- Feuilles et îlots : translateY 24 px → 0 et opacité, 300 ms, courbe d'entrée ; fond assombri en fondu de 200 ms ; sortie en 200 ms, courbe de sortie.
- Changement d'étape dans une page : la barre glisse en 300 ms, cubic-bezier(0.2, 0, 0, 1) ; l'ancien contenu sort en 150 ms, puis le nouveau entre en 320 ms, jamais les deux à la fois.
- Chargement : un élément qui attend ses données entre quand elles sont là ; avant, un squelette à sa taille finale, sans décalage de mise en page.
- Technique : seulement opacity et transform ; variables partagées --motion-enter, --motion-exit, --motion-stagger (frontend/src/motion.css) ; rien ne bloque un clic.
- Mouvement réduit (prefers-reduced-motion) : fondu d'opacité seul, 150 ms, sans déplacement ni cascade (WCAG 2.3.3). Remplace, pour ces entrées et sorties, « tout mouvement s'arrête » de docs/regles-ui-ergonomie.md §6.
- Ne s'animent pas : le texte tapé, les champs, les listes longues.
- Ordre de travail : une PR « motion tokens », puis une PR par zone, en commençant par les premiers pas (CV, Ce que tu cherches, Alerte et ses états de code, Trier), téléphone et ordinateur.
