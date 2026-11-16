## Un seul relèvement du CSS pour #764, #770 et #771 (Kevin, 16.11.2026, 14 h 08)

- Avant ces trois PR, un allègement à part (#777) : 47 groupes de règles identiques de `style.css` réunis, −189 octets gzip, 138 captures sans un pixel d'écart. L'objectif de 470 octets n'est pas atteignable par regroupement (plafond mesuré ≈ 390 octets).
- Mesures sur main du 16.11 : #764 ajoute 413 octets de CSS, #770 397, #771 168. Les trois avec #777 : css-total 119 403 octets.
- Décision : css-total passe de 118 780 à 119 450 octets, une seule fois, dans #777, pour les trois PR ensemble. Pas de relèvement PR par PR.
- #770 garde le contour du résultat courant (sans lui, seule la couleur distingue le résultat courant, WCAG 1.4.1).
- JS : pas de relèvement de js-total sans que Kevin ait vu les chiffres. Avant de fusionner la troisième PR, mesurer l'apport JS de chacune et proposer un découpage (chargement à la demande des parties absentes du premier écran).
