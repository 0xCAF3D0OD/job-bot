## Adresse du registre copiée seulement dans un champ vide (Kevin, 17.11.2026, 22 h 05)

- Quand le registre IDE connaît déjà l'entreprise (cache), « Chercher l'adresse » copie son adresse dans l'offre, seulement si le champ adresse est vide.
- Une adresse saisie par l'utilisateur, ou trouvée ailleurs, n'est jamais écrasée.
- Un test couvre les deux cas : champ vide, adresse copiée ; champ rempli, adresse inchangée.
- Origine : audit du 17.11, K6 (la fiche disait « Adresse trouvée » et restait « Non renseignée »).
