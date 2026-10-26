# Une version, un fichier

Chaque version ajoute ici son fichier `X.Y.Z.md` (par exemple `1.6.37.md`) :

- la première ligne : le contenu de la version, en une phrase (sans « | ») ;
- une ligne facultative `État : …` quand la version n'est pas simplement « livrée ».

Ne modifie pas `CHANGELOG.md` : il est assemblé sur main après chaque fusion (`scripts/changelog.py`, action
`changelog.yml`). En local : `make changelog` pour le voir, `make changelog-check` pour vérifier les fichiers.
Deux PR qui prendraient le même numéro ajouteraient le même fichier : GitHub le signale aussitôt.
