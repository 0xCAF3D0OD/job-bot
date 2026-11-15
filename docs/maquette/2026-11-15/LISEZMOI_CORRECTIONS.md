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
- Réglages : même liste et même ordre des notifications partout : Nouvelles offres, Relances, Objectif ORP, E-mail en plus des notifications (4 interrupteurs, pas de réglage pour un envoi qui n'existe pas). Apparence : Clair / Sombre / Auto.

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

## 10. Filtres des envoyées

- Le tri « À relancer d'abord » et les puces de statut, retirés de la rangée Envoyées, vivent dans le volet Filtres de cet onglet : Statut (Toutes · 26, Sans réponse · 22, Réponse reçue · 3, Entretien · 1) et Trier (À relancer d'abord par défaut, Plus récentes d'abord). Pied : « Tout effacer » et « Afficher 26 candidatures ».
- Ordinateur : même volet que les filtres d'Offres, à la place de la liste (CandidaturesOrdinateurB, état tab=en + menu=filtres).
- Téléphone : feuille du bas FiltresEnvoyees.dc.html, même construction que Filtres.dc.html. Le fond de Filtres.dc.html est mis à jour (cartes sans libellé sous l'anneau, lien Alertes).
- Les groupes « À relancer » / « Cette semaine » de la liste ne changent pas.

## 11. Candidatures ordinateur : liaison carte → détail (flèche et encoche)

Remplace la partie « détail à droite » de la section 8 pour Offres et Envoyées. Planches : CandidaturesOrdinateurB et BSombre (onglets Offres et Envoyées), Statut, Ajouter, Spontanée. Captures : CandidaturesOrdinateurB(.png, --envoyees.png), BSombre, Liaison-fleche-encoche-zoom.png.

Jetons à créer : trait de liaison (clair #D5D1C7, sombre #4E473E) et fond de carte sélectionnée dans une liste reliée à un détail (clair #EEF1FC, sombre #232B45). Ne pas changer la sélection ailleurs.

Règle de mise en page : liste + détail = zone de détail ouverte reliée par une flèche ; page seule = cartes empilées (inchangé ailleurs).

Liste (colonne de gauche, 532 px)
- Cartes non sélectionnées : 480 px de large, 52 px d'écart avec la zone de détail. Le champ de filtre, « Plus de filtres » et la carte Objectif ORP s'alignent sur ce bord.
- Carte sélectionnée : s'allonge de 28 px vers la droite (margin-right -28 px), fond #EEF1FC (sombre #232B45), contour 2 px #2445C2 (sombre #7D95FF), plus d'ombre.
- Flèche : SVG 22 × 44 px soudé au contour de la carte, centré verticalement, pointe arrondie. Trait 2 px de la couleur du contour, remplissage du fond de la carte (tracé exact dans les planches, attribut data-arrow).
- Barre de recherche et filtres (et Objectif ORP sur Envoyées) : fixes, seules les cartes défilent dessous. Dès que la liste a défilé, ombre légère sous la barre (0 10px 12px -12px rgba(27,31,42,.35)) ; aucune ombre en haut de liste.
- Pastilles qui disent seulement qu'une information manque (« Contrat non précisé ») : retirées des cartes, ordinateur et téléphone (règle portée par le composant carte). L'information reste dans « L'offre en bref ».

Zone de détail (colonne de droite)
- Plus de fond ni de cadre : un trait 1,5 px #D5D1C7 (sombre #4E473E) à gauche et en haut, coin haut gauche arrondi 24 px. À droite, le trait du haut s'efface en dégradé sur 160 px ; il n'y a pas de trait à droite ni en bas.
- Bas : la zone va jusqu'au bas de la fenêtre ; fondu de 72 px vers la couleur du fond de page (comme la lettre dans Préparer), 48 px d'air sous la dernière carte.
- Encoche : creusée dans le trait de gauche, même pente et même arrondi que la flèche, 6 px d'écart constant avec elle (SVG data-notch). Halo bleu très léger côté zone uniquement (#2445C2 à 26 %, flou 5 px ; sombre #7D95FF à 22 %).
- L'encoche se positionne à la hauteur du centre de la flèche de la carte sélectionnée (à recalculer au défilement de la liste et au redimensionnement). Si la carte sélectionnée sort de la partie visible de la liste, l'encoche et la flèche se masquent et le trait redevient droit.
- Le contenu de la zone défile dans la zone ; le trait, l'encoche et le fondu restent fixes.

En-tête (à plat, sans carte, sous le trait du haut)
- Plus de logo (il est sur la carte). Intitulé complet 24/800 et entreprise complète : la carte les tronque, l'en-tête les donne en entier.
- Offres : sous un filet, une seule ligne « À creuser · 60 sur 100 » + pastille « Provisoire » + « Voir la compatibilité › » à droite. La carte Note séparée et le grand anneau sont supprimés. Les puces (contrat, reçue hier) sont supprimées de l'en-tête.
- Sans note : « Pas encore notée » + « Donner l'annonce pour la noter › » au même endroit.
- Envoyées : ligne de statut inchangée (« Sans réponse · 57 jours », « Déclarée à l'ORP »), alignée sur l'intitulé.

Cartes sous l'en-tête
- Offres : Candidature, L'offre en bref. Envoyées : Suivi (frise), Relance conseillée, Documents et contacts. Cartes blanches posées sur le fond de page, 16 px entre elles, 24 px de retrait depuis le trait de gauche, texte intérieur à 24 px (tout s'aligne sur l'intitulé).
- Champ manquant dans « L'offre en bref » : « Non précisé » en 15/500 gris (#596070, sombre #ABA398) au lieu de 15/700.

Sombre : « À creuser » (libellé de note, chiffres et arc des anneaux) reste en #B39A82, la valeur déjà utilisée dans le code (6,9:1 sur #171411, 6,2:1 sur #221E1A, 5,2:1 sur #232B45). La maquette est alignée sur cette valeur.

Hors champ : les onglets Envoyées des planches Ajouter et Spontanée sont d'une ancienne version et n'ont pas été modifiés. Référence pour Envoyées : CandidaturesOrdinateurB.

## 12. Trier les offres du jour (ordinateur)

Réponses aux questions (15 novembre) :
- Clavier : ← Écarter, → Garder (inchangé). Tab / Maj+Tab entre les cartes, Entrée ou Espace pour retourner la carte qui a le focus. Écarter affiche aussi un toast avec « Annuler ».
- 2 offres : éventail à 2 cartes, −4° et +4°, mêmes règles d'alignement et de centrage, étalées à 340 px au survol. 1 offre : une carte droite centrée, sans rotation ni étalement, retournement conservé. 0 offre : état « Rien à trier pour l'instant ». Titre manuscrit accordé (« 2 offres pour toi », « 1 offre pour toi »).


Planches TrierOffresOrdinateurV2 et Sombre, états e = ferme (défaut) / etale / dos. Captures TrierOffresOrdinateurV2.png et --etats.png.
- Éventail de 3 cartes 320 × 430 px : la meilleure offre devant au centre, les deux autres à −7° et +7° derrière. Hauts des trois cartes alignés, éventail centré dans son bloc.
- Survol : les cartes s'étalent sur un même plan (écart 340 px). Clic sur une carte : elle se retourne (dos = extrait de l'annonce surligné, 3 verdicts, lien « Voir l'annonce complète »).
- Face : logo et anneau de note sur la même ligne, notes manuscrites (Caveat Brush) au centre, poste et entreprise en bas, puces en capitales.
- Sous l'éventail : titre manuscrit (« 3 offres pour toi »), puis Écarter / Garder 52 px, 12 px entre eux, puis points de progression et compteur. Pas de phrase d'explication sous le titre (règle : texte hors carte = titre ou lien seulement).
- Garder : badge « Gardée » sur la carte et toast « Offre gardée dans tes candidatures » avec Annuler.

## 13. États vides

Règle générale
- Quand une liste est vide, on ne garde pas la mise en page liste + détail : l'illustration, le titre et les actions sont centrés sur toute la largeur de l'écran, au milieu de l'espace sous l'en-tête de page (un peu au-dessus du centre exact, 72 px de marge basse sur ordinateur).
- L'en-tête de page ne change jamais (titre, onglets, alertes, Ajouter) : les éléments restent au même endroit d'une page à l'autre.
- Liste vide parce qu'il n'y a encore rien : pas de champ de recherche ni de filtres (ordinateur et téléphone, y compris l'icône Filtres du téléphone). Liste vide à cause des filtres : la barre de filtres reste.
- Texte hors carte = titre ou lien seulement. Une explication devient une pastille : 14 px / 600, 6 px 12 px, rayon 999 px, icône 16 px, fond #E8ECFB texte #1A3496 (sombre fond #232B45 texte #C9D3FF).
- Ordinateur : illustration 400 px de large (Offres), titre 28/800, pastille 12 px dessous, boutons 52 px côte à côte 28 px dessous, lien 20 px dessous. Téléphone : titre 22/800, boutons 48 px empilés pleine largeur (300 px max), 12 px entre eux.

Nouvelles planches (clair et sombre)
- Premier passage, Offres, aucune alerte : CandidaturesOrdinateurVide, CandidaturesVide. Titre « Pas encore d'offre », pastille « Offres collectées chaque jour », boutons « Créer mes alertes » (principal) et « Ajouter une offre », lien « Faire une candidature spontanée ». L'en-tête affiche « Aucune recherche suivie ».
- Premier passage, Offres, alertes créées mais rien de collecté : CandidaturesOrdinateurVideAlertes, CandidaturesVideAlertes. Titre « Tes alertes sont prêtes », pastille « Première collecte ce soir vers 18 h » (heure réelle de la prochaine collecte), boutons « Ajouter une offre » (principal) et « Voir mes alertes ». Le bouton « Créer mes alertes » ne doit jamais s'afficher si des recherches sont suivies (incohérence vue en production : « 4 recherches suivies » + « Créer mes alertes »).
- Envoyées sans candidature : EnvoyeesOrdinateurVide, EnvoyeesVide. Titre « Pas encore de candidature envoyée », pastille « Objectif ORP de novembre : 10 candidatures » (mois et objectif réels), bouton « Voir les offres à préparer ».
- Rendez-vous sans rendez-vous : RendezVousOrdinateurVide, RendezVousVide. Titre « Aucun rendez-vous », pastille « jobA1 prépare ta feuille la veille », bouton « Ajouter un rendez-vous ».

Planches corrigées
- Aucune offre avec ces filtres (AucuneOffreOrdinateur, AucuneOffre) : en-tête Candidatures et barre de filtres conservés, « Plus de filtres » avec le nombre de filtres actifs. Les phrases sont remplacées par les filtres actifs en pastilles retirables (bouton, aria-label « Retirer le filtre … »), puis « Tout effacer » et « Modifier les filtres », puis le lien « Élargir à « À creuser et + » : 38 offres » (valeurs réelles). Téléphone : pastilles, « Modifier les filtres », lien « Tout effacer ».
- Fin du tri sans offre gardée (FinDuTriAucune, FinDuTriAucuneOrdinateur, clair et sombre) : la phrase devient la pastille « Prochaines offres demain matin ».
- Rendez-vous, haut de liste (Candidatures ordinateur, Relance) : « Aucun rendez-vous à venir » devient une pastille avec icône calendrier, la phrase d'explication est supprimée.
- Mes alertes e-mail vide (AlertesOrdinateurVide, AlertesOrdinateurSite) : la phrase sous le titre devient la pastille « Aucune alerte pour l'instant ».

Trier avec peu d'offres (complète la section 12) : TrierOffresOrdinateurV2Deux et TrierOffresOrdinateurV2Une (clair et sombre), états e = ferme, etale, dos. À 1 offre, l'état « etale » est un simple focus (contour), sans toast.

## 14. Rendez-vous : même liaison qu'Offres et Envoyées

Planches : CandidaturesOrdinateurB et BSombre (onglet Rendez-vous), Statut, Ajouter, Spontanée, RelanceOrdinateurV2 et Sombre. Captures CandidaturesOrdinateurB(Sombre)--rendez-vous.png.
- Mêmes règles que la section 11 : liste 532 px, carte choisie allongée de 28 px avec la flèche, encoche en face (data-notch « r »), trait fin en haut et à gauche, fondu en bas. La pastille « Aucun rendez-vous à venir » (et le bouton Ajouter à côté) s'aligne sur les cartes non sélectionnées.
- Détail : sous le trait fin, deux cartes empilées. Carte en-tête (calendrier, titre, date et lieu, menu ⋯), 24 px sous le trait, marges 24 px 28 px 24 px 32 px. Puis, 16 px dessous, la carte de contenu (rayon 24 px, 32 px de marge intérieure). Le séparateur qui ouvrait « Ce qui a été convenu » est supprimé. Le trait fin regroupe les deux cartes et les relie à la carte choisie.
- L'état « à venir » (Voir ma feuille, Ce que tu apportes, Tes questions au conseiller) suit la même structure : carte en-tête, puis chaque bloc en carte.
- Offres et Envoyées gardent pour l'instant leur en-tête à plat (section 11).
- RelanceOrdinateurV2 et Sombre : les onglets Offres et Envoyées du fond reçoivent aussi la liaison (section 11). Le panneau Relance ne change pas.

## 15. Saisie du code jobup (étape Alertes)

Planches : OnboardingOrdinateurAlerteCode, …CodeRecu, …CodeExpire (et Sombre), OnboardingAlerteCode, …CodeRecu, …CodeExpire (et Sombre) ; AlertesOrdinateurSite (panneau « Alerte jobup » de Mes alertes, état code reçu).
- Adresse au format sous-adressage : alertes+<nom>-<code>@joba1.ch (exemple alertes+kevin-0mwdr89t@joba1.ch). Téléphone : l'adresse passe à la ligne (overflow-wrap: anywhere), jamais tronquée.
- Nouvelle étape 3 « Recopie le code de jobup », l'ancienne 3 devient 4 « Termine l'alerte sur jobup, puis reviens ici ».
- Attente : cadre pointillé 56 px, roue de chargement, « En attente du code de jobup… ». Le cadre a role="status" aria-live="polite" : l'arrivée du code est annoncée.
- Reçu : cadre plein, contour bleu 1,5 px, code 26/800 espacé (letter-spacing .14em, chiffres tabulaires), bouton « Copier » ; pastille verte « Reçu à 14 h 02 · valable 10 minutes » (heure réelle, durée réelle de jobup).
- Expiré : cadre orange clair (#FDEDE3, texte #8A4A16 ; sombre #3A2A1E / #F2A766), « Code expiré », lien « Renvoyer » (aria-label « Renvoyer le code depuis jobup ») qui rouvre jobup. Le nouveau code remplace l'ancien dès réception.
- Ordinateur : texte d'aide sous le titre de l'étape 3. Téléphone : pas de texte d'aide (place), l'étape 4 se lit en défilant.
- La phrase d'explication sous le grand titre de l'étape est supprimée (ordinateur et téléphone), règle du texte flottant.

## 16. Candidatures téléphone : bouton Ajouter

Planches Candidatures et CandidaturesSombre (onglet Offres). Bouton rond 48 × 48 px à droite du champ de recherche, 8 px d'écart, contour 1,5 px #2445C2 (sombre #7D95FF), fond carte, icône + 22 px, aria-label « Ajouter une offre ». Le titre reste à 30 px. Masqué avec la recherche sur les écrans vides.

## 17. Sous-pages Offres (téléphone)

- ActionsOffre : le menu s'ouvre depuis le ⋯ de la page de l'offre, jamais depuis la carte de la liste. 5 actions, dans cet ordre : J'ai déjà postulé, Écarter l'offre (rouge, toast avec Annuler), Signaler comme expirée, Cette note ne me correspond pas, Partager. Pas de « Marquer comme envoyée » ni de « Justificatif ORP ».
- AjouterOffreTel : flèche d'envoi grise (#E5E2D9, icône #8C8478) et aria-disabled tant que le champ est vide, bleue dès qu'il y a du texte ou un fichier. Texte d'aide « Fonctionne avec jobup, jobs.ch, LinkedIn… » relié au champ (aria-describedby). Quota « Plus que N ajouts aujourd'hui » seulement quand N ≤ 5, en pastille orange à la place du texte d'aide.
- OffreProvisoire (clair et sombre) : lien « Voir la compatibilité » (même libellé partout). Points cochés seulement s'ils viennent de l'extrait de l'alerte. Pas de pastille « Contrat non précisé » dans l'en-tête.
- AucuneOffre : planche de la section 13, sans le bloc « Autres offres / Postuler spontanément ».
- ExtAlerte : adresse au format alertes+<nom>-<code>@joba1.ch.

## 18. Liaison carte → détail, version finale (remplace les parties « liaison » des sections 11 et 14)

Planches : CandidaturesOrdinateurB et BSombre (3 onglets), Statut, Ajouter, Spontanée, RelanceOrdinateurV2 et Sombre, CandidaturesOrdinateurEpinglee et EpingleeSombre (nouvelles). Captures CandidaturesOrdinateurB(Sombre)(--envoyees, --rendez-vous).png, CandidaturesOrdinateurEpinglee(Sombre).png, Liaison-rail-zoom.png.

Ce qui est abandonné par rapport aux sections 11 et 14 : la carte choisie allongée de 28 px, le trait en haut de la zone et son coin arrondi, l'encoche en creux, le halo, l'en-tête à plat.

Liste
- Colonne de 504 px. Toutes les cartes font 480 px, la carte choisie aussi (plus d'allongement). Le champ de filtre, « Plus de filtres », l'objectif ORP et les cartes ont le même bord droit, 24 px avant la fin de la colonne.
- Carte choisie : fond #EEF1FC (sombre #232B45), contour 2 px #2445C2 (sombre #7D95FF), flèche à droite.
- Flèche : SVG data-arrow 22 × 60 px, centrée verticalement. Le contour de la carte s'incurve vers la pointe (congés), pente à 45°, pointe arrondie, un seul trait continu de 2 px. Reprends le tracé exact de la planche.
- Barre de défilement de la liste : à gauche, dans la marge (direction rtl sur le conteneur, ltr sur son contenu ; margin-left -14 px et padding-left 14 px pour que les cartes restent alignées), fine (scrollbar-width: thin, 6 px), couleur #CFCBC1 (sombre #4E473E) sur fond transparent. Elle ne doit jamais passer sur le rail. Barre du détail : à droite, fine, mêmes couleurs.

Rail
- Un seul trait vertical de 1,5 px (jeton --linked-line) entre la liste et le détail, 9 px après la colonne de liste (33 px après le bord des cartes). Pas de trait horizontal, pas de coin. Il apparaît en fondu sur 56 px en haut et disparaît en fondu sur 72 px en bas.
- En face de la carte choisie, le rail fait une pointe vers la gauche qui vient toucher la pointe de la flèche (SVG data-notch, même tracé que la flèche en miroir, 1 px d'écart au plus). Le tracé droit du rail est interrompu sur la hauteur de la pointe. Pas de halo.
- Position de la pointe : top = centre vertical de la flèche − haut de la zone − 30 px. À recalculer au défilement de la liste, au changement de sélection et au redimensionnement (écouteur passif, ResizeObserver, requestAnimationFrame).

Détail
- Tout est en cartes, sur les trois onglets. Première carte = en-tête (24 px sous le haut de la zone, rayon 24 px, marges 22 px 28 px) : intitulé complet, entreprise, puis la ligne de note (Offres), le statut (Envoyées) ou la date (Rendez-vous) et le menu ⋯. Puis les autres cartes, 16 px entre elles, 24 px après le rail.

Carte choisie toujours visible (CandidaturesOrdinateurEpinglee)
- Quand la carte choisie sort de la partie visible de la liste par le haut, une version compacte se fixe sous les filtres, à 12 px de la barre de recherche (jamais collée) : 76 px de haut, rayon 14 px, mêmes fond et contour, logo 40 px, intitulé sur une ligne (ellipse), « <Entreprise> · Sélection affichée » en 13 px, chevron vers le haut, ombre 0 8px 20px rgba(27,31,42,.14). Elle porte la flèche, et la pointe du rail se place en face d'elle. Les cartes défilent dessous (fondu de la couleur de page sous la carte épinglée).
- Si la carte sort par le bas : même carte compacte fixée en bas de la liste, chevron vers le bas.
- C'est un bouton (aria-label « Revenir à la candidature sélectionnée dans la liste ») : au clic, la liste défile jusqu'à la vraie carte (scrollIntoView, block: nearest, sans animation si prefers-reduced-motion) et la carte compacte disparaît.
- La flèche et la pointe du rail ne sont donc jamais masquées : le détail affiché est toujours relié à une carte visible.

## 19. Réglages, menu du compte, Notifications « Tout est lu »

Planches : ReglagesOrdinateurComplet (nouvelle, page entière 1440 × 2340), ReglagesOrdinateur (même contenu, hauteur d'écran), NotificationsOrdinateurVide (nouvelle), Notifications et NotificationsSombre (téléphone, état « tout est lu »), et les 51 planches ordinateur qui contiennent le menu du compte. Captures ReglagesOrdinateurComplet.png, NotificationsOrdinateurVide.png, Notifications--tout-lu.png, NotificationsSombre--tout-lu.png.

Menu du compte (avatar), toutes les pages ordinateur
- Le libellé est « Apparence » (plus « Mode sombre ») et l'ordre des segments est Clair, Sombre, Auto. Même libellé, même ordre que sur la page Réglages. role="group" aria-label="Apparence".

Réglages, carte Notifications
- « Nouvelles offres » : sous-titre « Quand une offre atteint le niveau choisi ».
- « M'avertir dès » (sous-titre « Niveau de correspondance minimum ») : contrôle segmenté Très proche / Proche / À creuser. Chaque segment a 14 px de marge intérieure à gauche et à droite, 32 px de haut, texte jamais collé au bord. Segment choisi : fond blanc, graisse 700.
- « Notification de test » (sous-titre « Un message sur ton téléphone, pour vérifier ») : bouton pilule « Envoyer » (contour bleu, rayon = moitié de la hauteur), pas un bouton rectangulaire.

Réglages, section « Extension du navigateur » (nouvelle carte, après Connexions)
- « Extension Firefox », sous-titre « Remplit tes candidatures et tes codes, sans rien envoyer à ta place », bouton pilule « Installer l'extension » avec l'icône lien externe.
- Une ligne par navigateur relié, nommée « <Navigateur> sur <Système> » (« Firefox sur Mac »), jamais un identifiant technique. Sous-titre « Utilisé aujourd'hui » ou « Utilisé le 9 nov. » (un seul point : ne pas ajouter de point après une abréviation qui en a déjà un).
- Le navigateur en cours porte la pastille verte « Ce navigateur ».
- Bouton corbeille 44 × 44 px par ligne, aria-label « Retirer Firefox sur Windows ». Après retrait : message « Navigateur retiré » avec « Annuler » pendant 6 s.
- Les navigateurs non utilisés depuis plus de 30 jours sont repliés sous « N anciens navigateurs » (bouton avec chevron, aria-expanded), avec le lien rouge « Tout retirer » à droite (confirmation avant d'agir).
- « Relier avec un jeton », sous-titre « Si le bouton « Relier » de l'extension ne marche pas », bouton pilule « Créer un jeton ». Il n'y a plus de champ où taper l'adresse du service à la main.

Réglages, carte « Mes données »
- Toutes les lignes ont la même graisse (600) et la même hauteur. Nouvelle ligne « État du service », sous-titre « Collecte des offres, IA et envoi des e-mails ».

Notifications, état « Tout est lu » (ordinateur et téléphone)
- Scène centrée sur toute la largeur du contenu : mascotte (200 px de haut sur ordinateur, 140 px sur téléphone), titre « Tout est lu », pastille bleue avec cloche « Offres et rappels ORP arrivent ici », bouton pilule à contour « Voir toutes les notifications ».
- Pas de phrase flottante : hors d'une carte, un texte est soit un titre, soit un lien, soit une pastille.
- La cloche de la barre du haut n'a pas de pastille de compteur dans cet état, et « Tout marquer comme lu » n'est pas affiché.

Défauts du code vus sur les captures de production (pas de planche, c'est la règle générale)
- Contours de carte : 1 px, même couleur partout, pas d'ombre en plus du contour. La carte « Effet des critères » du Profil n'a pas de contour bleu.
- Espacement des lignes dans une carte : même hauteur et mêmes marges pour toutes les lignes d'une même carte.
- Boutons : pilules partout (rayon = moitié de la hauteur), jamais rectangulaires.

## 20. Aujourd'hui ordinateur : l'éventail remplace le livre

Planches : AujourdhuiOrdinateurV2 et AujourdhuiOrdinateurV2Sombre (les 3 états qui montrent « 3 offres à trier »). Captures AujourdhuiOrdinateurV2(Sombre).png.

- Le bloc « 3 offres à trier » de la colonne de droite ne montre plus le livre ouvert. Il montre l'éventail de la page Trier (section 12), en petit : les 3 mêmes cartes, mêmes couleurs, mêmes angles (−7°, 0°, 7°), réduites à 66 % (transform: scale(.66), origine en haut au centre), hauteur du bloc 318 px, 20 px sous le titre.
- Sur ces mini-cartes : pas de pastilles (CDI, %, trajet, niveau), elles seraient illisibles à cette taille. Nom de l'entreprise à 13 px affichés.
- Le bloc est un role="group" avec aria-label « 3 offres à trier, la première : <intitulé> chez <entreprise> ». Les boutons Écarter et Garder restent en dessous, sans changement.
- Supprime tout le code, le CSS et les images du livre (couverture, signet, pages) s'il en reste dans l'app.
- Dans le code des planches Trier, l'état « fermé » s'appelle maintenant is_ferme (avant is_livre). Le mot « livre » ne doit plus apparaître nulle part.

## 21. Carte « Pas encore notée » (liste Candidatures ordinateur)

Planches : CandidaturesOrdinateurB(Sombre), Epinglee(Sombre), Statut, Ajouter, Spontanee, RelanceOrdinateurV2(Sombre), états vides Envoyées et Rendez-vous.

- Le texte « Pas encore notée » sur deux lignes en haut à droite disparaît.
- À sa place, même position et même taille que le cercle de note (40 px, aligné en haut) : cercle vide en pointillés (12 tirets égaux, trait 8 sur une échelle de 100, #D5D1C7, sombre #4E473E) avec un tiret central (#8C8478, sombre #ABA398). role="img" aria-label="Pas encore notée".
- Une pastille neutre « Pas encore notée » s'ajoute en tête de la ligne de pastilles (fond #F1EFE9, texte #3D4250 ; sombre #2B2620 / #C9C2B8), même style que les autres pastilles neutres.

## 22. Nouveau compte sans offre, carte Google Emplois, Trier « Rien à trier »

Planches : AujourdhuiOrdinateurNouveau(Sombre), AccueilNouveau(Sombre) (téléphone), TrierOrdinateurRien(Sombre), TrierRien(Sombre), CandidaturesOrdinateurVide(Sombre) et CandidaturesVide(Sombre) (lien ajouté). Captures du même nom.

Aujourd'hui, nouveau compte sans offre
- Bloc d'accueil : « Bienvenue, / tes offres arrivent bientôt », sous-titre « Crée ta première alerte : jobA1 s'occupe du reste. »
- « Premiers pas » (compteur « 2 sur 3 ») : étapes faites avec coche verte et « Fait », étape suivante numérotée en bleu avec le seul bouton plein de l'écran « Créer mon alerte » (pleine largeur sur téléphone).
- Carte Google Emplois juste sous les premiers pas (32 px d'écart). C'est une ligne à fond bleu (#E8ECFB, sombre #232B45), rayon 20 px, même hauteur que les lignes des premiers pas (88 px) : icône loupe dans un rond blanc de 36 px, titre « Des offres pour toi, en attendant », sous-titre « <Métier> · <Lieu> » (#3D4250), bouton pilule blanc sans contour « Voir sur Google Emplois » + icône lien externe (48 px de haut), croix « Masquer » 44 × 44 px. Pas de pastille, pas de date.
- Téléphone : même carte bleue, titre et sous-titre en haut avec la croix à droite, bouton blanc pleine largeur dessous (12 px d'écart).
- États des planches (v = pas, ferme, masque). « ferme » : premiers pas fermés, la carte passe en premier sous le bloc d'accueil ; sur téléphone la section s'appelle « Tes premières offres ». « masque » : la carte disparaît, message « Carte masquée » + « Annuler » pendant 6 s (même composant que « Offre gardée »), masquage mémorisé pour le compte, pas de réglage pour la réafficher.
- Sous la carte, deux liens : « Ajouter une offre vue ailleurs », « Transférer mes alertes ».
- Colonne ORP à zéro (« 0 sur 10 », « 10 candidatures d'ici le 5 décembre »). Bloc « Offres à trier » : « Rien à trier pour l'instant / Tes premières offres arrivent après ta première alerte. », sans signet ni lien « Élargir ma recherche ».

Trier, 0 offre (« Rien à trier pour l'instant »)
- Illustration des mascottes sur le banc (celle de « Pas encore d'offre »), pas celle de fin de tri (confettis = tri terminé).
- Titre : « Rien à trier » en manuscrit + « pour l'instant ». Pastille bleue « Offres collectées chaque jour ».
- Boutons pilule : « Voir mes candidatures » (plein) et « Gérer mes alertes » (contour), 12 px d'écart (empilés sur téléphone).

Candidatures vide
- Lien « Voir les offres sur Google Emplois » + icône lien externe, au-dessus de « Faire une candidature spontanée ». Pas de carte. Ce lien n'est pas concerné par « Masquer ». Il figure aussi dans l'état « Tes alertes sont prêtes » (planches CandidaturesOrdinateurVideAlertes et CandidaturesVideAlertes, clair et sombre).

## 23. Premiers pas en 5 étapes (Aujourd'hui ordinateur et Accueil téléphone)

Planches : AujourdhuiOrdinateurNouveau(Sombre) (hauteur 1200), AccueilNouveau(Sombre). États v = pas (2 sur 5), alerte (3 sur 5), ferme, masque. Captures AujourdhuiOrdinateurNouveau*--alerte.png, AccueilNouveau*--alerte.png, etc.

- Une seule forme, une liste de 5 lignes, sur ordinateur et téléphone. L'ancienne carte « 2 sur 5 » disparaît partout, téléphone compris.
- Compteur à droite du titre « Premiers pas » : « N sur 5 ».
- 1 « Ton CV est lu » / « N compétences reprises » (coche verte, « Fait »). 2 « Tes critères sont réglés » / « Métier · Lieu · taux » (coche, « Fait »).
- 3 avant l'alerte : rond bleu « 3 », « Créer ta première alerte » / « jobup : 2 minutes », bouton plein « Créer mon alerte » (seul bouton plein de l'écran ; pleine largeur sous la ligne sur téléphone). Après : coche, « Ta première alerte est créée » / « jobup · chaque jour », « Fait ».
- 4 « Garder tes premières offres » et 5 « Préparer et envoyer une candidature » : rond gris (#ECE9E1, chiffre #596070), titre et sous-titre en #596070, pas de bouton, aria-disabled="true". Sous-titre « Dès ta première offre ». Quand les 3 premières étapes sont faites sans offre arrivée, le sous-titre de l'étape 4 devient « Ta première offre arrive après la prochaine collecte ».
- Ordinateur : lignes en cartes blanches de 88 px, 12 px d'écart. Téléphone : lignes de 72 px séparées par un trait, dans la feuille blanche.
- L'écran « C'est fait ! » reste à la fin des 5 étapes.
