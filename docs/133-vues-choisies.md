# 133 — Les vues choisies : une chose à la fois, rien en double (version 1.5.0)

> Statut : **validé d'avance** le 2026-10-22 (« écris le cadrage 133 et exécute-le »).
> Origine : tes captures du Bilan, du Suivi et du Rendez-vous en mode sombre, après la 1.4.1, et ta question « est-ce que c'est le constat ergonomique qui t'a poussé à faire comme cela ? ». Réponse : non. Les règles interdisaient déjà ces défauts (un seul cadre par bloc, docs/74) ; mes audits ne regardaient que l'état par défaut des pages et ne voyaient pas l'intérieur de « Le détail », replié.

## Le constat

1. **Suivi** : « À relancer » puis « À déclarer dans Job-Room », l'un sous l'autre dans la colonne de droite : il faut parcourir la page de haut en bas.
2. **Bilan › Le détail** : une carte repliable qui contient des cartes (Parcours, Par mois, quatre analyses, Semaines), des cartes dans une carte.
3. **Bilan, la place** : les quatre tuiles sur une rangée, puis « Objectif ORP » sur toute la largeur.
4. **Bilan, le doublon** : le mois en cours (« 7 / 13 candidatures ») est déjà dans « Mois ORP » d'Aujourd'hui.
5. **Rendez-vous** : la carte du rendez-vous et les questions côte à côte ; les questions, longues, passent sur deux lignes alors que la page a la place.
6. **Suivi, la légende** : une carte repliable à part, sous le calendrier.

## La phrase qui guide

**On choisit ce qu'on regarde ; une seule chose s'affiche à la fois, dans un seul cadre.**

## 1. Suivi : deux onglets à droite

- En haut de la colonne de droite, « À relancer · 10 » et « À déclarer · 7 », un sélecteur à deux choix ; une seule liste à la fois, la forme de ligne d'Aujourd'hui.
- Un jour choisi dans le calendrier remplace les onglets par ce jour, comme aujourd'hui.

## 2. Bilan › Le détail : un sélecteur, une vue

- « Le détail » devient un titre de section avec, sur sa ligne, un sélecteur : **Parcours**, **Par mois**, **Ce qui marche**, **Semaines**, **Entretiens** (et **Pour l'ORP** sur un mois).
- Dessous, **une seule carte** : la vue choisie. « Ce qui marche » met ses quatre comparaisons dans cette carte, séparées par des filets, sur deux colonnes.
- Le choix est retenu sur l'appareil.
- « Enseignements » (les retours d'entretien) devient la vue « Entretiens » : plus de ligne repliable à part.

## 3. Bilan : les tuiles en carrés, les mois passés à côté

- Les quatre tuiles en **2 × 2** à gauche ; à droite, **« Mois précédents »** : juillet, août, septembre, avec leur compte sur l'objectif et « atteint » ou « manqué ».
- La jauge du mois en cours quitte le Bilan : elle est sur Aujourd'hui (§4).

## 4. Rendez-vous : de la place pour le texte

- « Le prochain rendez-vous » sur toute la largeur, date, lieu et conseiller sur une ligne.
- « Questions au conseiller » sur toute la largeur dessous, puis « La feuille ».

## 5. Suivi : la légende au-dessus du calendrier

- Une ligne discrète au-dessus du calendrier : une pastille et un mot par statut ; plus de carte repliable.

## Garde-fous

- Les audits ouvrent les repliables et choisissent chaque vue avant de conclure ; captures en clair **et en sombre**, à 1440 et 390 px.
- Rien ne disparaît : chaque vue du détail reste à un clic, le mois en cours reste sur Aujourd'hui.

## Écarts (1.5.0)

- **Les audits explorent** : un module commun (`frontend/scripts/explore.py`) ouvre une à une les lignes repliables et choisit chaque vue (le détail du Bilan, les listes du Suivi) ; les trois audits passent sur chaque état. L'audit d'accessibilité tourne aussi en sombre (`SCHEME=dark`).
- **Trouvé grâce à l'exploration, et corrigé** :
  - le journal des alertes ouvert collait au bord de sa carte (une règle retirait la marge des tableaux dans un volet) et débordait sur téléphone : marge rétablie, deux colonnes masquées sur téléphone, 10 lignes puis « Afficher plus » au lieu de 50 ;
  - en sombre, les étiquettes orange (vue « Entretiens ») manquaient de contraste : leur règle sombre était écrite avant la règle claire, qui l'écrasait.
- **Le sélecteur du détail** reste sur une ligne, même à cinq ou six vues (le style commun des sélecteurs passait à deux colonnes au-delà de trois choix) ; sur téléphone, la ligne défile.
- **« Mois précédents »** : les trois mois répartis sur la hauteur de la carte, à côté des tuiles.
- **Suivi sur téléphone** : « Octobre 2026 » ne passe plus sous la flèche du mois suivant.
- **L'assistant** : consigne `assistant-v20`.

## Vérifié (1.5.0)

- Tests de l'interface : le détail (une vue à la fois, retenue, les comparaisons dans une seule carte), « Mois précédents », les onglets du Suivi. 449 tests, lint, vue-tsc. Backend : la consigne. 632 tests, ruff, mypy.
- Les trois audits, avec exploration, à zéro sur la démo et sur un compte neuf ; l'accessibilité aussi en sombre.
- Captures en sombre à 1440 et 390 px : Bilan (Parcours, Ce qui marche), Suivi, Rendez-vous ; aucune page plus large que l'écran.
