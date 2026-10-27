# Une version, un fichier

Chaque PR dépose ici un fragment **sans numéro**, `<sujet>.md` (minuscules, chiffres et tirets, par exemple
`boutons-segmentes.md`) :

- la première ligne : le contenu de la version, en une phrase (sans « | ») ;
- une ligne facultative `État : …` quand la version n'est pas simplement « livrée » : livrée en partie, en pause,
  ou livrée avec une réserve à connaître.

Par exemple, `changelog.d/collecte-indeed.md` :

```
La collecte des offres d'Indeed, à côté de jobup
État : livrée (analyseur Indeed) ; Job-Room en pause, sans analyseur dédié
```

Sans ligne `État`, la version est « livrée ».

Le numéro est donné à la fusion : sur main, l'action `changelog.yml` (`scripts/changelog.py --number`) renomme chaque
fragment en `X.Y.Z.md`, le numéro suivant dans l'ordre de fusion, puis assemble `CHANGELOG.md`. Deux PR ne prennent
donc jamais le même numéro, et aucune ne touche un fichier partagé.

Ne crée pas de fichier `X.Y.Z.md` (la CI le refuse) et ne modifie pas `CHANGELOG.md`. En local : `make changelog` pour
voir l'assemblage, `make changelog-check` pour vérifier les fichiers.
