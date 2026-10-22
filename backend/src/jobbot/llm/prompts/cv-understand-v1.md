
## En plus : ce que le CV dit de la recherche (`understood`)

Le document est le CV de la personne, déposé pendant son accueil. En plus des blocs, remplis `understood`, seulement avec ce que le CV dit clairement ; sinon laisse vide (liste vide ou null). N'invente rien, ne devine pas.

- `roles` : 0 à 3 intitulés de postes que la personne vise ou occupe, courts, en français (« Ingénieure DevOps », « Chargée de communication »). Pas de nom d'entreprise.
- `min_rate` : le taux d'activité minimum souhaité, si le CV le dit (« disponible à 80 % » donne 80) ; sinon null.
- `languages` : parmi `allemand`, `italien`, `anglais`, celles que la personne parle à un niveau de travail (B1 ou plus, « courant », « bilingue », « langue maternelle »). Le français n'est pas dans la liste.
- `remote` : `remote` si le CV dit chercher du télétravail ou un poste à distance, `onsite` s'il dit sur place ; sinon null.
