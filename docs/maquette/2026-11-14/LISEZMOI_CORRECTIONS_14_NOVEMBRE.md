# jobA1, corrections de maquette du 14 novembre

Les 63 planches de `maquettes/` remplacent les fichiers de même nom dans `docs/mobile/maquettes/`. Maquette en ligne : version `1794669238-979f`. Planches retirées par Kevin le 14 novembre : `Animations`, `AujourdhuiOrdinateurReposD`, `RelierFermee`, `RelierLienInvalide`, `RelierPasTesteur` (à supprimer du dépôt).

## 1. Cartes d'offres (Offres, téléphone et ordinateur)

- L'anneau de note est en haut à droite de la carte, sans libellé (« Proche », « À creuser » disparaissent de la liste). Le libellé reste dans la fiche de l'offre et dans le livre.
- Même marge en haut et à droite : 20 px sur téléphone, 16 px sur ordinateur (la carte ordinateur passe de `padding: 0 18px` à `padding: 16px`, hauteur minimale 104 px inchangée).
- Sur ordinateur, l'anneau a les mêmes séparations blanches en quatre quarts que sur téléphone (en sombre : couleur du fond de la carte).
- Le nom (`aria-label`) de l'anneau garde le libellé : « Proche : 92 sur 100 ».
- Les séparations en quatre quarts sont sur tous les anneaux de l'appli, quelle que soit leur taille : listes, fiche de l'offre, panneau Compatibilité, en-tête de Préparer, Relance. Couleur du fond derrière l'anneau (blanc en clair, fond de la carte en sombre).

## 2. Cartes de candidatures envoyées

- Le statut (« Sans réponse », « Refus », « Envoyée », « Entretien ») est centré verticalement sur toute la hauteur de la carte (titre + puce), icône au-dessus du texte, sur téléphone comme sur ordinateur. Structure : logo, colonne (titre, entreprise, puce), statut ; la puce est dans la colonne du titre, pas sur une ligne à part.
- Une seule puce sous le titre (« Envoyée il y a 12 jours »).

## 3. Filtres de la vue Envoyées = ceux de la vue Offres

- Téléphone : un champ « Poste, entreprise, lieu », l'icône de filtres dans l'en-tête ouvre la feuille Filtres. Plus de puces « Toutes, À relancer, Sans réponse, Entretien » : elles passent dans la feuille Filtres.
- Ordinateur : la même rangée que la vue Offres (« Filtrer par titre ou entreprise » + « Plus de filtres »), sous la carte Objectif ORP. Plus de « Trier : à relancer d'abord » ni de puces.

## 4. Feuilles et panneaux (menus de haut en bas)

Référence : le panneau « Rendez-vous ORP ». Règle appliquée à toutes les feuilles téléphone et à tous les panneaux ordinateur :
- titre 20 px, graisse 800 ;
- croix de fermeture ronde de 44 px, bordure 1,5 px `#C9C5BA`, fond blanc (sombre : bordure `#38322B`, fond `#221E1A`), 20 px du bord droit ;
- libellés de section en capitales, 13 px, graisse 700, `#596070`, espacement .05em ;
- bouton principal en pilule de 52 px en bas : pleine largeur quand il est seul ; quand un lien secondaire (« Plus tard », « Tout effacer ») l'accompagne sur la même ligne, le bouton prend la largeur de son texte (`padding: 0 24px`), les deux sont alignés à droite avec 24 px d'espace entre eux (Alerte jobup, Filtres) ;
- sur ordinateur, le panneau est une carte flottante, jamais collée au bord : 16 px du haut, de la droite et du bas, coins de 24 px partout, ombre `0 12px 32px rgba(27,31,42,.2)` (sombre : bordure 1 px `#38322B`, ombre `rgba(0,0,0,.45)`). Les volets ancrés à un bouton (Ajouter, Nouveau rendez-vous) gardent 420 px et commencent à 84 px du haut, même carte.
Les menus déroulants de l'en-tête (Compte, Notifications) et les listes de réglages ne changent pas.

