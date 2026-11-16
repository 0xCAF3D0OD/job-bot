## Préparer : l'étape CV chargée à son ouverture (Kevin, 17.11.2026, 0 h 29)

- L'étape CV de Préparer se charge à son ouverture. Elle est préchargée au survol ou au focus de l'onglet « CV », sinon quand le navigateur est au repos (`requestIdleCallback`).
- Si le chargement dépasse 300 ms, un squelette de l'onglet s'affiche (les blocs de chargement communs), jamais un écran vide.
- Le gain réel est mesuré et donné dans la PR.
- Candidatures prend 1,4 Ko de JS depuis la #816 (les panneaux de Préparer y deviennent des blocs séparés) : on le laisse, sans PR de compensation, puisque la page reste 7,8 Ko sous sa limite.
