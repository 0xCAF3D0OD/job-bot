# Règles de l'interface

Ce qui vaut pour toute la plateforme, quelle que soit la page. Chaque règle renvoie au document qui l'a posée.

## Illustrations (docs/62, docs/67)

1. Une illustration seulement si l'écran n'a rien d'autre à montrer (vide, erreur, première fois) ou pour marquer un moment (réussite, transition d'une page qui charge).
2. Jamais dans un formulaire, une liste ou un tableau ; jamais dans une carte (posée à côté, ou au-dessus pour la carte d'une réussite).
3. Une seule famille : les images générées pour jobA1 (des personnes dans des scènes calmes), en version transparente, sans cadre ni fond. 300 px au plus, 200 sur téléphone ; dans l'accueil, 260 px (200 sur téléphone), le personnage qui parle 320 px (240) ; la présentation de la plateforme, 440 px en tête et 320 par étape. Exceptions : la carte d'une réussite (220 px, 170 sur téléphone) et l'Engagement (440 px, 260 sur téléphone) ; la page de connexion, coupée en deux, où l'illustration occupe la moitié gauche (440 px au plus, 320 sur téléphone : c'est une bannière).
4. En sombre, la série sombre quand elle existe ; sinon l'image claire assombrie (luminosité 85 %). Décorative pour les lecteurs d'écran : le texte à côté dit tout.
5. Une entrée une fois chargée (fondu et légère montée, 500 ms), rien si « réduire les animations » est demandé. Préparées par `frontend/scripts/illustrations.mjs` (480 et 800 px). Les dessins unDraw d'avant restent en réserve (`frontend/reserve/`), non chargés.

## Mouvement (docs/59)

1. Le mouvement répond à une action (appui, survol, choix, envoi) ; rien ne bouge tout seul en boucle, sauf une vraie attente (rédaction par l'IA).
2. Trois durées : 150 ms (survol, appui), 250 ms (un état qui change), 500 ms (une entrée). Exceptions écrites : la carte d'une réussite monte en 420 ms avec un léger rebond (docs/61 §1) ; la transition d'une page qui charge entre et sort en 400 ms et reste au moins 1,2 s, rien si la page arrive en moins de 0,15 s (docs/63 §3).
3. « Réduire les animations » : les retours restent (couleurs, coches, textes), sans mouvement.

## Accès à un contenu (docs/57)

L'élément entier est cliquable, avec un survol ; pas de « › » ni de « Continuer › ». Les vraies actions gardent leur verbe.
