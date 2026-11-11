# Prompt Claude Code : icônes du Compte, bas de liste, accueil en bandes empilées (10 novembre 2026, fin de soirée)

À ajouter par-dessus `docs/mobile/` (fichiers modifiés seulement). Prime sur les paquets précédents pour ces points.

## PR 34. Icônes dans le Compte (téléphone, et menu « Mon compte » sur ordinateur)
Maquettes : `Compte`, `CompteSombre`.
- Une icône contour 24 px à gauche de chaque ligne (trait 2 px, couleur #3D4250, sombre #C7BFB3), toujours avec le texte, `aria-hidden="true"`.
- Formations = chapeau de diplômé, CV et lettres = document, Critères = loupe, Notifications = cloche, Apparence = lune, Mes données = base de données, Charte IA = bouclier avec coche, Aide = point d’interrogation, Objectif ORP et sites = drapeau, Alertes e-mail = enveloppe. La ligne du profil garde l’avatar.

## PR 35. Bas de la liste des offres (téléphone)
Maquettes : `Candidatures`, `CandidaturesSombre`, capture `etats/*--bas-de-liste.png`.
- Remplacer « Afficher plus (367) » par un bouton contour pleine largeur « Afficher 20 offres de plus · 367 en tout ».
- Puis un groupe « AUTRES OFFRES » (même ligne que le Compte, cercle flèche gris) : « Loin de ton profil · n offres, notées plus bas », « Expirées · n offres, pour mémoire », « Postuler spontanément · À une entreprise sans offre publiée ».
- 24 px de marge sous le dernier élément : rien ne passe sous la barre de navigation.
- Haut de la liste : la première carte ne doit pas passer sous l’en-tête (marge haute = hauteur de l’en-tête collant + 8 px).

## PR 36. Accueil : bandes qui s’empilent au défilement (téléphone)
Maquettes : `AccueilSmile`, `AccueilSombre`, animation `etats/AccueilSmile--bandes-empilees-animation.gif`.
- Bande « ORP » : `position: sticky; top: 0`. Bande « Offres » : `position: sticky; top: 16px` + ombre `0 -10px 24px rgba(27,31,42,.10)`. Bande « À faire » : non collante, passe par-dessus.
- Une bande collante ne dépasse jamais la hauteur de l’écran (sinon elle n’est pas collante).
- Toucher le bord visible d’une bande empilée fait défiler jusqu’à elle.
- `prefers-reduced-motion: reduce` : pas d’empilement (défilement normal).
- Focus clavier : `scroll-margin-top` sur les liens et boutons pour qu’un élément focalisé ne soit jamais caché sous une bande (WCAG 2.4.11).

## Vérifications
- Téléphone 360 et 390 px, clair et sombre ; ordinateur 1440 px pour le menu du compte.
- `outils/audit-grille.js` : 0 écart sur `Compte`, `Candidatures`, `AccueilSmile`.
- Tester l’accueil avec « réduire les animations » activé, et au clavier (Tab) jusqu’en bas de page.
