# jobA1, corrections de maquette du 13 novembre (soir), lot complet

Ce lot remplace le premier lot de corrections du même soir. Il complète le paquet de référence du 13 novembre : les 38 planches de `maquettes/` remplacent les fichiers de même nom dans `docs/mobile/maquettes/`, et `OnboardingOrdinateurAlerte` est nouvelle. Maquette en ligne : version `1794595537-1f2b`.

Le suffixe `--état` d'une capture désigne un état de la planche.

## 1. Premiers pas : nouvelle étape « Alerte »

- Ordre : CV, critères, **alerte**, premières offres.
- Téléphone (`OnboardingC`, étape 3) : la barre passe de 4 à 5 segments. Titre « Chercher » barré, « Recevoir. » à la main, comme les autres étapes. Phrase : « Crée une alerte sur jobup : ses offres arrivent ici chaque matin, déjà triées. Environ 2 minutes. » Puis le rappel de la recherche et les trois étapes numérotées du panneau Alertes. Étape 2 sur téléphone : « Copie-la, puis colle-la dans le champ e-mail de l’alerte. »
- Pied : bouton principal « J’ai créé l’alerte », bouton texte « Plus tard » dessous (44 px de haut). Les deux mènent à l'étape suivante.
- Le bouton de l'étape des critères devient « Continuer » (« Voir mes offres » avant).
- Ordinateur (`OnboardingOrdinateurAlerte`) : « Étape 3 sur 4 », surtitre « Tes prochaines offres », titre « Une alerte, et elles arrivent seules », les trois étapes dans une carte, personnage Orange à droite (260 px). Pied : « Retour » à gauche, « Plus tard » et « J’ai créé l’alerte » à droite.
- Les huit autres planches `OnboardingOrdinateur*` passent de « sur 3 » à « sur 4 », avec 4 points.
- Un seul site dans l'étape : jobup. Si la personne choisit « Plus tard », la carte « Premiers pas » d'Aujourd'hui garde l'étape ouverte.
- Le compteur « Recherches par mois » des premiers pas va de 1 à 99.

## 2. Alertes sur ordinateur

- `AlertesOrdinateurVide` : l'illustration de l'ancienne série est retirée. Le personnage Orange (112 px de haut) est à gauche du titre. 24 px sous ce bloc, puis la carte « Ta recherche ».
- `AlertesOrdinateurSite` : même page derrière, panneau à 440 px.
- Bouton « Copier l’adresse » : 44 × 44 px.

## 3. Gris #8C8478 interdit en texte

- « Pas encore notée » et le mois écrit dans la petite icône de calendrier : `#596070` en clair, `#ABA398` en sombre.
- `#8C8478` reste permis pour les bordures et les traits d'icônes.

## 4. Ma candidature sur téléphone

- État « lettre » : ligne « Moderne · Français » et lien « Changer » entre les onglets et la légende. C'est la ligne déjà codée.

## 5. Rendez-vous, feuille « Ce qui a été convenu »

- `RendezVous` et `RendezVousSombre`, état `noter` : les deux champs de texte suivent le champ commun (56 px, rayon 12 px, bordure 1,5 px, libellé flottant de 12 px gras). Sous chaque champ, une aide de 13 px : « Ex. : cours, stage, programme » et « Ex. : ce que ton conseiller t’a demandé ».
- Un filet, puis le titre centré « Prochain rendez-vous », puis « Date » et « Heure ». La phrase « jobA1 le met dans tes Rendez-vous. » est centrée.
- C'est un alignement de la maquette sur le code. Rien à recoder si l'écran est déjà ainsi.

## 6. Objectif du mois atteint, sur Accueil et Aujourd'hui

- Nouvel état `atteint` dans `AccueilV2`, `AujourdhuiOrdinateurV2` et leurs versions sombres.
- Il n'y a plus de carte à part avec une image de l'ancienne série. Trois choses changent :
  - le titre manuscrit : « Objectif du mois atteint, » en vert (`#17734A`, `#62D497` en sombre), « la suite est en plus » en bleu ; dessous : « Tes 10 recherches de novembre sont faites. Ce que tu envoies maintenant compte en plus. » ;
  - la barre ORP : « 10 sur 10 », barre pleine verte, « Objectif atteint » (état déjà décrit dans `BarreOrpEtats`) ;
  - « À faire » ne contient plus « Envoyer N candidatures ».
- L'écran plein « C’est fait ! » (`ObjectifAtteint`) reste : il s'affiche au moment où l'objectif est atteint. Cet état est ce qu'on voit ensuite en revenant sur Aujourd'hui.

## 7. Notifications, « Tout est lu »

- `Notifications` et `NotificationsSombre` : le personnage de l'ancien kit est remplacé par le Sourire (140 px de haut). En sombre, il porte un liseré clair (`drop-shadow(0 0 1px #F3EEE6)` deux fois).

## 8. Adresse de l'entreprise manquante, sur l'écran de fin

- Nouvel état `finadresse` dans `MaCandidatureV2` (et sombre), et état `adr` dans `CandidatureEnvoyeeOrdinateur`.
- Une ligne de plus sous « Relance prévue » : icône d'épingle brune, « Il manque l’adresse de l’entreprise », « Il la faut pour ton suivi ORP », lien « Ajouter » à droite (zone de 44 px).
- La ligne n'apparaît que si l'adresse manque. « Ajouter » ouvre le champ d'adresse existant de la fiche entreprise. Jamais bloquant.

## 9. Surlignage en mode sombre

- Le texte d'un passage surligné hérite de la couleur du texte (`color: inherit`) sur le fond `#5C4A14`. Sans cela, le navigateur met du noir (2,4:1).

## Pas dans ce lot : il faut d'abord une capture de l'écran actuel

- La ligne d'une alerte non reconnue dans « Alertes reçues ».
- La ligne du certificat dans « À joindre » (Postuler, ordinateur).
