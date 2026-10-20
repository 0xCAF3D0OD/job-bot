# 109 — Le menu comme Sphere (version 0.77.5)

> Statut : **validé** le 2026-10-20 : largeur fixe sur ordinateur, l'initiale avec le nom, le plein écran sur téléphone, la barre d'onglets cachée.
> Origine : ta demande du 2026-10-20, captures de Sphere sur téléphone à l'appui : « respecte la référence pour le menu : regarde ce que Sphere fait en mode téléphone. Et sur ordinateur, le menu ne bouge pas vers la gauche, il a la bonne largeur fermé. Dis-moi si le mode ordinateur est bon ou si l'exemple Sphere est mieux. »
> Se construit sur docs/89 (la capsule) et docs/91 (la capsule qui se déroule).

## Ce que fait Sphere

### Sur téléphone (tes captures)

- **L'en-tête ne bouge jamais** : le logo à gauche, la capsule à droite (☰ · compte · langue), à la même place, ouverte ou fermée.
- **☰ devient ✕** et **tout l'écran sous l'en-tête devient le menu** : de grands liens en gras (1,8 rem environ), l'un sous l'autre, alignés sur le logo ; dessous, une rangée de cartes. La page derrière disparaît.
- **Le compte** (l'icône de personne) fait de même : sa flèche se retourne, et l'écran montre ses choix (« Candidate Log In », « Create An Account ») en texte simple. Pareil pour la langue.
- **Rien ne s'élargit** : la capsule garde sa taille.

### Sur ordinateur (vérifié sur leur site, 1280 px)

- La capsule (☰ MENU · compte · langue) mesure environ 18 rem, **ouverte comme fermée**.
- Elle se déroule **vers le bas, à sa largeur** : le menu tient dans la colonne de la capsule. Rien ne passe à gauche.

## Ce que fait jobA1 aujourd'hui

- **Ordinateur** : la capsule fermée (cloche · livre · initiale) fait environ 11 rem ; ouverte, elle **s'élargit vers la gauche**, à 15 rem pour le compte et 24 rem pour les alertes (docs/91 §1).
- **Téléphone** : ouverte, elle **s'élargit sur toute la largeur et passe par-dessus le logo** (docs/91, écarts) ; le contenu reste à la taille d'un menu.

## Mon avis sur l'ordinateur

**L'exemple Sphere est mieux.** Une capsule qui change de largeur fait sauter le cadre sous la souris : l'œil perd le point qu'il vient de cliquer, et le titre de la page, à gauche, est poussé ou recouvert. Une largeur fixe, qui ne fait que descendre, se lit comme un tiroir : calme, prévisible.

## La proposition

### 1. Ordinateur : une largeur fixe

- **La capsule a la même largeur, fermée et ouverte** : **20 rem**, ce qu'il faut pour que les alertes restent lisibles (aujourd'hui 24 rem ouvertes ; 20 rem suffisent avec le texte sur deux lignes).
- **Fermée**, les trois zones se partagent cette largeur : la cloche, le livre, puis l'initiale avec son nom (« Kevin ▾ ») pour remplir l'espace sans vide.
- **Ouverte**, elle se déroule vers le bas, à sa largeur, comme aujourd'hui pour la hauteur (350 ms, la courbe de Sphere).

### 2. Téléphone : le menu plein écran

- **L'en-tête ne bouge plus** : le logo à gauche, la capsule fermée à droite (cloche · livre · initiale), à sa taille. Plus d'élargissement par-dessus le logo.
- **Une zone ouverte prend tout l'écran sous l'en-tête**, comme Sphere :
  - **l'initiale** : « Connecté : eliot », puis **en grands liens** (1,6 rem, gras) : Profil, Réglages, Données personnelles ; puis, plus petits, Collecter maintenant, Fermer mon compte, Se déconnecter ;
  - **la cloche** : les alertes, en liste pleine largeur ;
  - **le livre** : l'aperçu de Progresser (actualités, formations en cours), en liste pleine largeur.
- **La flèche de l'initiale se retourne**, la zone ouverte passe en noir ; un second appui, Échap ou un choix referme. La page derrière ne défile pas tant que le menu est ouvert.
- **La barre d'onglets du bas** (Aujourd'hui, Candidatures) reste : c'est notre ☰. Elle est cachée tant que le menu plein écran est ouvert, pour qu'il ait toute la hauteur.

### 3. Ce qui ne change pas

- Les zones, leurs noms pour les lecteurs d'écran, le clavier (flèches, Échap, focus rendu à la zone).
- Le déroulé de 350 ms ; avec « réduire les animations », tout s'ouvre d'un coup.
- Les menus « ⋯ ».

## Écarts

- **La largeur fixe** est posée par `HeaderCapsule` : 20 rem sur ordinateur, fermée comme ouverte ; seule la hauteur s'anime. Les alertes (24 rem avant) et l'aperçu de Progresser (26 rem avant) tiennent dans 20 rem, le texte passe sur deux lignes.
- **La cloche sur téléphone** s'ouvrait sous la barre et poussait la page (retour du 2026-10-15) ; elle s'ouvre maintenant en plein écran, comme le compte et le livre. L'emplacement `#bell-drop` disparaît.
- **Le plein écran** commence 0,75 rem sous la capsule, mesuré à l'ouverture ; la page derrière ne défile plus (`capsule-sheet` sur la page), la barre d'onglets et le bouton de l'Assistant se cachent.
- **Le compte en grand** : Profil, Réglages, Données personnelles (et Diagnostic pour l'exploitant) en 1,6 rem gras, sans icône ; Collecter maintenant, Fermer mon compte et Se déconnecter restent à 1 rem, avec leur icône, sous un espace.
- **« Fermer mon compte »** ne se colore plus comme une page en cours quand on est dans les Réglages (son lien y mène).
- **Collecter maintenant et Se déconnecter** prennent la graisse des autres lignes du menu ; le filet au-dessus de Se déconnecter n'a plus de bouts arrondis.

## Vérifié

- Tests : la capsule à la même largeur fermée et ouverte (ordinateur) ; sur téléphone, le plein écran pour la cloche et le compte, la page immobile, et tout qui se referme ; tests complets, lint, typecheck.
- Captures avec Playwright, les vrais composants (cloche, livre, compte) dans un en-tête comme celui de l'application : à 414 px, fermé, compte ouvert, alertes ouvertes ; à 1280 px, compte ouvert. Largeur de la page mesurée : 414 et 1280 px, rien ne dépasse.

## Décisions (2026-10-20)

Tes quatre réponses : largeur fixe (20 rem) ; l'initiale avec le nom ; le plein écran sur téléphone ; la barre d'onglets cachée pendant que le menu est ouvert.

### Les questions posées

1. **Ordinateur** : une capsule de largeur fixe (20 rem), ouverte comme fermée, qui ne fait que descendre ?
2. **Ordinateur, fermée** : l'initiale accompagnée du nom (« Kevin ▾ ») pour remplir la largeur, ou les trois zones simplement espacées ?
3. **Téléphone** : le menu plein écran sous l'en-tête, avec les trois pages du compte en grands liens comme Sphere ?
4. **Téléphone** : la barre d'onglets du bas cachée pendant que le menu est ouvert ?
