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

## 24. Onboarding, étape 3 : trajet du code jobup

Planches : OnboardingOrdinateurAlerteCode, ...CodeRecu, ...CodeExpire et OnboardingAlerteCode, ...CodeRecu, ...CodeExpire (téléphone), en clair et en sombre. Complète la section 15.

- Sous « Recopie le code de jobup », un trajet en 3 points reliés par un trait : « jobup », « Ta boîte jobA1 » (« Boîte jobA1 » sur téléphone), « Cette page ». Chaque point : rond de 40 px avec icône, nom en gras, état dessous.
- En attente : cadre à contour plein (plus de pointillés). Points 1 et 3 en pointillés gris (« envoie le code », « le code s'affiche »), point 2 actif en bleu avec anneau (« on écoute »), traits en pointillés. Sous un séparateur, ligne d'état avec l'indicateur tournant : « Rien reçu pour l'instant. Valide l'alerte sur jobup, on vérifie toutes les 15 s. » (téléphone : sans la fin). role="status" aria-live="polite".
- Code reçu : les 3 points en vert avec coche (« code envoyé », « code reçu », « code affiché »), traits verts pleins, puis le champ du code et la pastille « Reçu à … » inchangés.
- Code expiré : points 1 et 2 verts, point 3 orange avec icône d'alerte (« code expiré »), puis le bandeau « Code expiré / Renvoyer » inchangé.
- Le serveur ne sait qu'une chose : l'e-mail est arrivé ou non. N'affiche jamais d'état intermédiaire inventé (« en route », « envoyé par jobup ») avant l'arrivée.
- Après 2 minutes sans code : ajoute sous la ligne d'état « Toujours rien ? Vérifie que l'adresse est bien collée dans jobup. » (pas de planche, même style que la ligne d'état).
- prefers-reduced-motion : l'indicateur ne tourne pas.

## 25. Onboarding ordinateur, étape alerte : scène à la place du bonhomme seul

Planches : OnboardingOrdinateurAlerte, ...AlerteCode, ...AlerteCodeRecu, ...AlerteCodeExpire, en clair et en sombre. Image source : captures/scene-boite-aux-lettres.png (fond transparent).

- La mascotte seule est remplacée par la scène des trois mascottes autour de la boîte aux lettres. Largeur affichée 420 px, hauteur automatique, 40 px sous le haut de la colonne. alt="" aria-hidden="true" (décorative).
- Sers-la en WebP, 840 px de large (2x), environ 73 Ko, avec width et height en attributs pour éviter le saut de mise en page, loading="lazy" inutile (elle est au-dessus de la ligne de flottaison).
- Téléphone : pas d'illustration sur cette étape, inchangé.

Compléments section 23 (premiers pas) :
- Bloc d'accueil, sous-titre : « Crée ta première alerte : jobA1 s'occupe du reste. » avant l'alerte ; « Ton alerte est créée. La prochaine collecte t'apporte tes premières offres. » une fois l'alerte créée (état v = alerte).
- Un seul bouton à la fois, sur l'étape en cours : 3 « Créer mon alerte », 4 « Trier mes offres », 5 « Préparer une candidature ». Étapes faites : « Fait », sans bouton. Étapes à venir : grisées, sans bouton.
- Croix « Masquer les premiers pas » : 44 × 44 px à droite du compteur, aria-label « Masquer les premiers pas », bandeau « Premiers pas masqués » + « Annuler ».
- Phrase ORP : la phrase commune de l'app (« Encore N d'ici le <date> »), pas celle de la planche.
- Tous les bandeaux avec « Annuler » ont le trait de compte à rebours.

## 26. Téléphone : Réglages à parité, carte « Pas encore notée »

Planches : Reglages et ReglagesSombre (nouvelle), Candidatures et CandidaturesSombre. Captures Reglages--complet.png et ReglagesSombre--complet.png (page entière).

Réglages téléphone
- « Nouvelles offres » : sous-titre « Quand une offre atteint le niveau choisi ».
- Nouvelle ligne « M'avertir dès » (sous-titre « Niveau de correspondance minimum ») : contrôle segmenté Très proche / Proche / À creuser, 40 px de haut, 6 px de marge intérieure par segment, texte 13 px, jamais collé au bord. role="group" aria-label « M'avertir dès », aria-pressed.
- Nouvelle ligne « Notification de test » (« Un message sur ce téléphone, pour vérifier ») : bouton pilule à contour « Envoyer », 40 px.
- Nouvelle section « Extension du navigateur » : une ligne « Navigateurs reliés · N » (sous-titre : noms des navigateurs) qui ouvre la liste (retirer, anciens navigateurs, « Tout retirer », comme sur ordinateur). Sous la carte, pastille bleue « L'extension s'installe depuis ton ordinateur ». Pas de bouton « Installer » ni de jeton sur téléphone.
- « Mes données » : nouvelle ligne « État du service » (« Collecte des offres, IA et e-mails »).
- « Apparence » : déjà conforme (Clair, Sombre, Auto).

Candidatures téléphone, carte sans note
- Cercle vide en pointillés de 48 px à la place de l'anneau, tiret central, aria-label « Pas encore notée ».
- Pastille neutre « Pas encore notée » en première position. Les pastilles qui ne tiennent pas passent dans le « +N » existant, jamais coupées.

## 27. Téléphone : cartes de liste sur 2 lignes, notifications, Réglages, Bandeau pêche

Règle générale téléphone : une carte de liste affiche 2 lignes de texte au plus. Ligne 1 : le titre (16 px, gras, une ligne, points de suspension) avec au plus une pastille d'état au bout. Ligne 2 : le détail (14 px, gris, une ligne, points de suspension). Exception : la rangée de pastilles des cartes Offres reste (outil de tri), seul le titre passe sur 1 ligne. aria-label de la carte = tout le texte, y compris ce qui est coupé.

Notifications (Notifications, NotificationsSombre)
- Ligne 1 : titre court (20 caractères au plus) + pastille bleue « Nouveau » tant que la notification n'est pas lue. Ligne 2 : « détail · heure » (détail 22 caractères au plus). Non lue = titre en gras + fond bleuté + pastille « Nouveau ». Plus de texte « Non lue » ni de point.
- Titres de la planche : « 5 nouvelles offres », « Lettre à relire », « Justificatifs ORP », « 5 relances à faire », « Bilan de la semaine », « Budget IA presque atteint », « 17 nouvelles offres ».
- Le message « Notification supprimée » + « Annuler » a le trait de compte à rebours.

Envoyées (Envoyees, EnvoyeesSombre, EnvoyeesStatut)
- Ligne 1 : poste + pastille de statut (Sans réponse : orange ; Entretien : vert ; Vue : bleu ; Envoyée, Refus, Refusée : neutre). Ligne 2 : « entreprise · quand » (« il y a 12 j », « réponse hier », « jeu. 12 nov., 14 h », « lundi », « 21 oct. »). La colonne de statut à droite et la pastille « Envoyée il y a… » disparaissent.
- Le message « Réponse de … : refus » + « Voir » + « Annuler » a le trait de compte à rebours.

Détail d'une envoyée (EnvoyeeDetail, …Contacte, …Contacts, …Documents)
- Historique replié par défaut : bouton « Historique » + résumé « N étapes · dernière le <date>, <étape> », chevron, aria-expanded. La liste s'ouvre au toucher.

Filtres des envoyées (FiltresEnvoyees)
- Tri à 3 choix : « À relancer » (défaut), « Plus récentes », « Plus anciennes ». Pastilles de statut en vraie pilule (rayon 22 px pour 44 px).

Rendez-vous (RendezVous, RendezVousSombre)
- Cartes « À venir » : icône calendrier + ligne 1 « titre » avec pastille (« Feuille prête » vert pour l'ORP, « Entretien » neutre) + ligne 2 « heure · lieu court » (« 9 h 30 · ORP Renens », « Alpstack · 14 h · visio »). Toute la carte est cliquable, pas de flèche. « Préparer le rendez-vous » et « Préparer l'entretien » passent dans le détail.
- Carte « À noter » : « ORP du 13 octobre » + pastille orange « À noter », ligne 2 « 1 minute pour noter l'essentiel ». Toute la carte ouvre la saisie.

Bilan (Orp, OrpSombre)
- Lignes « À déclarer » et « Recherches du mois » : ligne 1 entreprise + pastille d'état (« justificatif joint » vert, « infos à compléter » / « justificatif à joindre » orange) ; ligne 2 « poste · date ».
- Les phrases sous les titres de section deviennent des pastilles bleues : « Pas encore sur ta feuille ORP », « Justificatif : e-mail ou capture ».

Candidatures (Candidatures, CandidaturesSombre)
- Titre de l'offre sur 1 ligne avec points de suspension. Rangée de pastilles inchangée.

Réglages téléphone, variantes (ReglagesConnexions, ReglagesRetirer)
- Mêmes ajouts que la section 26 (M'avertir dès, Notification de test, Navigateurs reliés, État du service). « Retirer l'accès » et « Supprimer mon compte » en pilule (aussi sur Reglages et ReglagesSombre).

Préparer ordinateur (8 planches PreparerOrdinateur*)
- Vignette « Bandeau » de la carte Mise en page : bandeau pêche #F3B08A avec la barre de titre #1B1F2A, en clair comme en sombre (couleur du document, identique au PDF et au téléphone).

## 28. Derniers écrans téléphone et vérification finale

Planches : AlertesTel, AlertesTelAlerte, AlertesTelConfirmer, FinDuTri(Sombre), OrpRemisV2(Sombre), ReglagesLangue, et les planches ordinateur Candidatures*, Relance*, AucuneOffreOrdinateur, Envoyées et Rendez-vous vides.

- Alertes e-mail (téléphone) : cartes en 2 lignes. Ligne 1 : la recherche + pastille orange « À confirmer » si besoin. Ligne 2 : « source · lieux ». Les phrases hors carte deviennent des pastilles : « 5 recherches suivies · dernière le 7 nov. », « Ouvre l'alerte pour la confirmer sur Indeed » (orange), « Les offres arrivent dans « À traiter » » (bleu), « Pas encore créée sur le site » (neutre).
- Fin du tri (téléphone) : titre et ligne 2 des offres gardées sur une ligne chacun, avec points de suspension.
- Bilan, mois remis (téléphone) : « Preuve gardée » devient une pastille verte au bout du nom de l'entreprise.
- Réglages, variante Langue (téléphone) : mêmes ajouts que la section 26, « Supprimer mon compte » en pilule.
- Ordinateur : les boutons de 52 px de haut (« Préparer ma candidature », « J'ai déjà postulé », etc.) ont un rayon de 26 px (pilule), plus 22 px.
- Ordinateur : tous les messages avec « Annuler » (dont « Offre écartée ») ont le trait de compte à rebours.
- Ordinateur, mode sombre : quand le message a un fond clair (#F3EEE6), « Annuler » est en #1A3496 (le bleu clair #AEBDFF n'était pas lisible dessus).

## 29. Bilan sur ordinateur : les 9 états sans planche (clair et sombre)

Planches : BilanOrdinateur(+Sombre) mises à jour, et BilanOrdinateurMois, BilanOrdinateurMoisPrecedents, BilanOrdinateurExports, BilanOrdinateurFicheSombre, BilanOrdinateurFormVide, BilanOrdinateurCatalogue, BilanOrdinateurFormEtats, BilanOrdinateurTropTot, BilanOrdinateurChargement, BilanOrdinateurErreur (chacune avec sa version Sombre, sauf la fiche qui n'existe qu'en sombre ici). Captures : captures/bilan-etats/.

ORP
- En bas de la page ORP, sous « Rendez-vous ORP » : deux boutons pilule contour (44 px) « Mois précédents » (icône calendrier) et « Autres exports » (icône téléchargement), avec chevron bas. Ils sont maintenant sur la planche principale aussi.
- Menu « Mois précédents » ouvert : s'ouvre vers le haut, largeur 300 px, rayon 16 px, ombre 0 12px 32px rgba(27,31,42,.16) ; 6 mois (octobre 2026 à mai 2026), une ligne de 44 px par mois avec l'icône calendrier. Le mois dont les justificatifs sont à remettre porte « À remettre » en orange (#8A4A16 / sombre #F2B98E), comme le bandeau du haut. Chevron du bouton vers le haut quand le menu est ouvert.
- Menu « Autres exports » : même style, 2 lignes : « Télécharger en CSV (Excel) » et « PDF avec le journal des recherches ».
- Mois déplié (?tout=1) : les 11 recherches à déclarer s'affichent toutes, sans « Voir les 8 autres ». Le chevron de la carte Novembre pointe vers le haut. « Voir tout le mois et les justificatifs » est remplacé par le lien « Replier le mois » (chevron haut), qui revient à la vue normale (retire ?tout=1). Nouveau : aujourd'hui seul le bouton Retour du navigateur permettait de revenir.
- Fiche « Pour l'ORP » en sombre : mêmes jetons sombres que le reste de l'app.

Formations
- Aucune formation suivie : l'encadré « L'ORP peut financer une formation » reste en haut ; dessous, état vide centré : scène « introuvable » (troupe), titre « Aucune formation suivie », pastille bleue (icône signet) « Garde une formation du catalogue avec son signet », bouton principal 52 px « Voir le catalogue » (icône livre). Le libellé « Chercher d'autres formations » n'est pas utilisé ici : il n'y en a pas encore.
- Catalogue : lien « ← Mes formations » en haut ; encadré pêche (#FFF1E6) « Financement possible par l'ORP / Seulement avec l'accord préalable de l'ORP » avec icône étiquette et flèche ; puces Tout / Certifications / Cours | Gratuites / En français (puce active : fond #1B1F2A, texte blanc ; sombre : fond #F3EEE6, texte #171411) ; une carte par section (« Certifications », « Cours et ateliers », avec le nombre à droite). Ligne : icône 40 px (étoile sur fond orange clair pour une certification, livre sur fond bleu clair pour un cours), titre sur 1 ligne, ligne 2 : organisme · format · niveau + pastille « Gratuit » (verte) ou « Payant » (neutre). À droite, bouton signet rond 44 px : contour gris si pas gardée, fond #E8ECFB et signet plein si gardée (aria-pressed). Puis « Chercher d'autres formations » en pilule contour.
- En cours sans nombre de modules : sous le titre, le texte libre sur 1 ligne (points de suspension) en #3D4250, et à droite le lien « Noter l'avancement ». Une formation avec modules garde la barre et « Module N sur 12 ».
- Terminée dans « Gardées » : à droite, coche + « Terminée » en vert (#17734A / sombre #62D497), puis la flèche ronde.

Résultats
- Trop tôt pour conclure : état vide centré, scène « groupe » (troupe, 300 px), pastille bleue (icône graphique) « Le Bilan se remplit avec tes premières candidatures et réponses », bouton principal « Voir les offres » (icône mallette).
- Chargement : 3 blocs gris (#ECE9E1 / sombre #2C2722) aux formes du contenu (chiffres, « Le mois en bref », « Ce qui bloque »), reflet animé ; aria-busy="true". Animation coupée si prefers-reduced-motion.
- Erreur (remplace la ligne rouge actuelle) : état vide centré, NOUVELLE scène « erreur » (illustrations/erreur-480|840.webp et erreur-sombre-480|840.webp, affichée à 360 px de large), titre « Bilan indisponible pour l'instant » (role="alert"), pastille bleue (coche) « Tes candidatures et ton suivi ORP ne sont pas touchés », bouton principal « Réessayer » (icône flèche circulaire) qui relance le chargement. Hors ligne : garder NetworkError tel quel.

## 30. Offre écartée sans note (A2)

Planches : OffreEcartee(+Sombre) (téléphone), CandidaturesOrdinateurEcartee(+Sombre) (ordinateur). Captures : captures/ecartee/.

- Téléphone, fiche de l'offre : la carte de note garde sa place et sa forme. À gauche, l'anneau gris en pointillés avec un trait (le même que « Pas encore notée », aria-label « Pas de note »). Titre « Écartée le 12 nov. » (couleur du texte, pas de vert). Dessous : « Pas de note : jobA1 ne note pas les offres écartées. » La ligne du bas de la carte devient « Remettre dans le tri » (à la place de « Voir la compatibilité », même style, même chevron). Barre du bas : « Écarter » disparaît, seul « Préparer ma candidature » reste, sur toute la largeur.
- Ordinateur, détail : la ligne de note devient « Écartée le 12 nov. » + pastille neutre « Pas de note » (#F1EFE9 / #3D4250) + lien à droite « Remettre dans le tri ». Le bouton « Écarter » disparaît de la rangée d'actions.
- Liste : la carte a l'anneau en pointillés et la pastille neutre « Écartée » (à la place de « Pas encore notée »), dans le groupe « Écartées ».
- « Remettre dans le tri » remet l'offre dans les offres à traiter ; elle est alors notée comme les autres (dans le plafond du jour).

## 31. Filtres : des mots que tout le monde comprend

Planches : le panneau Filtres de toutes les planches Candidatures ordinateur (13 planches, clair et sombre) et Filtres (téléphone). Captures : captures/filtres/.

- « Correspondance minimale » devient « Note minimale, sur 100 ». Choix : Toutes / 50 et + / 75 et + / 85 et + (mêmes seuils qu'avant : 50 À creuser, 75 Proche, 85 Très proche ; seuls les libellés changent). Dessous, en 13 px #596070 (sombre #ABA398) : « À quel point l'offre correspond à ton profil. »
- « Note » devient « Type de note ». « Sûres · n » devient « Définitives · n ». Dessous, sur ordinateur aussi : « Provisoire : notée sur l'extrait de l'alerte, sans l'annonce complète. »
- « Taux minimum » devient « Taux d'activité ». Choix : Tous / Dès 60 % / Dès 80 % / 100 % (un seul choix). Sur téléphone : contrôle segmenté à 4 cases, comme « Note minimale » (la planche avait des tranches à choix multiples que l'app n'a pas).
- Trier : « Par jour » devient « Par date ».
- « Télétravail au moins partiel » devient « Télétravail possible, même partiel ».
- Téléphone : « Note minimale » passe à 4 cases (Toutes / 50 et + / 75 et + / 85 et +), comme l'ordinateur (la planche avait 60 et 80, pas les seuils de l'app).

## 32. CV adapté : dire pourquoi chaque changement

Planches : PreparerOrdinateurCVChangements, PreparerOrdinateurCVPret (compteur). Captures : captures/pourquoi-illisible/review_cv_pourquoi.png.

- Sous « Avant / Maintenant » de chaque changement, une ligne : icône cible 18 px (#596070) + « Pourquoi : » en gras + la raison, 14 px, #3D4250. La raison ne figure plus dans « Maintenant ».
- Les mots tirés de l'annonce sont surlignés comme dans « Le poste » : <mark> fond #FFE9A8, rayon 4 px.
- Règle stricte côté IA : la raison ne cite que des mots présents dans l'annonce (ou, pour un retrait, la contrainte « tenir sur une page »). Demander la raison dans la même réponse que le changement (champ « pourquoi » par changement), sans appel en plus. Si aucune raison fiable : ne pas afficher la ligne, plutôt qu'inventer.
- Les retraits sont aussi des changements : « Maintenant : retirés pour cette offre. » + pourquoi + « Annuler ce changement ». Chaque changement, Profil compris, a « Annuler ce changement ».

## 33. Annonce illisible : les liens tout de suite

Planches : CandidaturesOrdinateurB et toutes les planches ordinateur qui montrent ce bloc (clair et sombre), OffreProvisoire(+Sombre) état refused. Captures : captures/pourquoi-illisible/review_illisible.png.

- Texte : « {Site} bloque la lecture. Trouve l'annonce complète, puis donne-la à jobA1. »
- Ordinateur : une rangée sous le texte, gap 8 px, boutons pilule 44 px : « Ouvrir sur {Site} ↗ » (contour bleu, nouvel onglet), « Chercher sur le site de {Entreprise} ↗ » (contour bleu, nouvel onglet), « Donner l'annonce » (fond #E8ECFB, ouvre la zone existante : lien chez l'employeur + coller le texte). Le menu déroulant disparaît.
- Téléphone : les 2 premiers en liens texte (44 px de haut, empilés), puis « Donner l'annonce » (même style tonal), qui ouvre la feuille existante.
- « Chercher sur le site de … » ouvre une recherche web : "{titre du poste}" "{entreprise}" (jobA1 ne connaît pas l'adresse de la page carrière). Lien externe : rel="noopener", texte caché « (nouvel onglet) ».

## 34. Chercher dans le CV (et la lettre) et voir les changements

Planches : PreparerOrdinateurCVPret (boutons fermés), PreparerOrdinateurCVChangementsVus(+Sombre), PreparerOrdinateurCVRecherche(+Sombre). Captures : captures/agence-recherche/review_cv_recherche.png. Même chose à l'étape Lettre.

- En-tête « CV adapté », à gauche de FR/DE/EN : bouton rond 44 px loupe (aria-label « Chercher dans le CV », aria-expanded) et bouton pilule 44 px « Voir les changements · N » (aria-pressed ; actif = fond #E8ECFB, contour #2445C2).
- Voir les changements : chaque passage modifié est surligné dans l'aperçu, fond #E8ECFB (sombre #232B45) + trait 2 px #2445C2 à gauche (box-shadow inset). N = nombre de changements de « Adapté pour cette offre ».
- Recherche : barre sous l'en-tête : champ pilule 44 px (contour 2 px #2445C2 au focus, icône loupe), compteur « 2 sur 2 » (aria-live="polite"), boutons ronds précédent / suivant, fermer (X). Résultats : fond #FFE9A8 ; résultat courant : fond #FFB86B + contour 2 px #B4631F, et défilement jusqu'à lui. Entrée = suivant, Maj+Entrée = précédent, Échap = fermer.
- « Ce CV » : « N changements, à vérifier » en orange #8A4A16 (sombre #F2B98E), pas en vert. Lignes sans fond ni coins arrondis propres : seulement le trait de séparation (corrige le bug vu en vrai : la ligne avait un fond bleu et une bordure arrondie, une carte dans la carte).

## 35. Agence de placement

Planches : CandidaturesOrdinateurAgence(+Sombre), OffreAgence(+Sombre), panneau Filtres (13 planches ordinateur) et Filtres (téléphone). Captures : captures/agence-recherche/review_agence.png.

- Nouveaux jetons : fond #EFE9F7 / texte #5B3E8C (sombre : #2E2540 / #C9B3F0), contraste ~7:1.
- Carte : pastille « Agence » avec icône 2 flèches opposées, en premier dans la rangée de pastilles.
- Fiche : sous le nom de l'entreprise, séparée par un trait, une ligne : rond 32 px avec la même icône ; « Agence de placement » en gras ; « {Agence} recrute pour un client dont le nom n'est pas donné. Demande-le avant d'envoyer : tu évites de postuler deux fois au même poste. » ; lien « Ce n'est pas une agence » (à droite sur ordinateur, dessous sur téléphone). La correction est gardée pour cette entreprise.
- Filtres : interrupteur « Masquer les agences de placement » (téléphone : sous-titre « Seulement les employeurs directs »).
- Détection, du plus sûr au moins sûr : 1) l'entreprise figure au répertoire SECO des entreprises autorisées au placement / à la location de services (vérifier d'abord les conditions d'usage, pas de lecture automatique sans accord de Kevin) ; 2) l'annonce dit « pour notre client », « mandatés par », « on behalf of our client »… → titre « Probablement une agence de placement » ; 3) la correction de l'utilisateur. Location de services / régie (l'agence embauche, tu travailles chez un client) : même dessin, titre « Société de placement en régie », texte « Tu serais employé par {Agence} et placé chez un de ses clients. »
- Doublon : si une candidature envoyée vise le même poste (titre + lieu proches) chez l'employeur ou via une autre agence, le dire dans cette ligne.

## 36. Colonne de droite vide (rien d'ouvert) et nouvelle scène d'erreur

Planches : CandidaturesOrdinateurAucuneOuverte, EnvoyeesOrdinateurAucuneOuverte, RendezVousOrdinateurAucunOuvert (chacune + Sombre), et l'état « Choisis une offre » de toutes les planches Candidatures ordinateur. BilanOrdinateurErreur(+Sombre) : scène remplacée. Images : illustrations/choisis-offre, choisis-candidature, choisis-rendez-vous, erreur (chacune en -480 / -840, clair et -sombre). L'ancienne erreur-*.webp de la section 29 est remplacée par celle-ci (même nom).

- Ordinateur, Offres / Envoyées / Rendez-vous, quand aucun élément n'est ouvert : dans la colonne de droite, centré : scène (340 px de large), titre 24 px 800, pastille bleue (#E8ECFB / #1A3496 ; sombre #232B45 / #C9D3FF) avec une flèche vers la gauche :
  - Offres : « Choisis une offre » + « Son détail s'affiche ici »
  - Envoyées : « Choisis une candidature » + « Suivi, relances et documents s'affichent ici »
  - Rendez-vous : « Choisis un rendez-vous » + « Préparation et feuille ORP s'affichent ici »
- Dans la liste, aucune carte sélectionnée et pas de pointe de liaison vers le détail.
- Pas de bouton : l'action est dans la liste à gauche, que les personnages montrent du doigt.
- Après « Écarter » (offre retirée de la liste), le même état s'affiche, avec le message « Offre écartée · Annuler ».

## 37. Téléphone : les ajouts du jour (Bilan, CV, agence)

Planches (chacune + Sombre) : OrpMois, OrpMoisPrecedents, OrpExports, BilanTropTot, BilanChargement, BilanErreur, BilanFormations, BilanFormationsVide, BilanCatalogue, MaCandidatureCV, MaCandidatureCVPourquoi, MaCandidatureCVRecherche, CandidaturesAgence. Captures : captures/telephone-1611/.

Bilan, ORP
- Mois déplié : la carte « Mois ORP » a son chevron vers le haut ; les recherches s'affichent toutes, en cartes de 2 lignes (ligne 1 : entreprise + pastille d'état si besoin ; ligne 2 : poste · date), flèche ronde à droite. Lien « Replier le mois » sous la liste.
- « Mois précédents » et « Autres exports » : 2 boutons pilule contour côte à côte, chacun sur la moitié de la largeur, en bas de la page. Sur téléphone ils ouvrent une feuille du bas (titre + X), lignes de 52 px avec icône ; octobre porte la pastille « À remettre ».

Bilan, Résultats
- Trop tôt / chargement / erreur : comme l'ordinateur (section 29), scène 250 à 290 px, pastilles raccourcies : « Il se remplit avec tes candidatures », « Tes candidatures ne sont pas touchées ». Titre erreur : « Bilan indisponible ». Chargement : 3 blocs (96, 160, 256 px).

Bilan, Formations
- Encadré ORP en tête : « L'ORP peut financer une formation / Avec l'accord de ta conseillère » + flèche ronde.
- En cours : carte avec titre (1 ligne), organisme, puis barre + « Module N sur 12 » ou le texte libre (1 ligne) ; en bas « Noter l'avancement » (lien, à gauche) et « Continuer le cours » (pilule contour, à droite), sur toutes les cartes.
- Gardées : cartes de 2 lignes, statut en pastille sur la ligne 2 (« Terminée » vert avec coche, « Financement possible » vert).
- Aucune formation : scène « introuvable », « Aucune formation suivie », pastille « Garde-en une avec son signet », bouton « Voir le catalogue ».
- Catalogue : « ← Mes formations », encadré pêche, puces sur une ligne qui défile horizontalement, une carte par section ; ligne : titre (1 ligne) + organisme · format + pastille Gratuit/Payant, signet rond 44 px à droite. Pas d'icône de type à gauche sur téléphone (place pour le titre).

Ma candidature, étape CV
- Rangée d'outils sous les étapes : « Changements · N » (pilule, aria-pressed), espace, loupe ronde 44 px, lien « Modèle » (ouvre la feuille Mise en page existante).
- Changements visibles : passages modifiés surlignés (#E8ECFB + trait 2 px #2445C2).
- Toucher un passage surligné ouvre une feuille du bas : « Changement 2 sur 4 », titre du bloc, Avant / Maintenant / Pourquoi (mots de l'annonce surlignés), puis « Annuler ce changement » (pilule contour, large) et deux boutons ronds 52 px précédent / suivant (suivant en bleu plein).
- Recherche : la barre remplace la rangée d'outils (champ pilule, « 2 sur 2 », précédent, suivant, X).
- Le champ du bas dit « Demander une modification du CV ».

Liste Candidatures
- Pastille « Agence » en premier dans la rangée de pastilles (section 35), la carte reste à 2 lignes + pastilles.

## 38. Statuts des offres : des noms qui disent ce qu'il y a dedans

Planches : panneau Filtres de toutes les planches Candidatures ordinateur (clair et sombre), pages Alertes (ordinateur et téléphone), ExtAnnonce. Captures : captures/statuts/.

- Ordre des puces « Statut », celui du parcours d'une offre : Nouvelles · n / Gardées · n / En préparation · n / Toutes · n.
- « À examiner » devient « Nouvelles ». « Plus tard » / « Gardées » : « Gardées » (même mot que le bouton Garder, la pastille et le signet). « En préparation » ne change pas (même mot que « Préparer ma candidature »).
- « À traiter » devient « Toutes » : toutes les offres pas encore envoyées. C'est le choix par défaut, même s'il est en dernier.
- « En préparation » ne contient plus les offres envoyées (elles sont dans l'onglet Envoyées).
- Dans « Toutes », intertitre « En préparation » en tête de liste, puis les groupes par date (comme la planche).
- Le compteur de chaque puce tient compte des autres filtres actifs (bug du 415).
- Partout où « À traiter » apparaissait : « Les offres arrivent dans « Nouvelles » » (Alertes), « Elle t'attend dans Candidatures › Nouvelles » (extension), premiers pas, Assistant.

## 39. Cartes de rendez-vous : 2 lignes, hauteur selon le contenu

Planches : onglet Rendez-vous de toutes les planches Candidatures ordinateur (clair et sombre) ; RendezVous(+Sombre) au téléphone était déjà juste. Captures : captures/rendez-vous/.

- Section « À venir · n » en tête (remplace la pastille « Aucun rendez-vous à venir » quand il y en a un).
- Carte : calendrier 44 px (mois + jour) ; ligne 1 : titre (« Rendez-vous ORP ») + pastille sur la même ligne (« Feuille prête » vert #E3F3EA / #17734A ; « Entretien » neutre ; « À noter » orange) ; ligne 2 : heure · délai · lieu (« 9 h · dans 3 jours · ORP Renens »), coupée par « … ».
- Plus jamais 3 ou 4 lignes (« Dans 3 jours » au-dessus du titre, heure seule, pastille seule en dessous : non).
- Hauteur : min 80 px, padding 14 px 16 px, pas de rangée de pastilles vide. Les cartes Offres et Envoyées gardent 104 px (elles ont une vraie rangée de pastilles).

## 40. Téléphone : logos, Top du jour, offres à trier, fiche, frise, glisser, Trier en dossier

Téléphone seulement (décision de Kevin du 16.11). Planches (chacune + Sombre) : Candidatures, CandidaturesGlisser (nouvelle), AccueilV2, Offre, EnvoyeeDetail (EnvoyeeDetailSombre est nouvelle), TrierOffresV2 (états e = carte, garde, longue), TrierOffresCurseurGauche et TrierOffresCurseurDroite (nouvelles). Captures : captures/telephone-1611b/.

Logos d'entreprise
- Carré blanc 44 px (liste) ou 56 px (fiche, Trier), bord 1 px (#E5E2D9 / sombre #38322B), logo à 28 px (34 px dans la fiche), jamais recoloré ; le carré reste blanc en sombre.
- Source, du plus sûr au moins sûr : 1) logo fourni par le site d'emploi avec l'annonce ; 2) apple-touch-icon du site de l'entreprise ; 3) sinon les initiales sur fond neutre (#F1EEE7 / sombre #2C2722).
- Image enregistrée par jobA1 une fois par entreprise (pas de service tiers chargé à l'affichage). Moins de 64 px ou illisible : initiales.
- Les logos des planches sont inventés (entreprises fictives).

Pastille « Top du jour » (liste Offres)
- Tonale : fond #E3F3EA, texte #17734A, étoile 11 px (sombre #1C3527 / #62D497). En premier dans la rangée de pastilles.
- Jusqu'à 3 offres notées 75 et plus, pas encore envoyées. Aucune ce jour-là : pas de pastille.
- Les pastilles en trop se replient en « +N » ; la rangée reste sur une ligne. Les anneaux de note gardent leur épaisseur.

Glisser une carte de la liste pour l'écarter
- Vers la gauche seulement, depuis le milieu de la carte (pas depuis le bord : geste retour d'iOS). Dessous : zone grise (#ECE9E1 / #2C2722) avec croix et « Écarter ».
- Lâchée après la moitié : l'offre est écartée et le bandeau commun « Offre écartée · Annuler » apparaît. Avant la moitié : la carte revient.
- Les actions de la fiche restent (WCAG 2.5.7).

Accueil
- Ordre : À faire, ORP, Top du jour, 3 offres à trier.
- « Top du jour » : feuille verte (#E3F3EA / sombre #1C3527), titre 26 px, « Tout voir » à droite ; mêmes offres que la pastille ; lignes de 68 px : titre (1 ligne), entreprise · lieu, note 44 px, chevron. Aucune offre à 75 et plus : feuille absente.
- « 3 offres à trier » : sous-titre « Pas encore vues ». Jusqu'à 3 offres jamais ouvertes, jamais celles de « Top du jour ». Ligne : point bleu 10 px (« pas encore vue »), titre, puis entreprise · lieu · une raison surlignée comme les mots de l'annonce (<mark> #FFE9A8 / sombre #5A4A1E), note ou anneau en pointillés à droite. Bouton « Trier les offres » inchangé. Le titre suit le nombre (« 2 offres à trier ») ; zéro : feuille absente.

Fiche d'une offre
- Logo 56 px. Ligne de l'entreprise : « Alpstack · Lausanne · il y a 2 j ».
- Les 4 pastilles deviennent 3 cases nommées dans un cadre (bord 1 px, rayon 12 px) : Taux · Contrat · Télétravail (libellé 12 px #596070, valeur 15 px gras).
- En bas : carte « Autres offres chez {Entreprise} · N », lignes de 2 lignes (poste ; lieu · taux · date), pastille note ou « Envoyée », chevron, 44 px min. Absente s'il n'y a pas d'autre offre de la même entreprise.

Candidature envoyée : frise des étapes
- Dans la carte du haut, sous le statut : Envoyée → Réponse → Entretien → Décision. Faite : rond vert plein avec coche ; en cours : anneau orange (#8A4A16 / #F2B98E), libellé orange ; à venir : anneau gris. Trait vert jusqu'à l'étape en cours.
- <ol aria-label="Étapes de la candidature">, aria-current="step" sur l'étape en cours.

Trier : le dossier et le curseur
- Plus de contour bleu épais, plus de marque-page, plus de points ni de « 1 sur 3 » en bas.
- Carte = dossier : onglet blanc « Offre 1 sur 3 » soudé en haut à gauche (136 × 40 px), carte rayon 0 20 20 20, bord 1,5 px #CFCBC1, ombre légère. Derrière, les dossiers suivants en pêche (#FCEDE4 et #F8DCC8, comme la feuille de l'Accueil) avec leurs onglets « 2 » et « 3 » (non cliquables).
- Contenu aéré, la carte prend la hauteur libre : logo 56 px + titre 21 px (3 lignes max) ; note 56 px + « Proche de ton profil » ; pastilles 32 px ; citation de l'annonce 16 px ; points forts ; traits fins entre les 4 blocs ; lien « Voir l'offre complète » en bas de la carte.
- Barre du bas = un curseur : piste 64 px pleine largeur, « ✕ Écarter » à gauche, « Garder » à droite, rond bleu 52 px au milieu (flèches ↔). Glissé à gauche : remplissage gris foncé, « Lâche pour écarter », rond blanc avec croix ; à droite : remplissage bleu, « Lâche pour garder », rond blanc avec signet. Toujours 6 px entre le rond et le bord du remplissage. Lâché avant le bout : retour au milieu.
- Toucher « Écarter » ou « Garder » fait l'action sans glisser (deux vrais boutons pour un lecteur d'écran, WCAG 2.5.7).
- Après « Garder » : le dossier suivant passe devant (« Offre 2 sur 3 ») et le bandeau « Offre gardée dans tes candidatures · Annuler » apparaît au-dessus du curseur.

Animation Accueil → Trier
- Toucher « Trier les offres » : l'écran Trier monte depuis la feuille comme un dossier qu'on sort (léger penché, onglet « 3 offres à trier », Accueil assombri derrière), puis se redresse. 0,3 s en tout. Retour : mouvement inverse. prefers-reduced-motion : simple fondu. Captures : anim.png.

## 41. Premiers pas, étapes 2 et 3, et Candidatures vide (16.11.2026)

Planches : OnboardingOrdinateurEtape2, OnboardingOrdinateurAlerte, OnboardingOrdinateurAlerteCode, …CodeRecu, …CodeExpire, OnboardingC, OnboardingAlerteDebut, OnboardingAlerteCode, …Recu, …Expire, CandidaturesOrdinateurVideAlertes, CandidaturesVideAlertes, toutes avec leur version Sombre. Captures : premiers_pas_v3.png, premiers_pas_telephone.png.

Étape 2 « Quel travail cherches-tu ? »
- Un seul bloc de 3 lignes (Postes recherchés, Lieu, Taux d'activité), séparées par un trait, icône à gauche, bouton « Modifier » à droite (sur téléphone : bouton crayon 44 px avec aria-label « Modifier le lieu », etc.).
- Postes recherchés : liste à puces, un métier par ligne.
- Pastille verte « Depuis ton CV » collée à l'intitulé (Postes, Lieu) quand la valeur vient du CV.
- Bloc ORP : interrupteur « Je suis inscrit à l'ORP » + « Recherches à faire par mois » (− 10 +).
- Section Langues : une ligne par langue avec une liste déroulante, « Non renseigné » n'écarte aucune offre, lien « Ajouter une langue ».

Étape 3 « Crée ton alerte sur jobup »
- Une carte avec 4 étapes. Trait uniquement entre deux étapes. Pas de cadre bleu : l'étape en cours a seulement sa pastille bleue numérotée (aria-current="step"), les étapes faites une coche verte, les suivantes une pastille grise.
- Étape 1 : bouton plein « Ouvrir jobup avec ma recherche » (nouvel onglet). Une fois faite : lien « Rouvrir jobup ».
- Étape 2 : adresse jobA1 + bouton « Copier ».
- Étape 3 : 6 cases EN LECTURE SEULE. Le code n'est jamais saisi dans jobA1 : le serveur le reçoit dans la boîte jobA1 et l'affiche, la personne le recopie sur jobup. États :
  - attente : cases vides + « En attente du code de jobup. Il s'affiche ici dès qu'il arrive, tu n'as rien à faire. » (role="status") ;
  - reçu : cases remplies, contour vert, bouton « Copier le code », l'étape 4 devient l'étape en cours « Colle le code sur jobup et valide l'alerte » ;
  - expiré : cases vides + « Ce code a expiré. Sur jobup, demande un nouveau code : il s'affichera ici. » (orange).
- Bouton principal : « J'ai créé l'alerte », puis « J'ai validé l'alerte » une fois le code reçu. « Plus tard » reste à côté.
- Le code n'apparaît jamais dans les logs.

Candidatures vide (avant les premières offres)
- Titre « Tes premières offres arrivent bientôt » + phrase « jobA1 récupère les nouvelles offres de tes alertes et les ajoute ici, sans que tu aies rien à faire. »
- Pastille : « En attente des premières offres · prochaine vérification ce soir vers 18 h » (téléphone : « Prochaine vérification ce soir vers 18 h », pour tenir sur une ligne).
- Le lien « Faire une candidature spontanée » est retiré de cet état (il reste dans « Ajouter »).

Plus tard (hors de cette livraison) : avec l'extension du navigateur, le formulaire jobup est déjà rempli et le code collé tout seul.
