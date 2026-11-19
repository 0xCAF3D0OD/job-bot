## Sélection multiple des offres (Kevin, 19.11.2026, 13 h 29)

Planches §72q (planches_72l_72q.zip) : CandidaturesSelection, CandidaturesOrdinateurSelection (+Sombre), Candidatures et CandidaturesOrdinateurAucuneOuverte (+Sombre) pour l'entrée.

- Entrée : lien « Sélectionner » (14 px gras bleu, zone de 44 px) à droite du premier titre de section de la liste Offres. Pas de bouton de plus dans l'en-tête.
- En-tête : croix ronde « Quitter la sélection » + « N sélectionnées » ; dessous, la pastille-bouton « Toutes les expirées · N » (aria-pressed) qui coche ou décoche d'un coup les offres expirées ou retirées, masquée s'il n'y en a aucune.
- Cartes : la case à cocher (24 px, zone de 44) remplace le logo ; toute la carte est cliquable (role="checkbox", aria-checked) ; cochée : bordure bleue 2 px et fond #F3F5FD (sombre #232B45 et #7D95FF) ; les offres expirées ont la pastille orange « Offre expirée ».
- Actions : téléphone, la barre du bas remplace la navigation, « Annuler » (contour) + « Écarter N offres » (plein, flex 1), désactivé si N = 0 ; ordinateur, les deux boutons sur la ligne d'en-tête de la liste.
- Après « Écarter » : un seul appel serveur, même date d'écart qu'une offre seule ; bandeau « N offres écartées · Annuler » pendant 5 s, puis retour au mode normal.
- Rien ne change hors du mode sélection. Échap ou la croix quitte le mode sans rien écarter.
- Précision du 19.11 (K5 amendée) : les N cartes sortent ensemble, avec un seul bandeau.
- Précision du 19.11 : tous les bandeaux avec « Annuler » ont la même durée, une seule constante (UNDO_MS) ; « N offres écartées » la suit au lieu des 5 s.
