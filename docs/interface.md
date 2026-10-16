# Règles de l'interface

Ce qui vaut pour toute la plateforme, quelle que soit la page. Chaque règle renvoie au document qui l'a posée.

## Illustrations (docs/62)

1. Une illustration seulement si l'écran n'a rien d'autre à montrer (vide, erreur, première fois) ou pour marquer un moment (réussite, transition d'une page qui charge).
2. Jamais dans un formulaire, une liste ou un tableau ; jamais dans une carte (posée à côté, ou au-dessus pour la carte d'une réussite).
3. Une seule famille : des objets et des personnages unDraw, sans maquette d'écran ni cadre. 220 px au plus, 140 sur téléphone. Deux exceptions, les moments : la carte d'une réussite (170 px, 130 sur téléphone) et l'Engagement (380 px, 200 sur téléphone).
4. Couleurs des tokens : violet `--accent`, encre `--faint`, plans `--border`, papier `--surface`. Décorative pour les lecteurs d'écran : le texte à côté dit tout.
5. Animée une fois à l'apparition, rien si « réduire les animations » est demandé. Préparées par `frontend/scripts/illustrations.mjs`, sans changer leurs formes.

## Mouvement (docs/59)

1. Le mouvement répond à une action (appui, survol, choix, envoi) ; rien ne bouge tout seul en boucle, sauf une vraie attente (rédaction par l'IA).
2. Trois durées : 150 ms (survol, appui), 250 ms (un état qui change), 500 ms (une entrée). Exceptions écrites : la carte d'une réussite monte en 420 ms avec un léger rebond (docs/61 §1) ; la transition d'une page qui charge entre et sort en 400 ms et reste au moins 1,2 s, rien si la page arrive en moins de 0,15 s (docs/63 §3).
3. « Réduire les animations » : les retours restent (couleurs, coches, textes), sans mouvement.

## Accès à un contenu (docs/57)

L'élément entier est cliquable, avec un survol ; pas de « › » ni de « Continuer › ». Les vraies actions gardent leur verbe.
