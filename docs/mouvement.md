# Le mouvement des éléments

Décision de Kevin du 19.11.2026 (docs/decisions/2026-11-19-1115-mouvement-des-elements.md). Les variables et les
utilitaires sont dans `frontend/src/motion.css`, chargé sur toutes les pages.

**Changer de page reste instantané.** Seuls les éléments à l'intérieur d'une page s'animent. On n'anime que
`opacity` et `transform`. Rien ne bloque un clic. Le texte tapé, les champs et les listes longues ne s'animent pas.

## Les variables

| Variable | Valeur | Mouvement réduit |
| --- | --- | --- |
| `--motion-enter` | 320 ms cubic-bezier(0.05, 0.7, 0.1, 1) | 150 ms linear |
| `--motion-exit` | 180 ms cubic-bezier(0.3, 0, 0.8, 0.15) | 150 ms linear |
| `--motion-stagger` | 40 ms | 0 |
| `--motion-sheet` / `--motion-sheet-exit` | 300 ms courbe d'entrée / 200 ms courbe de sortie | 150 ms linear |
| `--motion-scrim` | 200 ms (fond assombri) | 150 ms linear |
| `--motion-step-exit` | 150 ms courbe de sortie | 150 ms linear |
| `--motion-progress` | 300 ms cubic-bezier(0.2, 0, 0, 1) | 0 |
| `--motion-rise` / `--motion-sink` / `--motion-sheet-rise` | 8 px / 4 px / 24 px | 0 |

## Les utilitaires

| Cas | Code |
| --- | --- |
| Un élément qui entre | `class="motion-in"`, et `style="--motion-i: 2"` pour son rang dans la cascade (0 à 4) |
| Un groupe en cascade | `class="motion-cascade"` sur le parent : les 5 premiers enfants à 40 ms d'écart, les suivants avec le 5e |
| Un élément qui apparaît et disparaît | `<Transition name="motion">` |
| Une feuille ou un îlot | `<Transition name="motion-sheet">`, le fond assombri dans `<Transition name="motion-scrim">` |
| Le contenu d'une étape qui change | `<Transition name="motion-step" mode="out-in">` : l'ancien sort en 150 ms, puis le nouveau entre |
| Une barre de progression | `class="motion-bar"` sur le remplissage, `style="--motion-value: 0.4"`, dans une piste en `overflow: hidden` |

## Chargement

Un élément qui attend ses données n'entre que quand elles sont là. Avant, un squelette (`LoadingBlocks`) à sa
taille finale : la page ne bouge pas quand le contenu arrive.

## Tests

Le test d'affichage tourne en mouvement réduit et capture avec les animations coupées ; il attend en plus la fin
des animations avant les contrôles. Garde-fou : `frontend/src/motion.test.ts`.
