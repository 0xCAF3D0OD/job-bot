# Les langues de jobA1

Cadrage : docs/147-langues-plateforme.md. Un glossaire par langue (`glossaire-<code>.md`), figé : un terme ne change que
par une décision de Kevin dans docs/decisions/, puis dans tous les écrans à la fois.

Chaque tableau a les colonnes `Id | Français | Terme retenu | Statut | Source`. L'identifiant est le même dans toutes
les langues ; `make i18n-check` (PR 1) s'en sert pour vérifier qu'une traduction emploie le terme retenu.

## Pour la personne qui relit

- Relire en priorité les lignes « proposition, à relire » et « usage administratif, à relire ».
- Proposer une correction dans la colonne « Terme retenu » ; Kevin la valide, puis le statut passe à « relu ».
- Une langue n'est activée dans jobA1 qu'une fois relue en entier (glossaire et écrans).

## Question ouverte pour Kevin

Le sigle de l'office en anglais, albanais, portugais et espagnol. Le SECO écrit en anglais « regional employment
centre (RAV) ». Mais une personne qui lit jobA1 en portugais à Lausanne reçoit des courriers de l'« ORP ». Proposition :
dans ces quatre langues, le sigle suit le canton du profil (ORP en Suisse romande, RAV en Suisse alémanique, URC au
Tessin), avec le nom traduit à côté la première fois ; ORP si le canton n'est pas connu. En allemand et en italien,
RAV et URC partout, comme le SECO.
