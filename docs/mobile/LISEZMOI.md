# jobA1, maquette de référence (8 novembre 2026)

Ce paquet remplace tous les précédents. Il ne contient que les écrans retenus.
Tout fichier absent d'ici (CandidaturesOrdinateur, RendezVousOrdinateur, AujourdhuiOrdinateur, AujourdhuiOrdinateurTravail, B et C, Onboarding 1, 2, 3 et B, Cercles, Main, Personnage) est abandonné : ne pas l'implémenter.

## Contenu
- `MODIFICATIONS_8_NOVEMBRE_SOIR.md` : texte complet et précis des lots 11 à 15 (corrections du soir), à suivre après `PROMPT_CLAUDE_CODE.md`.
- `maquettes/` : 67 écrans `.dc.html` (à ouvrir dans un navigateur) et `canvas.json` (titres et positions, rangés par section).
- `captures/` : un PNG par écran, du même nom, dans l'état par défaut. `captures/etats/<Fichier>--<état>.png` montre les états ouverts (menus, panneaux, onglets, sélecteur de date). `vue_ensemble.png` montre tout le canvas. `icone_calendrier.png` montre l'icône date.
- `illustrations/` :
  - `personnage/` : 12 poses en `-400.webp` (téléphone) et `-800.webp` (ordinateur). 01 debout, 02 bonjour, 03 cv, 04 marche, 05 assis, 06 perplexe, 07 révélation, 08 avion, 09 câbles, 10 hors ligne, 11 loupe, 12 célébration.
  - `avatars/` : 8 avatars (Souriant, Clin d'œil, Casque, Lunettes, Bonnet, Écharpe, Café, Étoile), en 128 et 256 px WebP et 256 px PNG, découpés en cercle.
  - `icones/calendrier-date.html` : modèle de l'icône calendrier.
  - `accessoires/`, `fonds/` : SVG avec les jetons de couleur.
- Pour le code, utiliser les fichiers de `illustrations/` et non les images intégrées dans les maquettes.

Le bloc Get'emAll (connexion job-bot #512, 7 écrans) est sur le canvas mais pas dans ce paquet : il appartient à un autre chantier.

Les couleurs écrites en hexadécimal dans ce document et dans les maquettes se traduisent en jetons avec le tableau §3 de PROMPT_CLAUDE_CODE.md. Les rayons suivent D7 (§4 du même fichier).

# INDEX TÉLÉPHONE (largeur <= 820 px, décision D8)

| Page | Fichier | Sombre |
|---|---|---|
| Accueil | AccueilSmile | AccueilSombre |
| Candidatures, à traiter | Candidatures | CandidaturesSombre |
| Candidatures, envoyées | Envoyees | EnvoyeesSombre |
| Candidatures, rendez-vous (états vue, noter, dp) | RendezVous | RendezVousSombre |
| Détail d'une offre | Offre | OffreSombre |
| Offre provisoire, lire ou coller l'annonce | OffreProvisoire | |
| Ajouter une offre (feuille du bas) | AjouterOffreTel | |
| Filtres (feuille du bas) | Filtres | |
| Actions sur une offre | ActionsOffre | |
| Préparer ma candidature | Preparer | PreparerSombre |
| Assistant | Assistant | |
| Suivi ORP | Orp | |
| Progresser, appelé « Bilan » dans la barre du bas | Explorer | ProgresserSombre |
| Bilan, résultats | BilanResultats | |
| Notifications | Notifications | NotificationsSombre |
| Compte | Compte | CompteSombre |
| Compte, choisir son image | CompteImage | |
| Alertes e-mail | AlertesTel | |
| Réglages | Reglages | |
| Premiers pas | OnboardingC | |
| Connexion | Connexion | ConnexionSombre |
| Candidature envoyée | CandidatureEnvoyee | |
| Objectif ORP atteint | ObjectifAtteint | |
| Aucune offre | AucuneOffre | |
| Erreur et attente | ErreurConnexion | |
| Maintenance, mise à jour / annoncée | MaintenanceMaj, MaintenanceAnnoncee | MaintenanceSombre |
| Pas de connexion | MaintenanceHorsLigne | |
| Page introuvable | PageIntrouvable | PageIntrouvableSombre |

# INDEX ORDINATEUR (largeur > 820 px, décision D8)

| Page | Fichier | États à tester |
|---|---|---|
| Aujourd'hui, jour de travail | AujourdhuiOrdinateurTravailD | menu = compte, notif |
| Aujourd'hui, jour de repos | AujourdhuiOrdinateurReposD | menu = compte, notif |
| Candidatures (à traiter, envoyées, rendez-vous) | CandidaturesOrdinateurB | tab = tr, en, rv ; q ; menu = compte, notif, actions, filtres, ajouter ; dp = cal |
| Préparer ma candidature | PreparerOrdinateur | tab = let, cv, pos |
| Bilan (ORP, résultats, formations) | BilanOrdinateur | tab = orp, res, form |
| Assistant (panneau latéral) | AssistantOrdinateur | plus, file |
| Mon profil et mon CV | ProfilOrdinateur | pick, pv, av |
| Toutes les notifications | NotificationsOrdinateur | tab = all, un |
| Mes alertes e-mail | AlertesOrdinateur | |
| Réglages | ReglagesOrdinateur | |
| Connexion | ConnexionOrdinateur | |
| Premiers pas | OnboardingOrdinateur | step = 1, 2, 3 |
| Candidature envoyée | CandidatureEnvoyeeOrdinateur | |
| Objectif ORP atteint | ObjectifAtteintOrdinateur | |
| Aucune offre (filtres) | AucuneOffreOrdinateur | |
| Page introuvable | PageIntrouvableOrdinateur | |
| Maintenance (sans menu) | MaintenanceOrdinateur | |
| Pas de connexion (sans menu) | HorsLigneOrdinateur | |

Extension navigateur (360 x 480) : ExtAnnonce, ExtAlerte, ExtAutreSite, ExtNonConnecte.
Système : Systeme (règles communes), Emoticones, Animations (logo isolé, plus une référence), ModeSombre (jetons sombres, valables aussi sur ordinateur).

# RÈGLES COMMUNES

## Illustration
- Logo transformé (soleil, loupe, cloche, roue dentée, cravate…) : indique où l'on est.
- Personnage : seulement sur les écrans « moment » (pages d'état, premiers pas). Statique, décoratif (alt="" aria-hidden="true"). Jamais sur un écran de travail. Sur ordinateur : 240 px de haut, 360 px aux premiers pas.
- Petites mascottes d'humeur : un état dans un petit espace (chargement, erreur dans la page, notifications).
- Un seul des trois par écran.

## Cartes, boutons, icônes
- Carte (fond blanc, bordure) = cliquable, toute la carte est le lien. Information seule = pas de cadre, traits gris légers #ECE9E1 entre les lignes.
- Dans une carte cliquable, pas de bouton : libellé coloré (couleur du ton, 15 px, gras) suivi de ›.
- Un seul bouton plein par écran. Les autres ont un contour.
- Icônes seules, sans pastille de fond coloré. Tons : #8A4A16 retard, #2445C2 normal, #17734A entretien.
- Éléments interactifs : 44 px minimum.
- Barres de défilement : 8 px, pouce #C9C5BA, #A9A397 au survol, piste transparente.

## Titres
- Accent manuscrit Caveat Brush sur la fin du H1 seulement (« repos. », « à envoyer. », « te revoir. »), 1.45em, #2445C2. Un seul par écran, seulement sur les écrans « moment ». Le H1 reste un seul élément.

## Mise en page ordinateur
- En-tête commun (AppHeader) aligné sur 1280 px. À droite, un seul groupe : bulle de recherche, cloche, avatar, 16 px entre eux (les 32 px séparent logo, menu et ce groupe). Les trois font 44 px. Cloche sans notification : rond blanc, bordure 1,5 px #D8D4CA, comme la recherche (état `lu`). Avec notifications : capsule pêche « 9+ ». Logo seul sur Maintenance, Pas de connexion, Premiers pas et Connexion.
- Pages de lecture (Aujourd'hui, Bilan, Notifications, Alertes, Réglages, Profil, pages d'état) : contenu centré sur 880 px. Pages de travail (Candidatures, Préparer) : 1280 px.
- Bande bleu pâle #E8ECFB (sombre #232B45) sous l'en-tête : seulement Aujourd'hui et Bilan. Elle porte la date, le H1 et le sous-titre. La carte du haut (Mois ORP) est à cheval sur son bord bas, bordure #D5DCF5, ombre 0 4px 16px rgba(36,69,194,.10).
- Aujourd'hui : H1 = action du jour, calculée sur le rythme qu'il faut pour tenir l'objectif ORP. Tâches sur une colonne : en retard, envoyer, trier, préparer un entretien, puis « Quand tu as le temps ».
- Candidatures : liste à gauche (cartes de 104 px), détail à droite, jamais vide (premier élément choisi par défaut). Filtre de liste « Filtrer par titre ou entreprise » + « Plus de filtres ».
- Mode sombre : jetons de la planche ModeSombre (fond #171411, surfaces #221E1A, bordure #38322B, texte #F3EEE6).

## Recherche globale (ordinateur)
- Bulle ronde de 44 px, fond blanc, bordure 1,5 px #D8D4CA. Au clic : 380 px (transition width .22s), bordure 2 px #2445C2, champ « Offres, candidatures, entreprises » et Fermer. Échap ferme.

## Panneaux et menus (ordinateur)
- Cloche et K : panneau latéral non modal de 420 px à droite, sous l'en-tête, sans voile, coin haut gauche à 24 px, ombre -12px 0 32px rgba(27,31,42,.12). Focus sur le titre à l'ouverture, retour au déclencheur à la fermeture.
  - Notifications : groupes « Nouvelles » et « Plus tôt », point bleu si non lue, pied « Voir toutes les notifications ».
  - Compte : avatar 48 px, nom, e-mail ; « Mon compte » (Profil et CV, Alertes e-mail, Réglages), « Affichage » (Clair, Auto, Sombre), « Aide » ; pied « Se déconnecter » #B4371F.
- Assistant : bouton flottant en bas à droite, panneau de 480 px de la même famille. Masqué quand un panneau, les filtres ou le sélecteur de date sont ouverts.
- Plus de filtres : le panneau remplace la colonne liste (480 px). « ‹ Retour à la liste », pastilles aria-pressed, pied fixe « Tout effacer » et « Afficher n offres ».
- Menu « … » d'un élément : role="menu", 280 px, ancré sous son bouton.
- Un seul panneau ou menu ouvert à la fois. Couche transparente (z-index 35) : un clic à l'extérieur ferme tout. L'en-tête reste au-dessus (z-index 38) : cloche et K basculent directement de l'un à l'autre. Les filtres gardent leurs choix.
- Clavier : flèches entre les éléments, Échap ferme et rend le focus.

## Animations
Keyframes ja-slide-r, ja-slide-l, ja-pop, déjà dans les maquettes. Aucune animation si prefers-reduced-motion.
- Panneaux latéraux : 24 px depuis la droite + fondu, 220 ms, cubic-bezier(.05,.7,.1,1). Fermeture 160 ms ease-in.
- Filtres et sélecteur de date : 16 px depuis la gauche + fondu, 200 ms.
- Menu « … » : depuis le coin du bouton, échelle 0,96 vers 1 + fondu, 150 ms ease-out.
- Jamais plus de 250 ms, jamais de blocage de la saisie.

# COMPOSANTS PARTAGÉS

## Zone de saisie (Composer)
Pour tout message libre envoyé tel quel.
- Une ligne : pilule min-height 56 px, rayon 28 px, fond blanc, bordure 1 px #E5E2D9, ombre 0 2px 10px rgba(27,31,42,.07). Bouton + (44 px, « Joindre un fichier »), champ (16 px, jusqu'à 6 lignes puis défile), micro (44 px, « Dicter »), Envoyer (cercle bleu de 44 px, désactivé si vide).
- Plusieurs lignes : texte sur toute la largeur en haut, barre du bas avec + à gauche et Envoyer à droite, rayon 24 px.
- Menu + (ja-pop) : Importer un fichier (PDF, Word, image, 10 Mo), Joindre mon CV, Joindre une offre de ma liste. Pièces jointes en pastilles dans la pilule. Glisser-déposer accepté. Entrée envoie, Maj + Entrée passe à la ligne.
- Mention sous l'Assistant : « L'Assistant peut se tromper. Relis toujours avant d'envoyer. »
- Emplacements : Assistant ; Préparer (« Demander une modification de la lettre », pastilles Plus court, Plus formel, Insister sur Terraform, En allemand) ; Ajouter une offre (3 lignes ordinateur, 4 lignes téléphone, « Lien ou texte de l'annonce », Envoyer = « Ajouter l'offre ») ; Coller l'annonce dans OffreProvisoire (5 lignes, « Enregistrer et refaire la note », désactivé sous 200 caractères).
- Les champs de formulaire restent des champs de formulaire : libellé au-dessus, hauteur 48 px, bordure 1,5 px #596070 (--text-secondary), fond blanc (--surface), rayon 8 px, sans + ni Envoyer. Une seule règle pour tous les formulaires, y compris ceux qui ne sont pas dessinés (Coordonnées).

## Logo de l'Assistant
- Sans cercle dans la discussion : 32 px dans l'en-tête du panneau, 28 px à gauche de chaque message. Pas d'avatar pour les messages de l'utilisateur. L'icône de la barre du bas (téléphone) garde son cercle.

## Image de profil
- Initiales (défaut), 8 avatars ou photo (JPG ou PNG, 5 Mo, recadrage en cercle). Contour 1 px #E5E2D9.
- Choix en grille, aria-pressed, anneau bleu de 3 px ; Annuler ou Enregistrer. Texte : « Elle s'affiche seulement dans jobA1. Elle n'est jamais envoyée aux employeurs. »
- Remplace le K partout : en-tête 40 px, panneau Compte 48 px, Profil 72 px. Nom accessible « Compte de Kevin ».

## Date et heure
- Déclencheurs en pilule : 52 px, rayon 26 px, bordure 1,5 px #8C8478, icône calendrier ou horloge bleue, valeur en toutes lettres (« Mardi 10 novembre 2026 », « 9 h 30 »), chevron.
- Le sélecteur prend la place du formulaire, pas de popover. Ordinateur : « ‹ Retour au formulaire », calendrier à gauche (raccourcis Demain, Lundi prochain, Dans 2 semaines, Dans 1 mois ; grille de 6 semaines, lundi en premier ; jour choisi en rond bleu, aujourd'hui en anneau, jours passés désactivés ; saisie jj.mm.aaaa), heure à droite (créneaux de 30 min de 8 h à 16 h, saisie hh:mm, encadré bleu pâle et « Valider »). Téléphone : même contenu en plein écran, « Valider » collé en bas.
- Échap ou Retour annule. Flèches pour les jours, Page haut et bas pour les mois, Entrée valide. aria-label complet sur chaque jour.

## Icône calendrier avec la date (CalendarDate)
- Au trait : contour arrondi 2,5 px, deux anneaux, mois abrégé en capitales en haut, jour en gras au centre, fond blanc (#221E1A en sombre). Remplace les carrés colorés partout.
- Tons : blue #2445C2 (à venir), orp #B4631F (ORP ou à noter), past #8C8478 (passé). Sombre : #AEBDFF, #F2B98E, #8C8478.
- Tailles : 36 px (Bilan), 44 px (listes ordinateur), 48 px (téléphone), 56 px (en-tête de détail). aria-hidden si la date est écrite à côté.

# TÉLÉPHONE ⇄ ORDINATEUR

Un même élément a le même dessin et le même comportement sur les deux supports (WCAG 3.2.4, NN/g « Consistency and standards »). Seul le conteneur change (Material Design 3, fenêtres compacte et étendue).

## Partagés
| Élément | Téléphone | Ordinateur |
|---|---|---|
| Composer | Assistant, Preparer, OffreProvisoire, AjouterOffreTel | AssistantOrdinateur, PreparerOrdinateur, CandidaturesOrdinateurB (ajouter) |
| Pastilles de suggestions | Preparer, PreparerSombre | PreparerOrdinateur |
| Logo de l'Assistant sans cercle | Assistant | AssistantOrdinateur |
| Icônes sans fond | partout | partout |
| CalendarDate | RendezVous | CandidaturesOrdinateurB, Aujourd'hui, Bilan |
| Pilules et sélecteur de date | RendezVous (plein écran) | CandidaturesOrdinateurB (à la place du formulaire) |
| Image de profil | Compte puis CompteImage | ProfilOrdinateur |
| Alertes e-mail | AlertesTel | AlertesOrdinateur |
| Carte = cliquable, libellé › | partout | partout |

## Différences voulues (ne pas « harmoniser »)
| Élément | Téléphone | Ordinateur | Raison |
|---|---|---|---|
| Filtres | feuille du bas | à la place de la liste | Material 3 : bottom sheet en fenêtre compacte |
| Notifications, Compte | pages entières | panneaux de 420 px | Apple HIG, navigation par pile sur iPhone |
| Ajouter une offre | feuille du bas | dialogue | conteneur adapté |
| Sélecteur de date | plein écran | à la place du formulaire | même logique, taille différente |
| Bande bleu pâle, colonne de 880 px | absentes | pages « moment » | pas la place sur 390 px |
| Navigation | barre d'onglets en bas | menu du haut | Apple HIG, Material 3 |
| Recherche | champ en haut de liste | bulle qui se déploie | |

## Pas encore dessinés
Attente de la première collecte, entretien décroché, refus reçu, compte supprimé : reprendre la mise en page de l'écran d'état le plus proche.

# CORRECTIONS DU 8 NOVEMBRE AU SOIR

| Point | Maquette, état | Capture |
|---|---|---|
| Champs de formulaire : rayon 8 px, bordure 1,5 px #596070, fond blanc | RendezVous, CandidaturesOrdinateurB, Connexion | captures/etats/CandidaturesOrdinateurB--tab-rv.png |
| En-tête : groupe de 16 px, éléments de 44 px, cloche sans notification | toutes les pages ordinateur, état `lu` | captures/etats/CandidaturesOrdinateurB--cloche-sans-nouvelle.png |
| Assistant qui écrit : logo sans cercle + bulle de 3 points animés, aucune bulle vide | AssistantOrdinateur `attente`, Assistant `phase: ecrit` | captures/etats/AssistantOrdinateur--attente.png, Assistant--ecrit.png |
| Mes alertes : lien « ‹ Candidatures » au-dessus du titre ; liste sans cadre ; « Créer l'alerte › » en libellé coloré | AlertesOrdinateur, AlertesTel | captures/AlertesOrdinateur.png, AlertesTel.png |
| Nouveau rendez-vous sur ordinateur : formulaire dans le panneau de détail, sans carte autour (titre, Date, Heure, Lieu ou lien, Ajouter le rendez-vous, Annuler) | CandidaturesOrdinateurB `tab: rv, ajrv: true` (bouton « Ajouter ») | captures/etats/CandidaturesOrdinateurB--tab-rv-ajouter.png |
| Envoyées, détail sur ordinateur en deux colonnes : à gauche Statut, Premier message, Prises de contact ; à droite (240 px, trait à gauche) Documents, Contacts. Formulaire d'une seule colonne (Écrire à, puis Canal). Espacements généreux : 32 px au-dessus et 36 px sous chaque section, 48 px entre les colonnes, 40 px de marge dans la colonne de droite | CandidaturesOrdinateurB `tab: en` | captures/etats/CandidaturesOrdinateurB--tab-en.png, --tab-en-bas.png |
| À traiter, détail sur ordinateur en deux colonnes : à gauche la note (anneau, raisons, bandeau « Il manque l'annonce complète » en bloc arrondi, « Le détail de la note ») puis « Le poste » ; à droite « L'offre en bref » (Lieu, Contrat, Taux d'activité, Reçue, libellé au-dessus de la valeur) et « Voir l'annonce sur le site ». Titre, étiquettes et boutons restent au-dessus des colonnes. Mêmes espacements qu'Envoyées | CandidaturesOrdinateurB `tab: tr` | captures/CandidaturesOrdinateurB.png, captures/etats/CandidaturesOrdinateurB--tab-tr-bas.png |
| Formulaires de rendez-vous sur ordinateur limités à 560 px de large | CandidaturesOrdinateurB `tab: rv` et `ajrv` | captures/etats/CandidaturesOrdinateurB--tab-rv.png, --tab-rv-ajouter.png |
| « Ce que je cherche » : libellé au-dessus de la valeur (14 px gris, puis 16 px gras), lignes de 68 px, chevron à droite | ProfilOrdinateur, OnboardingOrdinateur | captures/ProfilOrdinateur.png |
| Rendez-vous ORP sur ordinateur : plus de pastille « Noté » ni « Pas encore noté » (les groupes « À noter » et « Passés » le disent déjà). Détail structuré : sous l'en-tête, « Ce qui a été convenu » en trois sections titrées avec une phrase d'aide (Objectif de recherches, Mesures décidées, Prochain rendez-vous), séparées par un trait, puis « Enregistrer » ; à droite « Le rendez-vous » (Date, Heure, Lieu, Objectif jusqu'ici). Date courte dans la pilule : « Mar. 10 nov. 2026 » | CandidaturesOrdinateurB `tab: rv` | captures/etats/CandidaturesOrdinateurB--tab-rv.png, --tab-rv-bas.png |
| Préparer sur ordinateur, réorganisé comme la production : en-tête sur une ligne de 64 px centrée (« ‹ Retour à l'offre », logo, H1 = intitulé du poste, entreprise, anneau 76 + verdict, étapes) ; « Ma candidature » n'est plus affiché. À gauche la lettre (titre « Lettre de motivation », langue FR, DE, EN à droite, aperçu). À droite : « Mise en page » (modèle Sobre, Moderne, Bandeau, Classique, pour la lettre et le CV, longueur), « Pour cette offre » (deux groupes titrés « Points forts » avec coche et « À vérifier » avec point d'attention, sujet en gras et détail dessous), « Nouvelle version ». Le verdict n'est plus répété dans « Pour cette offre ». En bas : suggestions, zone de saisie, « J'ai relu la lettre » | PreparerOrdinateur | captures/PreparerOrdinateur.png, captures/etats/PreparerOrdinateur--colonne-bas.png |
| À traiter : bouton à contour « J'ai déjà postulé » à droite de « Écarter » | CandidaturesOrdinateurB `tab: tr` | captures/CandidaturesOrdinateurB.png |