## 5. Système

- Règle 1 (score) : sans libellé en liste, séparations blanches, marge égale.
- Règle 2 : l'objectif ORP est une barre, jamais un cercle (le « cercle liquide » est retiré).
- Bouton compact : 44 px au minimum.

## 6. Emplacement des boutons et des éléments : mêmes règles sur toutes les pages

Téléphone
- Champ de recherche « Poste, entreprise, lieu » toujours au même endroit : sous l'en-tête Candidatures, au-dessus des onglets Offres / Envoyées / Rendez-vous, sur les trois onglets. La carte Objectif ORP (Envoyées) vient après les onglets.
- L'en-tête Candidatures a toujours le lien « Alertes » et l'icône Filtres (aussi sur Aucune offre, Erreur de connexion, menu d'actions, feuille Filtres).
- Retour : une seule forme, la flèche « ← » de 24 px dans un bouton de 48 px, couleur du texte, puis le titre de la page. Plus de chevron « ‹ » ni de « ‹ nom de la page précédente » en bleu. Détail d'une envoyée : « ← Candidature ».
- Fiche d'offre : mêmes icônes en haut (retour, marque-page, ⋯) et même bouton « Préparer ma candidature » que l'offre soit sûre ou provisoire. Plus d'icône Partager, plus d'étincelle.
- ORP sur téléphone : c'est l'onglet ORP de la page Bilan (titre « Bilan », onglets ORP / Résultats / Formations), plus de page « Suivi ORP » ni de page « Progresser ».
- Compte : les lignes utilisent la flèche ronde, pas le chevron ; même en-tête « Compte » sans logo.

Ordinateur
- Envoyées : la rangée de filtres est exactement celle d'Offres (champ + « Plus de filtres »), sous la carte Objectif ORP. Plus de bouton « Trier », plus de puces de statut, plus de trait bleu reliant la carte au détail (la carte sélectionnée est déjà marquée par sa bordure et son fond).
- Rendez-vous : un seul bouton d'ajout, le « + Ajouter » de l'en-tête (le « + Nouveau rendez-vous » de la colonne disparaît).
- Alertes e-mail : la carte « Ta recherche » a la même action à droite que les lignes du dessous : libellé « Modifier » + flèche ronde de 36 px, bleu `#1A3496`, à 18,5 px du bord de la carte (jamais collée au bord).
- Lien de retour (« ‹ Candidatures », « ‹ Mon profil ») toujours en bleu `#1A3496`.

Les deux
- Réglages : même liste et même ordre des notifications partout : Nouvelles offres, Relances, Objectif ORP, Actualités et formations, E-mail en plus des notifications. Apparence : Clair / Sombre / Auto.

## 7. Espace entre deux boutons voisins

- Deux boutons d'action côte à côte (pilules) : 12 px entre eux, partout. Concerne : barre Écarter / Préparer ma candidature (téléphone), Préparer / Écarter / J'ai déjà postulé (détail d'une offre, ordinateur), Tout effacer / Modifier les filtres, Exporter le formulaire / Ajouter une recherche, Exporter le PDF / Déjà remis, Voir mes candidatures / Préparer la prochaine, Retour à l'accueil / Préparer la première, Retour à l'accueil / Exporter ma feuille ORP, Ouvrir Job-Room / Fermer, Nouvelle conversation / Fermer.
- Ne change pas : onglets, segments et puces de filtres restent à 4 ou 8 px, c'est un seul composant.
- Un lien texte à côté d'un bouton : 24 px (section 4).

## 8. Candidatures sur ordinateur : le détail en cartes (Offres et Envoyées)

Le détail à droite n'est plus une grande carte blanche avec des colonnes et des traits : c'est une colonne de cartes empilées, 16 px entre elles, fond de page entre les cartes. Plus de trait vertical entre la liste et le détail, plus de trait bleu de liaison, plus de texte hors carte. Chaque carte a un seul rôle : titre, état, action, informations.

Envoyées (planches CandidaturesOrdinateurB onglet Envoyées, CandidaturesOrdinateurStatut, RelanceOrdinateurV2)
1. Carte titre : logo, poste, entreprise · lieu, ligne de statut (« Sans réponse · 57 jours », « Déclarée à l'ORP »), menu ⋯.
2. Carte suivi : la frise à 5 étapes seule, pleine largeur, 5 colonnes égales, nœud et libellés centrés dans chaque colonne (plus d'alignement sur le texte du titre).
3. Carte Relance conseillée : en-tête = titre 18/700 + pastille « Message prêt » ; ligne « À » (étiquette 13 px grise au-dessus de la valeur 15/700) avec « Changer » à droite ; ligne « Message » avec le texte ; pied = deux pilules de 52 px, « Copier et ouvrir LinkedIn » pleine et « Modifier le message » bordée, 12 px entre elles ; dernière ligne = pastille « Après l'envoi » + « Statut Relancé, prochaine relance proposée dans 10 jours ». La phrase « Court et poli… » est supprimée.
4. Carte Documents et contacts : deux colonnes « Ce que tu as envoyé » / « Trouver un contact » séparées par un filet de 1 px, mêmes lignes qu'avant (titre 15/700, sous-titre 13 px gris, icône à droite), puis une ligne « Historique » (nombre d'étapes et dernière étape) avec chevron.

Offres (CandidaturesOrdinateurB onglet Offres, Statut, Relance, Ajouter, Spontanée)
1. Carte titre : logo, poste, entreprise · lieu, puces (contrat, reçue hier), menu ⋯.
2. Carte note : anneau 64 px avec ses séparations, « À creuser » + pastille « Provisoire », phrase d'explication, ligne « Voir la compatibilité » avec chevron.
3. Carte Candidature : titre ; ligne « Annonce illisible / Indeed bloque la lecture » avec le bouton « Donner l'annonce » à droite (le dépliant ne change pas) ; ligne « Le poste » (étiquette + texte) ; pied = « Préparer ma candidature » pleine 52 px, « Écarter » et « J'ai déjà postulé » bordées, 12 px entre elles.
4. Carte L'offre en bref : Lieu, Contrat, Taux d'activité, Reçue en deux colonnes (étiquette 13 px grise, valeur 15/700), dernière ligne « Voir l'annonce sur Indeed » avec l'icône externe à droite.

Les lignes à étiquette (étiquette grise 13 px au-dessus d'une valeur 15/700, filet de 1 px entre les lignes) sont le même composant partout dans ces cartes.

## 9. Note, puces et marges de lecture

- En-tête de Préparer (lettre, CV, postuler) : l'anneau de compatibilité seul, 48 px, cliquable (ouvre le volet Compatibilité). Plus de libellé « Proche de ton profil » ni de lien « Voir la compatibilité » à côté : l'information est sur la carte de l'offre, la page d'avant.
- Détail d'une offre (ordinateur) : les puces (contrat, reçue hier) sont à 14 px sous l'entreprise et alignées sur le texte (72 px, après le logo). La carte note tient sur une ligne de 76 px : anneau 48 px, libellé (« À creuser ») + pastille (« Provisoire »), « Voir la compatibilité › » à droite. La phrase « Calculée sur l'extrait de l'alerte… » va dans le volet Compatibilité.
- Lignes à deux textes (étiquette + valeur, ou titre + sous-titre) dans une carte : 12 px en haut et en bas, hauteur minimale 64 px. Avant : 6 à 8 px. Concerne : À recopier sur le formulaire (Postuler), Pour l'ORP (panneau), Premiers pas étape 2, Ta candidature (Préparer), feuilles Ce que tu as envoyé / Trouver un contact, et les cartes Relance, Documents, Contacts, L'offre en bref. Les menus (compte, notifications) restent à 56 px, c'est un menu, pas une liste de lecture.
- Trier (livre) : 12 px sous la dernière ligne du verdict.
