## Trier ordinateur, l'éventail remplace le livre (Kevin, 15.11.2026, 11 h 44)

- Chaque carte est un bouton (`aria-pressed` faux à l'endroit, vrai au dos), nommé « poste, entreprise. notes entières. Retourner pour voir l'extrait ». Focus : contour de 2 px `--primary-graphic`, décalé de 3 px, qui suit l'arrondi de la carte.
- Clavier : ← Écarter et → Garder inchangés ; Tab et Maj+Tab passent d'une carte à l'autre ; Entrée ou Espace retourne la carte ; Entrée sur « Voir l'annonce complète » ouvre l'annonce sans retourner la carte (le lien est à côté du bouton, pas dedans).
- Mouvement réduit : ni étalement animé ni rotation 3D, un fondu de 150 ms au plus.
- « Écarter » affiche « Offre écartée » et « Annuler », le même bandeau et la même durée que « Garder ».
- Badge « Gardée » : le style de la puce de la liste Candidatures, icône signet orange #F2853A ; fond et texte `--peach-soft` / `--peach-text`.
- Signet : gardé sur la carte du téléphone ; fichier, composant et classes renommés « signet » (SignetMark). L'écran « Rien à trier » est refait à part (#735).
- La ligne des touches ← → sous le compteur est retirée (Kevin, 15.11, 12 h 40) : les boutons portent `aria-keyshortcuts` et le titre « Écarter (←) » / « Garder (→) ».
