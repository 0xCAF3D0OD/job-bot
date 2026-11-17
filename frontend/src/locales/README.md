# Catalogues de langue (docs/147)

- `pages.json` : pour chaque catalogue, les routes qui le chargent (`*` = toutes) et les fichiers dont il contient
  les textes. `commun` : les composants de l'application (barre du bas, en-tête, messages), chargé sur toutes les pages.
  Les autres noms sont ceux des pages de `scripts/poids.mjs`.
- `<langue>/<page>.json` : texte français → traduction ; pour un pluriel, la clé est la forme `other` française et la
  valeur les formes de la langue (`{ "one": "…", "other": "…" }`). Variables `{nom}` identiques au français.
- Le français n'a pas de catalogue : c'est le texte du code.
- `make i18n-check` vérifie chaque catalogue (complet, variables, pluriels, pas de « ß », glossaire de docs/i18n/).
