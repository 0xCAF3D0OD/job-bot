# Une décision, un fichier

Chaque décision de Kevin a son propre fichier ici, `AAAA-MM-JJ-HHMM-sujet.md` : la date, l'heure de la décision si
on la connaît (`AAAA-MM-JJ-sujet.md` sinon), puis le sujet en minuscules, chiffres et tirets. Par exemple,
`docs/decisions/2026-11-15-1907-bandeau-peche.md` :

```
## Bandeau pêche (Kevin, 15.11.2026, 19 h 07)

- Bandeau : pêche partout (#F3B08A, la teinte du PDF et de la planche PreparerMiseEnPage).
```

- La première ligne est un titre `## …`, la suite est le texte de la décision : une liste, un tableau
  `| Date | Décision | Remplace |` ou des phrases, comme on veut.
- Une nouvelle décision qui en remplace une ancienne a son propre fichier et le dit ; l'ancien fichier ne change pas.
- Une précision donnée plus tard par Kevin sur la même décision peut s'ajouter à son fichier, avec sa date.

Sur main, après chaque fusion, l'action `decisions.yml` (`scripts/decisions.py`) assemble `docs/mobile/DECISIONS.md`,
trié par date puis par heure (une décision sans heure passe en tête de sa journée). Deux PR ne touchent donc jamais
le même fichier, et il n'y a plus de conflit sur la fin de DECISIONS.md.

Ne modifie pas `docs/mobile/DECISIONS.md` (la CI le refuse). En local : `make decisions` pour voir l'assemblage,
`make changelog-check` pour vérifier les noms et les titres.
