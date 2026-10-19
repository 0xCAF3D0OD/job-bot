# Règles de l'interface

Ce qui vaut pour toute la plateforme, quelle que soit la page. Chaque règle renvoie au document qui l'a posée.

## Titres et textes (docs/88)

1. Le titre d'une page reprend mot pour mot son entrée du menu, sans sous-titre ; une petite précision peut se mettre au-dessus, en capitales (la date d'Aujourd'hui). Les pages de présentation (connexion, Découvrir, accueil) gardent leurs phrases.
2. Titres de cartes, d'onglets, de sections et légendes : un nom, sans « ton », « ta », « tes », « mon », « ma », « mes ».
3. Boutons et liens d'action : un verbe à l'infinitif (« Demander un certificat intermédiaire »).
4. Le tutoiement reste dans les phrases : messages, erreurs, états vides.
5. Un texte d'aide reste affiché pour une erreur (avec quoi faire), un avertissement avant une action irréversible, ou ce qui part à l'IA, en une ligne. Ce qui explique passe en description au survol (`HoverNote`, docs/53) ou disparaît : l'assistant répond au reste.
6. Pas de prix dans le libellé d'un bouton : le coût d'une action IA est dans sa description au survol (« Environ 0,10 $. »).
7. Un test (`frontend/src/titles.test.ts`) vérifie les règles 1, 2 et 6.

## La barre du haut (docs/89)

Trois pages dans le menu principal (docs/90) : Aujourd'hui, Candidatures, Progresser. À droite, une capsule : la cloche, puis l'initiale du compte, qui ouvre le menu du compte (Profil, Réglages, Données personnelles, Diagnostic, « Collecter maintenant », la déconnexion) ; sur téléphone, ☰ s'y ajoute et ne montre que les trois pages. Du nouveau à lire : un point, pas un chiffre ; un chiffre dit ce qui attend une action. Dans la capsule, des zones sans cadre ni fond, séparées par des filets ; ouvrir l'une déroule le cadre vers le bas, et son contenu apparaît dedans (docs/91). Les menus « ⋯ » ont le même style : bordure fine, coins de 10 px, presque pas d'ombre, un déroulé court.

## Illustrations (docs/62, docs/67)

1. Une illustration seulement si l'écran n'a rien d'autre à montrer (vide, erreur, première fois) ou pour marquer un moment (réussite, transition d'une page qui charge).
2. Jamais dans un formulaire, une liste ou un tableau ; jamais dans une carte (posée à côté, ou au-dessus pour la carte d'une réussite).
3. Une seule famille : les images générées pour jobA1 (des personnes dans des scènes calmes), en version transparente, sans cadre ni fond. 300 px au plus, 200 sur téléphone ; dans l'accueil, 260 px (200 sur téléphone), le personnage qui parle 320 px (240) ; la présentation de la plateforme, 440 px en tête (320 sur téléphone) et 250 par étape (190). Exceptions : la carte d'une réussite (220 px, 170 sur téléphone) et l'Engagement (440 px, 260 sur téléphone) ; la page de connexion, coupée en deux, où la scène remplit toute la moitié gauche (élargie à 57 %), et un bandeau sur téléphone. Hors famille : le personnage du titre, un dessin unDraw animé fourni par Kevin, un par heure (docs/68).
4. En sombre, la série sombre quand elle existe ; sinon l'image claire assombrie (luminosité 85 %). Décorative pour les lecteurs d'écran : le texte à côté dit tout.
5. Une entrée une fois chargée (fondu et légère montée, 500 ms), rien si « réduire les animations » est demandé. Préparées par `frontend/scripts/illustrations.mjs` (480 et 800 px ; 480, 800 et 1264 pour la connexion). Exceptions : la transition d'une page qui charge garde les dessins unDraw animés d'avant, aux couleurs des tokens (`LoadingDrawing`, docs/67 complément 0.55.1) ; la page de maintenance montre le dessin unDraw de la maintenance, au même endroit qu'une illustration (300 px, 200 sur téléphone), et en boucle (docs/80) ; les autres dessins unDraw restent en réserve (`frontend/reserve/`), non chargés.

## Mouvement (docs/59)

1. Le mouvement répond à une action (appui, survol, choix, envoi) ; rien ne bouge tout seul en boucle, sauf une vraie attente (rédaction par l'IA, page de maintenance : son dessin unDraw bouge tant que l'attente dure, docs/80).
2. Trois durées : 150 ms (survol, appui), 250 ms (un état qui change), 500 ms (une entrée). Exceptions écrites : la carte d'une réussite monte en 420 ms avec un léger rebond (docs/61 §1) ; la transition d'une page qui charge entre et sort en 400 ms et reste au moins 1,2 s, rien si la page arrive en moins de 0,15 s (docs/63 §3) ; en sombre, la connexion joue une fois la vidéo du soir qui tombe (9 s), puis reste sur l'image du soir (docs/67, complément 0.55.3) ; le personnage du titre, une fois connecté, ne bouge qu'au survol du titre (docs/68) ; sur la connexion, le ciel suit la vidéo (9 s) et la phrase change de couleur en 1,2 s à 5,5 s de la vidéo (docs/67, compléments 0.55.3 à 0.55.5) ; le chemin de La plateforme suit le défilement (120 ms), entier d'emblée si « réduire les animations » (docs/67) ; la capsule se déroule en 350 ms et un menu « ⋯ » en 250 ms, sur la courbe `cubic-bezier(0.72, 0.01, 0, 1)` prise à Sphere, leur contenu en fondu (docs/91).
3. « Réduire les animations » : les retours restent (couleurs, coches, textes), sans mouvement.

## Accès à un contenu (docs/57)

L'élément entier est cliquable, avec un survol ; pas de « › » ni de « Continuer › ». Les vraies actions gardent leur verbe.

## La note (docs/73, docs/76)

Un cercle dont le contour se remplit comme la note (plein à 100), à la couleur de la note ; la part manquante reste visible en gris clair. Une offre pas encore notée : un cercle vide en pointillés, avec « – », qui dit pourquoi au survol. Jamais une pastille.

## Les actions (docs/74, docs/76)

1. Dans chaque partie (ou ligne d'un tableau), le contenu reste visible, avec au plus une action importante ; le reste va dans « ⋯ », en haut à droite de la partie ou au bout de la ligne.
2. Les suppressions toujours dans « ⋯ », en dernier, en rouge, après un filet, avec leur confirmation.
3. Pas de « ⋯ » pour une seule action ordinaire : elle s'affiche directement.
4. Chaque « ⋯ » a un nom pour les lecteurs d'écran : « Actions sur … ». 2,75 rem au doigt ; le menu ne sort jamais de l'écran, ni sous une barre fixe.
5. Restent visibles sans menu : les « Copier » à côté des champs, les téléchargements qui sont le but d'une carte (PDF, Word), les listes de liens qui sont le contenu, les étapes d'un parcours, les boutons d'un formulaire.

## Les listes (docs/73)

Une ligne par élément, séparées par un filet ; une ligne par jour quand la liste suit les jours. Au moins 0,75 rem au-dessus et au-dessous d'une ligne, et entre un texte et la carte qui suit.

## Un seul cadre par bloc (docs/74, docs/76)

Dans une carte ou un volet, un tableau, une liste ou un repliable perd son propre cadre : des lignes séparées par un filet, alignées sur le texte de la carte. Jamais deux cadres l'un dans l'autre.

## Écrans de travail sur téléphone (docs/75)

Sous 820 px, un écran où l'on travaille un moment (l'entraînement à l'entretien) prend tout l'écran ; sa barre du haut garde le titre sur une ligne et ses actions.

