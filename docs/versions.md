# Numéros de version

Réserver son numéro ici avant d'ouvrir une PR, dans la même PR que son travail, ou par une ligne ajoutée tôt sur sa
branche. Le prochain numéro libre est le plus grand des deux listes (fichiers de `changelog.d/` et réservations
ci-dessous) plus un. Deux PR qui prendraient le même numéro ajoutent le même fichier `changelog.d/X.Y.Z.md` : GitHub le
signale aussitôt ; celle qui fusionne en second prend le numéro suivant.

Une fois la PR fusionnée, sa ligne peut rester : `changelog.d/X.Y.Z.md` fait alors foi.

| Version | Session | Tâche | Branche | État |
|---|---|---|---|---|
| 1.6.36 | Dépôt | Un fichier par version dans `changelog.d/` | `chore/1.6.36-changelog-d` | fusionnée |
| 1.6.37 | Design | En-tête sur ordinateur | `fix/1.6.37-en-tete` | fusionnée |
| 1.6.38 | Dépôt | Tableau de coordination et réservation des numéros | `chore/1.6.38-coordination` | fusionnée |
| 1.6.39 | Design | Règles §6 : la séparation sous l'en-tête en fondu au défilement | `docs/regles-6-fondu` | fusionnée (#355) |
| 1.6.40 | Dépôt | Inscriptions de la session Design dans les tableaux | `chore/1.6.40-inscriptions` | fusionnée |
| 1.6.41 | Design | Boutons segmentés selon Material 3 (rail neutre, pastilles ajustées au texte, actif comme l'onglet de l'en-tête) : filtre Note des Offres et période du Bilan ; règle §4 | `fix/1.6.41-segmentes` | fusionnée |
| 1.6.42 | Dépôt | Tableaux à jour (1.6.40 fusionnée, 1.6.41 précisée) | `chore/1.6.42-tableaux` | fusionnée |
| 1.6.43 | Pages | « jour de repos » partout, tests qui dépendent de la date, baisse des tests 478 → 463 expliquée | `fix/1.6.43-jour-de-repos` | fusionnée (#353) |
| 1.6.44 | Dépôt | Chaque session tient ses lignes ; inscription de la session Pages | `chore/1.6.44-inscriptions` | PR ouverte |
| 1.6.45 | Pages | Passe de concision des textes de l'interface | `fix/1.6.45-concision` | prévu (tableau avant/après à valider) |
| 1.6.46 | Design | Revue de la plateforme : en-tête sans bulle (soulignement, boutons ronds), Offre du jour en pile, « + Ajouter » des Offres, filtre Note en ligne, focus de la recherche ; Figma d'abord, code de l'en-tête | `design/1.6.46-revue` | fusionnée (#356) |
| 1.6.47 | Pages | Revue 1.6.46, Offres : un seul « + Ajouter » (Ajouter une offre, Postuler spontanément), la Note en ligne comme Statut et Tri, la marge de la colonne des filtres | `fix/1.6.47-offres` | fusionnée (#359) |
| 1.6.48 | Design | Règle §3 : la bande d'action | `docs/1.6.48-bande-action` | fusionnée (#357) |
| 1.6.49 | Design | Composant « Bande d'action » dans le code | `feat/1.6.49-bande-action` | fusionnée (#358) |
| 1.6.50 | Pages | Revue 1.6.46 : l'écran de tri des offres du jour (`/aujourdhui/tri`), la bande d'action d'Offres « Commencer le tri » | `feat/1.6.50-tri` | fusionnée (#360) |
| 1.6.51 | Pages | Revue 1.6.46 : Aujourd'hui en une colonne (la bande « Tri du jour. », « À faire aujourd'hui. », « Mois ORP. », « À retenir. ») | `feat/1.6.51-aujourdhui` | fusionnée (#361) |
| 1.6.52 | Pages | Aujourd'hui, Mois ORP : sans la tuile du visage, le mois plus grand (choix de Kevin) | `fix/1.6.52-mois-orp` | fusionnée (#362) |
| 1.6.53 | Pages | Offres sans bande d'action (décision de Kevin : la liste est déjà la tâche, le nombre est dans l'onglet et la conclusion) | `fix/1.6.53-offres-sans-bande` | fusionnée (#363) |
| 1.6.54 | Design | Règle §3 : la bande ne répète jamais le contenu de la page (pas de bande sur Offres) | `docs/1.6.54-bande-sans-repetition` | fusionnée (#364) |
| 1.6.55 | Pages | Offres : barre d'outils (recherche, « Filtrer » en panneau ou feuille, « + Ajouter »), filtres actifs en pastilles, sans colonne de filtres | `feat/1.6.55-barre-outils` | PR ouverte |
| 1.6.56 | Pages | Test du retour d'entretien indépendant de la date du jour (signalé par Design) | `fix/1.6.56-test-retour` | fusionnée (#365) |
| 1.6.57 | Pages | Offres, feuille « Filtres » sur téléphone selon la planche : voile à 40 %, coins du haut à 16 px | `fix/1.6.57-feuille-filtres` | fusionnée (#367) |
| 1.6.58 | Pages | Série de Kevin, point 1 : sélection des onglets (pastille teintée dans l'en-tête, indicateur actif de Material 3 sur la barre du bas), en-tête confié par Design | `feat/1.6.58-onglets` | PR ouverte |
| 1.6.59 | Design | Série du 27.10 inscrite au tableau (points 1 à 7) | `docs/1.6.58-serie-27-10` | fusionnée (#368) |
| 1.6.60 | Design | Barre d'onglets du téléphone : `--tabbar-h` de 3,6 à 4 rem, de l'air au-dessus de la pastille | `fix/1.6.60-tabbar-h` | fusionnée (#370) |
| 1.6.61 | Design | Repliable : icône et phrase facultatives (pour le Bilan, série du 27.10 point 4) | `feat/1.6.61-repliable` | fusionnée (#371) |
| 1.6.62 | Pages | Série du 27.10, points 3 et 4 : le Bilan selon la planche « 3 et 4. Bilan » (conclusion exacte, bande du meilleur site, période en pastilles, quatre repliables chiffrés et « Pour l'ORP », mois d'avant la première activité masqués) | `feat/1.6.62-bilan` | PR ouverte |
| 1.6.63 | Design | Repliable ouvert et survolé : la phrase en --text, contraste 4,5:1 (signalé par Pages) | `fix/1.6.63-repliable-contraste` | PR ouverte |
