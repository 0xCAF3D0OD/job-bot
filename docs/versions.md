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
| 1.6.40 | Dépôt | Inscriptions de la session Design dans les tableaux | `chore/1.6.40-inscriptions` | PR ouverte |
| 1.6.41 | Design | Boutons segmentés au style de l'en-tête (Bilan, Note des Offres) et règle §4 | `fix/1.6.41-segmentes` | prévu |
