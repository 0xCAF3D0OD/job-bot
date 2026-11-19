## Barre du bas du téléphone, la même partout (Kevin, 19.11.2026, 12 h 58)

D'après la barre de la planche Offre, pour toutes les barres du bas d'action du téléphone (composant `BottomBar`) :
- Une seule ligne, padding 12 px 16 px, plus la zone de sécurité du bas.
- Fond = couleur de la page (#F7F5F0, sombre #171411), trait de 1 px en haut (#E5E2D9, sombre #3A342D).
- À gauche, au plus une action secondaire : bouton à contour, 48 px de haut, largeur au texte.
- À droite, l'action principale : bouton plein, 48 px de haut, qui prend le reste de la largeur (flex: 1), écart de 10 px.
- Précision du 19.11, 13 h 54 : l'écart passe à 12 px, comme la planche Offre (10 px sortait de la grille de 4 et
  audit-grille le refusait).
- Plus de lien texte centré sous le bouton principal, ni d'espace vide en dessous.
- Premier écran : Ma candidature › Postuler (« J'ai déjà postulé » + « Ouvrir l'annonce ↗ »).
