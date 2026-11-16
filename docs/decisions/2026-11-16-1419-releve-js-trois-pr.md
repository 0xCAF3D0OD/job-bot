## Un seul relèvement du JS pour #764, #770 et #771, puis l'issue « Budget JS » (Kevin, 16.11.2026, 14 h 19)

- Mesures sur main du 16.11 (js-total 428 054 octets gzip, limite 428 780) : #764 ajoute 715 octets (AlertSiteSteps, code jobup), #770 1 544 (PreparationView, recherche dans le CV), #771 916 (OffersView, agences de placement). Les trois ensemble : 431 252 octets.
- Le chargement à la demande des trois composants a été mesuré : js-total + 1 840 octets, js-candidatures − 250 seulement. Il n'est pas retenu.
- Décision : js-total passe de 428 780 à 431 500 octets, une seule fois, dans une petite PR à part, pour les trois PR ensemble. Pas de découpage.
- Après la fusion de #764, #770 et #771 : ouvrir une issue « Budget JS » qui (1) mesure le JS chargé au premier écran de chaque page (gzip), (2) propose une limite par page en plus de js-total, (3) liste les 5 plus gros modules avec des pistes d'allègement chiffrées.
- Plus aucun relèvement de css-total ou de js-total sans passer par cette issue.
