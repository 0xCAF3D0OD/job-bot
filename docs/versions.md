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
| 1.6.39 | Design | Règles §6 : le mouvement (micro-animations) | `docs/regles-6-fondu` | prévu (texte en attente de validation par Kevin) |
| 1.6.40 | Dépôt | Inscriptions de la session Design dans les tableaux | `chore/1.6.40-inscriptions` | fusionnée |
| 1.6.41 | Design | Boutons segmentés selon Material 3 (rail neutre, pastilles ajustées au texte, actif comme l'onglet de l'en-tête) : filtre Note des Offres et période du Bilan ; règle §4 | `fix/1.6.41-segmentes` | PR ouverte (#351) |
| 1.6.42 | Dépôt | Tableaux à jour (1.6.40 fusionnée, 1.6.41 précisée) | `chore/1.6.42-tableaux` | fusionnée |
| 1.6.43 | Pages | « jour de repos » partout, tests qui dépendent de la date, baisse des tests 478 → 463 expliquée | `fix/1.6.43-jour-de-repos` | en cours |
| 1.6.44 | Dépôt | Chaque session tient ses lignes ; inscription de la session Pages | `chore/1.6.44-inscriptions` | PR ouverte |
