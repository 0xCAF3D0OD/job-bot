# Version ordinateur, corrections du 9 novembre 2026

Ce document prime sur tout le reste pour la version ordinateur (largeur > 820 px).
Il applique à l'ordinateur les règles validées sur téléphone (MODIFICATIONS_8_NOVEMBRE_SOIR.md, D24, D28 à D35, §2.9, §2.10), sans changer la mise en page en 2 colonnes.
Les panneaux venant du bas sur téléphone deviennent des panneaux latéraux à droite (440 à 480 px, voile rgba(27,31,42,.45), animation ja-panel 250 ms, fermeture par la croix, Échap ou clic sur le voile).

Captures avant / après : `captures/commentees/`.

## 1. Règles communes

| Règle | Contenu |
|---|---|
| Fond | Crème #F7F5F0 partout. Plus de bande bleue sous l'en-tête, sauf Aujourd'hui qui la garde comme point focal (§11). |
| Cartes | Carte cliquable : blanche, bordure 1,5 px #CFCBC1, rayon 18, marge intérieure 20 px (18,5 + bordure). Carte d'information : même style, sans flèche. Jamais de carte dans une carte. |
| Listes | Une carte par élément, 8 px entre les cartes. Plus de conteneur blanc rempli de lignes. |
| Flèches | Cercle de 36 px, trait 2 px **#596070 (sombre #ABA398)**, à 20 px du bord droit de la carte (§10.1). Chevron simple de 24 px dans les lignes d'un panneau. |
| Défilement | Une seule zone défile : la page. Pas de défilement interne dans une colonne, une carte ou une liste. La colonne de droite est sticky et doit tenir dans 900 px. |
| Action principale | Visible sans défiler. Un seul bouton plein par écran. |
| Champs | Pilule (rayon 24 ou 28), marge gauche 20 px, bordure 1,5 px #8C8478 ; au focus un seul contour 2 px #2445C2 (pas de double trait). Zones de texte : rayon 20. |
| Boutons | Toujours en pilule, largeur du contenu (jamais 100 % de la page, sauf dans le pied d'un panneau). |
| Copier | Icône de 40 px, cercle bordure 1,5 px #CFCBC1, aria-label « Copier : <libellé> », info-bulle « Copier ». Lignes de 56 px, libellé (13 px) au-dessus de la valeur (16 px). |
| Valeurs vides | « Non renseigné » en gris, jamais un tiret seul. |
| Textes | Apostrophe typographique ’ partout. Accord au singulier pour 0 et 1. Noms en français (CICR, Genève). Téléphone affiché espacé (+41 76 430 43 21), copié brut. |
| Cibles | Au moins 24 px sur ordinateur (WCAG 2.5.8), décidé le 9 novembre (§11). 44 px sur téléphone. |

## 2. Écrans

### 2.1 Candidatures (CandidaturesOrdinateurB)
- La note de l'offre est une carte d'information (crème sur la carte blanche du détail) avec une ligne « Voir la compatibilité » alignée sur le texte de la note. Elle ouvre le panneau Compatibilité (état `cmp`), même contenu que la feuille du téléphone (Points forts, À vérifier, « Comment la note est calculée »).
- « Écarter » agit tout de suite (état `ec`) : l'offre sort de la liste, le détail affiche « Choisis une offre », un message en bas « Offre écartée » avec « Annuler » en bleu clair #AEBDFF, 6 secondes.
- « + Ajouter » remplace « Ajouter une offre » et le lien « Postuler spontanément » : voir 2.6.

### 2.2 Préparer : Lettre (PreparerOrdinateur, PreparerOrdinateurLettreVide, PreparerOrdinateurRelecture)
- En-tête de page : retour, logo, titre, note avec « Proche de ton profil » et le lien « Voir la compatibilité › » (panneau), puis les étapes 1. Lettre, 2. CV, 3. Postuler (onglets de 44 px).
- Zone document : toujours une page A4 (560 x 792 px) dans le modèle choisi. Pas encore générée : lignes grisées dans le modèle et une carte au centre « Pas encore de lettre pour cette offre », texte d'explication et bouton plein « Générer la lettre », visible sans défiler. Changer de modèle change l'aperçu tout de suite.
- Langue de la lettre : FR / DE / EN en haut du document, seulement. La puce « En allemand » est retirée.
- Colonne de droite (360 px, sticky) : carte Mise en page avec 4 vignettes de modèle (Sobre, Moderne, Bandeau, Classique, 48 x 64 px) sur une ligne, puis « Tient sur une page A4 · 248 mots » ; carte « Cette lettre » avec 2 lignes : Relecture (« 7 sur 7, rien à renforcer » en vert, ouvre le panneau Relecture) et Versions · 3 (version actuelle et heure, ouvre le panneau Versions) ; bouton plein « J’ai relu la lettre ».
- Panneau Relecture : résultat, date, puis les 7 critères vérifiés (entreprise, poste, compétences demandées, exemple concret, longueur, ton, orthographe), icône cercle au trait de 24 px.
- Zone de saisie collée en bas de la colonne gauche (sticky) : 3 puces de 40 px (Plus court, Plus formel, Insister sur …), pilule de 56 px, texte à 20 px du bord, micro et Envoyer de 40 px. Pas de bouton + ici (on modifie, on ne joint rien).
- La page défile seule ; plus de défilement dans le document ni dans la colonne.

### 2.3 Préparer : CV (PreparerOrdinateurCV)
- Même structure que la lettre. Pas encore généré : page A4 grisée dans le modèle (photo, nom, sections) et carte « Pas encore de CV adapté à cette offre » avec « Générer le CV adapté ». Texte : le CV d'origine ne change pas.

### 2.4 Préparer : Postuler (PreparerOrdinateurPostuler)
- En haut, carte « Où postuler » : site (« Sur LinkedIn »), explication, ligne « À joindre : Lettre.pdf · CV.pdf » (pastilles avec téléchargement), bouton plein « Postuler sur LinkedIn ↗ » (largeur du contenu) et lien « J’ai déjà postulé ».
- Carte « À recopier sur le formulaire » : lignes de 56 px avec icône copier (voir §1). La lettre en texte est coupée à 2 lignes, la copie prend tout.
- Colonne de droite : carte Entreprise (Nom, Adresse avec sa source, Site), ligne « Contacts · 2 » qui ouvre un panneau ; carte « Après l’envoi » (déclaration ORP et relance à 7 jours).

### 2.5 Bilan, ORP (BilanOrdinateur, BilanOrdinateurFiche)
- Famille « À déclarer à l’ORP · n » en premier : une carte par candidature (date d'envoi en icône calendrier, entreprise, poste et mode, mot d'état « Prête » vert ou « Infos à compléter » orange, cercle flèche). « Voir les n autres » en lien.
- Puis « Recherches de novembre » (déjà déclarées, justificatif joint ou à joindre), puis « Rendez-vous ORP ». Toutes en cartes séparées.
- Panneau « Pour l’ORP » (480 px) : bouton « Ouvrir Job-Room ↗ » dans l'en-tête ; résumé (entreprise, poste, date d'envoi) ; encadré orange si une info manque ; groupe « La recherche » (Date, Mode avec l'étiquette « Case à cocher dans Job-Room », Poste, Lien de l’annonce coupé sur 1 ligne avec copie) ; groupe « L’entreprise » (Nom, Rue et numéro avec « Compléter » si vide, NPA et lieu, Pays, Personne contactée) ; pied fixe avec « Marquer comme déclarée » et la phrase « Elle passe dans « Recherches de novembre » ». Rien ne déborde, libellé au-dessus de la valeur.
- Mois affiché : le mois en cours. Les candidatures du mois précédent restent dans « À déclarer » tant qu'elles ne sont pas marquées (délai : le 5 du mois suivant, ORP_DEADLINE_DAY = 5, §11).

### 2.6 Ajouter (CandidaturesOrdinateurAjouter, CandidaturesOrdinateurSpontanee)
- Un seul bouton « + Ajouter » dans Candidatures. Il ouvre un panneau de 480 px avec un choix en 2 onglets : « Une offre » et « Candidature spontanée » (états `ajt` = of, sp).
- Une offre : phrase d'explication 15 px ; zone de texte 3 lignes qui s'agrandit (rayon 20) ; sous le champ « 0 offre ajoutée sur 20 ces 24 heures. » ; bouton à contour « Importer le PDF de l’annonce » ; pied « Ajouter l’offre ».
- Candidature spontanée : Entreprise, Poste visé (exemple sous le champ, pas dans le champ), Site de l’entreprise (facultatif), Pourquoi cette entreprise (zone de texte 4 lignes, aide sous le champ) ; tous les champs en pleine largeur ; pied « Créer la candidature ».

### 2.7 Aucune offre (AucuneOffreOrdinateur)
- Groupe centré : illustration, titre, phrase, « Tout effacer » et « Modifier les filtres » (plein). Sous un trait de 420 px : « Tu vises une entreprise précise, même sans offre ? » et le lien « Faire une candidature spontanée › » qui ouvre le panneau 2.6.

### 2.8 Alertes e-mail (AlertesOrdinateur)
- Familles « À confirmer », « Actives », « À créer » (titre en capitales 13 px de la couleur du statut, phrase d'explication), une carte par alerte avec mot d'état à droite et cercle flèche. Panneaux : alerte active (`al`) et alerte à confirmer (`cf`, bouton plein « Confirmer sur Indeed ↗ »). Plus de bandeau, d'étiquettes ni de menu « … ».

### 2.9 Profil (ProfilOrdinateur)
- « Ce que je cherche » : une carte par préférence. Mon CV et Compétences : cartes d'information avec bordure.

### 2.10 Réglages (ReglagesOrdinateur)
- Groupes avec bordure 1,5 px. Langue et Taille du texte deviennent des lignes (valeur + chevron) qui ouvrent un panneau à boutons radio (`lg`, `tx`). Textes des notifications alignés sur le téléphone (relance à 7 jours, objectif ORP 5 jours avant la fin du mois).

### 2.11 Notifications
- Inchangées sur ordinateur (validées le 9 novembre).

## 3. Questions ouvertes
Toutes tranchées le 9 novembre au soir, voir §11 (24 px, bande bleue gardée, ORP_DEADLINE_DAY = 5). Maquettes sombres de l'ordinateur : les écrans principaux seulement, pour fixer la ligne artistique.

## 4. Téléphone : déconnexion (ajout du 9 novembre)
- Compte et CompteSombre : nouveau groupe tout en bas, après « Confidentialité et aide », séparé par un trait.
- Une ligne de 56 px « Se déconnecter » : icône de sortie 24 px et texte en rouge (#B4371F, sombre #FF9B85, nouveau jeton `--danger-dark`), e-mail du compte en 2e ligne, pas de flèche (c'est une action, pas une page).
- Action immédiate, sans confirmation, retour à l'écran Connexion. La déconnexion reste dans Compte, loin de « Supprimer mon compte » (Réglages) pour ne pas confondre les deux.
- Ordinateur : inchangé, « Se déconnecter » reste au pied du panneau Compte.

## 5. Premiers pas et nouveau compte (ordinateur)

### 5.1 Grille commune aux 3 étapes
- Conteneur de 1080 px centré, en-tête aligné dessus : logo à gauche, « Étape n sur 3 » et les 3 traits à droite. Plus de « Passer » (doublon de « Continuer sans CV »).
- Colonne de contenu 640 px à gauche, illustration 360 px à droite, 80 px entre les deux, aux 3 étapes. Le contenu ne bouge plus d'une étape à l'autre.
- Les boutons suivent le contenu (32 px sous le dernier bloc) : « Retour » à contour à gauche, bouton plein à droite, aligné sur le bord de la colonne. Un seul bouton plein par écran.

### 5.2 Étape 1 (OnboardingOrdinateur, OnboardingOrdinateurLecture, OnboardingOrdinateurCV, OnboardingOrdinateurCoupure)
- Sans CV : zone « Glisse ton CV ici » avec « Choisir un fichier » (seul bouton plein) ; en bas, deux liens : « Pas de CV à jour ? L’Assistant t’aide à en créer un » et « Continuer sans CV ».
- Après l'envoi : carte du fichier, barre de lecture, « Tu peux continuer, on termine pendant ce temps ». L'analyse tourne en tâche de fond (POST 202 + job_id), elle ne bloque pas l'écran.
- CV lu : « Lu : 3 postes, 14 compétences, 1 lieu trouvés » en vert, lien « Changer ». Pas de pastille colorée autour de l'icône.
- Coupure : la page reste en place, la barre passe en orange « En pause » (« Ton CV est bien enregistré… »), message en bas « Connexion interrompue. Nouvel essai dans 5 secondes. Réessayer ». L'écran « jobA1 se met à jour » est réservé à une vraie maintenance (503 + en-tête X-Maintenance).

### 5.3 Étape 2 (OnboardingOrdinateurEtape2)
- Titre « Tes critères », sous-titre « Repris de ton CV ». Une carte par critère (Postes, Lieux, Taux d’activité), étiquette verte « Trouvé dans ton CV » quand c'est le cas ; la carte ouvre un panneau pour modifier.
- Carte ORP : interrupteur « Je suis inscrit à l’ORP » et « Recherches par mois » avec boutons − et + de 40 px (vrai signe moins).
- Si la lecture du CV n'est pas finie, les cartes affichent « Lecture du CV… » puis se remplissent.

### 5.4 Étape 3 (OnboardingOrdinateurEtape3)
- « 3 offres pour toi » : jobA1 a lu 312 offres, ces 3 correspondent le mieux ; Écarter / Garder sur chaque carte ; « Les suivantes arrivent chaque matin ». Bouton « Voir mes offres ».
- Plus de récapitulatif de réglages jamais demandés. Si aucune offre n'est encore là : « Tes premières offres arrivent demain matin » à la place de la liste.

### 5.5 Alertes, nouveau compte (AlertesOrdinateurVide, AlertesOrdinateurSite)
- Fond crème. Un seul message en haut, puis carte d'information « Ta recherche » reprise des critères (postes et lieux ne sont jamais redemandés), lien « Modifier ».
- Famille « À créer · 5 sites » : une carte par site avec mot d'état « À créer ». La carte ouvre un panneau de 480 px : « Site n sur 5 » et 5 traits, puis 3 étapes numérotées (Ouvrir le site, coller l'adresse avec champ et bouton copier dans le champ, enregistrer et revenir) ; pied : lien « Plus tard » et bouton plein « J’ai créé l’alerte ».
- LinkedIn : une seule ouverture, avec la case « Aussi en télétravail » au lieu de deux boutons.
- Termes de recherche affichés avec accents et majuscules (« Infirmière · Lausanne »).

### 5.6 Profil, nouveau compte
- La maquette ProfilOrdinateur reste la référence : pas d'onglets Critères / Parcours / Coordonnées, une carte par critère, fond crème, une seule largeur de colonne.
- Indicateur « Profil n sur 5 » : le trait allumé doit correspondre à n.
- « Langues non parlées » devient « Langues » avec les langues parlées et leur niveau.

## 6. Illustrations : qui fait quoi (décision du 9 novembre)

| Rôle | Illustration | Écrans |
|---|---|---|
| Présenter, expliquer une situation | Scènes de la page de présentation (`SceneIllustration`, `public/illustrations/`, docs/67) | Page de présentation, premiers pas, alertes d'un nouveau compte |
| L'outil qui t'aide | Le personnage (docs/141) | Assistant, aides dans Préparer et ORP, chargements, états vides des outils, réussites, page introuvable, maintenance |
| Où l'on est | Logo transformé | En-têtes, petites icônes |

- Un seul type par écran, jamais les deux.
- Cette décision modifie docs/141 §4 : la série `SceneIllustration` n'est plus « à retirer écran par écran ». Elle reste pour la présentation et les premiers pas. Ne pas la supprimer.
- Premiers pas, colonne de droite (360 px de large, 48 px sous le haut de la grille) : étape 1 `offres-profils` ; lecture du CV `lecture-calme` ; CV lu `formations-vide` ; coupure `lecture-calme` en gris (grayscale, opacité 0,6) ; étape 2 `lieux-carte` ; étape 3 `reussite`.
- Alertes d'un nouveau compte : `alertes-carte`, 360 px, centrée sous le titre.
- Images décoratives : `alt=""` et `aria-hidden="true"`. Fichiers dans `illustrations/scenes/` (480 et 800 px).
- À faire : une scène « connexion perdue » dans le même style (l'ancienne `connexion-perdue` a été retirée en PR 2).

## 7. Raccourcis validés (analyse des touchers de Claude Code)

| N° | Décision | Maquettes |
|---|---|---|
| 1 | « Préparer ma candidature » lance l'écriture de la lettre tout de suite ; le CV adapté se prépare en même temps, en arrière-plan. La relecture de la lettre reste obligatoire. | PreparerOrdinateurGeneration, PreparerOrdinateur |
| 2 | Téléphone : plus de case « J'ai relu la lettre » ; un seul bouton « J’ai relu, continuer », comme sur ordinateur. | Preparer, PreparerSombre |
| 3 | Confirmation Gmail automatique : seulement si l'adresse Gmail d'origine est celle du compte et que la personne a lancé l'étape ; afficher « Gmail confirmé », journaliser, mettre à jour la déclaration de confidentialité. Vérification de sécurité à présenter avant le code. | aucune |
| 4 | Postuler : bouton à contour « Tout télécharger » (les deux fichiers séparés). Lettre.pdf et CV.pdf restent téléchargeables un par un. PDF fusionné seulement pour une candidature par e-mail. | PreparerOrdinateurPostuler |
| 5 | Job-Room : après « C'est déclaré », l'extension préremplit la candidature suivante ; l'envoi reste toujours un clic de la personne. | aucune |
| 6 | « Candidature envoyée » : proposer l'adresse de l'entreprise trouvée, à confirmer ; si introuvable, question facultative et non bloquante. | à faire |
| + | Extension en panneau latéral (chrome.sidePanel) pour rester ouverte pendant l'étape Gmail. | à faire |

### 7.1 Préparer pendant l'écriture (PreparerOrdinateurGeneration)
- Bandeau bleu en haut du document (role="status") : « J’écris ta lettre… environ 20 secondes » et, à droite, « Le CV adapté se prépare en même temps ».
- La lettre apparaît au fur et à mesure dans le modèle choisi ; le reste est en lignes grisées.
- Puces de retouche et zone de saisie grisées (« Tu pourras retoucher la lettre dès qu’elle est écrite »).
- Carte « Ta candidature » : Lettre « En cours d’écriture », CV adapté « En préparation », avec indicateur qui tourne (arrêté si prefers-reduced-motion).
- Bouton « J’ai relu, continuer » désactivé tant que la lettre n'est pas écrite.

### 7.2 Lettre écrite (PreparerOrdinateur)
- Carte « Ta candidature » : Relecture (7 sur 7), Versions · 3, CV adapté « Prêt, à relire à l’étape 2 ». Bouton plein « J’ai relu, continuer ».

### 7.3 Échecs (PreparerOrdinateurLettreVide, PreparerOrdinateurCV)
- Ces écrans ne servent plus qu'en cas d'échec : « La lettre n’a pas pu être écrite » / « Le CV adapté n’a pas pu être préparé », explication courte, bouton « Réessayer ».

## 8. Envoyées : détail restructuré, relance et statut par e-mail (validé le 9 novembre)

Remplace la ligne « Envoyées, détail sur ordinateur en deux colonnes » du LISEZMOI (corrections du 8 novembre au soir) : l'ancien détail (Statut, Premier message, Prises de contact, colonne Documents / Contacts à trait) n'existe plus.

### 8.1 Ordinateur (CandidaturesOrdinateurB, onglet `en`)
- Plus de grand cadre blanc autour du détail : des cartes blanches séparées (bordure 1,5 px #CFCBC1, rayon 18) sur le fond crème. Jamais de carte dans une carte (D29).
- **8 px entre toutes les cartes du détail**, à l'horizontale et à la verticale (loi de proximité). 20 px avant « Historique ».
- **Carte d'en-tête** : avatar 56 px, titre, entreprise · ville, menu « … ». Sous le titre, statut en mots colorés (« Sans réponse · 57 jours » en #8A4A16, « ✓ Déclarée à l’ORP » en #17734A). Puis le **Suivi** en 5 étapes : Préparée, Envoyée, Déclarée ORP, Relance, Réponse (date ou état sous chaque libellé).
- **Alignement** : statut et Suivi décalés de 72 px (avatar 56 + écart 16). Titre, entreprise, statut et bord gauche du premier cercle partent du même bord. Libellés alignés à gauche sous leur cercle (pas centrés). Traits entre étapes : de 8 px après un cercle à 8 px avant le suivant ; verts jusqu'à l'étape en cours, gris ensuite. La dernière étape finit sur la marge droite de la carte.
- **Carte de relance** (colonne gauche) : libellé « Relance conseillée » dans la carte, « Ton message est prêt », message proposé en citation, destinataire et canal avec « Changer », bouton plein « Copier et ouvrir LinkedIn » (ou « Ouvrir l’e-mail » selon le canal d'envoi) et lien « Modifier ». Sous la carte : « Quand tu reviens, le statut passe à « Relancé » et la prochaine relance est proposée dans 10 jours. »
- **Colonne droite (280 px)** : carte « Ce que tu as envoyé » (Lettre, CV adapté, L’annonce) et carte « Trouver un contact » (Recrutement, L’équipe du poste, Anciens de 42 Lausanne), lignes de 56 px.
- **Historique** sur le fond crème (simple liste, pas de carte), puis « J’ai contacté quelqu’un ».
- **Séparation liste / détail** : trait vertical 2 px #E5E2D9 sur toute la hauteur. Un trait bleu #2445C2 de 2 px, terminé par un point de 8 px, part du bord droit de la carte sélectionnée et rejoint ce trait. **Il suit la carte sélectionnée** (centre vertical de la carte) et disparaît si aucune carte n'est sélectionnée. Décoratif : `aria-hidden="true"`, la sélection reste portée par `aria-current`.

### 8.2 Statut mis à jour par e-mail (CandidaturesOrdinateurStatut, EnvoyeesStatut)
- Quand un e-mail de réponse est reconnu, la carte de la liste change tout de suite : mot d'état « Refus » (icône croix, #596070), pastille « Réponse reçue hier ».
- Snackbar : « Réponse de [entreprise] : refus. » + « Depuis l’e-mail du 8 nov. », actions « Voir » (ouvre le détail) et « Annuler » (#AEBDFF, remet l'ancien statut).
- La carte reste à sa place tant que la snackbar est visible, puis part dans le groupe des candidatures terminées au prochain rafraîchissement.

### 8.3 Téléphone (EnvoyeeDetail et ses 3 feuilles du bas, validé le 9 novembre)
- Écran poussé depuis la liste Envoyées (la carte Sword Services y mène) : barre du haut « ‹ Envoyées » et « … », sans barre d'onglets. Marges de 20 px, **12 px entre les cartes** (plus d'air que sur ordinateur, où la place ne manque pas).
- **Carte d'en-tête** : titre, entreprise · ville, statut en mots colorés. **Pas d'avatar et pas de graphique de suivi sur téléphone** : les mots de statut disent où on en est, la carte de relance dit quoi faire, l'Historique donne les étapes datées (NN/g, design minimaliste). L'ordinateur garde les 5 cercles.
- **Carte de relance compacte** : « Relance conseillée », « Ton message est prêt », une phrase (« Court et poli, à envoyer par e-mail à Sword Services. »), bouton plein pleine largeur « Voir et envoyer » qui ouvre la feuille Relance.
- **Une carte de 2 lignes de 72 px** avec chevron : « Ce que tu as envoyé » (Lettre, CV adapté et l’annonce) et « Trouver un contact » (3 pistes chez Sword Services). Chaque ligne ouvre sa feuille.
- **Historique** sur le fond crème, puis « J’ai contacté quelqu’un ».
- **Feuille Relance** (EnvoyeeDetailRelance) : destinataire et canal avec « Changer », message entier dans une carte blanche, note « Quand tu reviens… », pied fixe avec bouton plein « Ouvrir l’e-mail » (ou « Copier et ouvrir LinkedIn ») et « Modifier le message ».
- **Feuille Ce que tu as envoyé** (EnvoyeeDetailDocuments) : Lettre, CV adapté (téléchargement), L’annonce (lien externe), lignes de 56 px.
- **Feuille Trouver un contact** (EnvoyeeDetailContacts) : phrase d'aide, puis Recrutement, L’équipe du poste, Anciens de 42 Lausanne (liens externes).
- Les 3 feuilles réutilisent `BottomSheet.vue` (poignée, titre 22 px, croix 48 px, voile, glisser, Échap, retour ; focus rendu au déclencheur ; jamais une feuille ouverte depuis une autre).
- `outils/audit-grille.js` : 0 écart sur les 4 maquettes.

## 9. Téléphone : Préparer simplifié (validé le 9 novembre)

Maquettes : Preparer, PreparerSombre, PreparerMiseEnPage, PreparerMiseEnPageSombre. Capture de l'état « saisie active » : captures/Preparer--saisie-active.png. L'ordinateur ne change pas.

- **En-tête** : plus d'anneau de note (l'offre est déjà choisie à cette étape). Restent l'avatar, le poste, l'entreprise et les étapes Lettre, CV, Postuler.
- **Plus de carte « Mise en page » ni de sélecteur FR / DE / EN** sur l'écran. Sous le titre du document : « Moderne · Français » en gris, et à droite le lien « Changer » (44 px) qui ouvre la feuille.
- **Feuille « Mise en page et langue »** (ancienne feuille Mise en page) : les 4 modèles, « Tient sur une page A4. », puis « Langue de la lettre » en 3 boutons (Français, Deutsch, English), puis la ligne « Retoucher dans Canva » (« Pour changer les couleurs ou la police »). Toujours `BottomSheet.vue`.
- **Aperçu du document : 384 px de haut** (au lieu de 168) pour relire la lettre avant « J’ai relu, continuer ».
- **Puces de retouche** (Plus court, Plus formel, Insister sur…) : cachées par défaut, elles apparaissent au-dessus de la zone de saisie quand elle a le focus ; l'aperçu passe alors à 300 px. Plus de libellé « Retoucher la lettre ».
- **« Retoucher dans Canva »** n'est plus sur l'écran : uniquement dans la feuille.
- `outils/audit-grille.js` : 0 écart sur les 4 maquettes.

## 10. Simplifications transverses (validées le 9 novembre)

### 10.1 Cercles-flèches en gris (téléphone et ordinateur)
- Même composant que le §2.9 (cercle de 36 ou 40 px, flèche de 18 px, à 20 px du bord de la carte), **seule la couleur change** : contour et flèche en #596070 (clair) et #ABA398 (sombre), au lieu du bleu.
- Raison : le bleu reste réservé à l'action principale de l'écran (D30). Le signal « cliquable » garde sa taille et sa forme (NN/g, signifiers). Contraste : 6,3:1 (clair) et 6,6:1 (sombre), WCAG 1.4.11 demande 3:1.
- Ne jamais éclaircir ce gris (il serait lu comme « désactivé »).
- Partout sauf les **notifications** (inchangées).
- Maquettes : Compte, CompteSombre, Orp, OrpSombre, Explorer, ProgresserSombre, AlertesTel, AlertesTelAlerte, AlertesTelConfirmer, AujourdhuiOrdinateurTravailD, AujourdhuiOrdinateurReposD, BilanOrdinateur, BilanOrdinateurFiche, ProfilOrdinateur, AlertesOrdinateur, AlertesOrdinateurVide, AlertesOrdinateurSite, ReglagesOrdinateur, OnboardingOrdinateurEtape2.

### 10.2 Compte (téléphone, clair et sombre)
- Une carte par groupe (profil ; Mon parcours ; Préférences ; Confidentialité et aide ; Se déconnecter), lignes séparées par un trait de 1 px (#EFECE5 clair, #38322B sombre), comme Réglages.
- Plus de trait entre les groupes : le titre du groupe suffit. 12 px au-dessus et au-dessous de chaque groupe.

### 10.3 Suivi ORP (téléphone : Orp, Explorer, clair et sombre ; ordinateur : Bilan)
- Téléphone : à côté de l'anneau 8/10, « Novembre » puis « Encore 2 d’ici le 5 décembre ». Plus de « 2 recherches à faire » ni de « Objectif fixé par ta conseillère… ».
- Ordinateur : « Novembre » à gauche, « 4 sur 13 » à droite, la barre, puis « Encore 9 d’ici le 30 novembre · dans les temps ».

### 10.4 Rendez-vous ORP (téléphone, clair et sombre)
- Une seule action dans la carte : bouton plein « Préparer le rendez-vous », qui ouvre la feuille (elle contient « Imprimer ou télécharger en PDF »). Plus de lien séparé ni de « Voir ma feuille ».
- La pastille « Ta feuille est prête » reste.

## 11. Décisions du 9 novembre au soir
- **Cibles sur ordinateur : 24 px minimum** (WCAG 2.2 AA, 2.5.8). Les boutons principaux restent à 40-48 px ; le téléphone garde 44 px (Apple HIG). `outils/audit-grille.js` en mode ordinateur : seuil 24 px.
- **Bande bleue d'Aujourd'hui : gardée.** Elle marque le point focal du haut de page (l'élément important du jour). Pleine largeur, comme aujourd'hui.
- **Objectif ORP** : saisi par la personne (accord avec sa conseillère), boutons − et +, de 1 à 99 (pas de plafond bas : la valeur est celle convenue avec la conseillère), départ à 10, dans les premiers pas, modifiable dans Profil, redemandé après chaque rendez-vous ORP. Une seule source pour tous les écrans.
- **`ORP_DEADLINE_DAY = 5`** confirmé (art. 26 al. 2 OACI : au plus tard le 5 du mois suivant, ou le premier jour ouvrable qui suit). Le calcul doit reporter au jour ouvrable suivant (samedi, dimanche, jour férié du canton de l’ORP de la personne, Vaud par défaut). Les textes « d’ici le 30 novembre » des maquettes deviennent « d’ici le 5 décembre ».

## 12. Ordinateur sombre : ligne artistique (validée le 9 novembre)
Maquettes : AujourdhuiOrdinateurTravailDSombre, CandidaturesOrdinateurBSombre (onglets tr, en, rv), PreparerOrdinateurSombre, BilanOrdinateurSombre. Les autres écrans ne sont pas dessinés : ils suivent la même table, celle du téléphone sombre.

| Clair | Sombre | Usage |
|---|---|---|
| #F7F5F0 | #171411 | fond de page |
| #FFFFFF | #221E1A | cartes, panneaux |
| #CFCBC1 | #4E473E | bordure des cartes |
| #E5E2D9 | #38322B | traits, séparateurs |
| #1B1F2A | #F3EEE6 | texte principal |
| #596070 | #ABA398 | texte secondaire, cercles-flèches |
| #2445C2 | #7D95FF | bouton plein (texte #171411 dessus) |
| #1A3496 | #AEBDFF | liens |
| #E8ECFB / #F5F7FE | #232B45 | bande bleue d’Aujourd’hui, carte sélectionnée |
| #17734A | #62D497 | vert (Déclarée, Prête) |
| #8A4A16 / #B4631F | #F2B98E | orange (Sans réponse, À creuser) |
| #B4371F | #FF9A85 | rouge (Se déconnecter) |

- **La page A4 de la lettre reste blanche** (document imprimé, comme Word ou Google Docs en sombre), ombre plus marquée.
- Les avatars aux initiales s’inversent (fond clair, lettres foncées).
- Contraste vérifié : texte secondaire #ABA398 sur #221E1A 6,6:1.

## 13. Scène « connexion perdue » (validée le 9 novembre)
- Fichiers : `illustrations/scenes/connexion-perdue-480.webp`, `-800.webp`, `connexion-perdue.svg`. Ordinateur débranché, Wi-Fi barré, prise à côté, plante et tasse.
- Utilisée dans OnboardingOrdinateurCoupure (à la place de `lecture-calme` en gris).
- Version provisoire sans personnage : une version finale avec personnage sera faite dans Recraft ; garder le même nom de fichier.

## 14. Préparer ordinateur : étape CV quand le CV est prêt (validée le 9 novembre au soir)
Maquettes : PreparerOrdinateurCVPret, PreparerOrdinateurCVChangements (panneau). PreparerOrdinateurCV reste l'état d'échec.
- Même structure que l'étape Lettre : CV en page A4 à gauche, carte « Mise en page » à droite (« Même modèle que la lettre · 1 page »), retouche en bas (puces « Plus court », « Mettre Kubernetes en avant », « Tenir sur une page »), bouton « J’ai relu, continuer » vers Postuler.
- **Sélecteur FR / DE / EN** en haut du CV (aria-label « Langue du CV ») : par défaut la langue de la lettre, modifiable à part.
- **Carte « Ce CV »** (remplace « Ta candidature ») : « Adapté pour cette offre · n changements, à vérifier » (ouvre le panneau), « Versions · n », « CV d’origine » (ne change pas, sert de base).
- **Panneau « Adapté pour cette offre »** (SidePanel) : phrase « rien n’est inventé, tout vient de ton CV d’origine », puis un bloc par changement (rubrique, « Avant : … », « Maintenant : … », lien « Annuler ce changement »), et « Ton CV d’origine ne change pas. Ces changements valent pour cette candidature seulement. »

## 15. Les 4 personnages du logo remplacent le personnage à capuche (validé le 9 novembre au soir)
Les 4 morceaux du logo (point bleu, « 1 », sourire, point orange) deviennent les personnages de la plateforme. Le personnage à capuche (illustrations/personnage/) n'est plus utilisé, **sauf dans les notifications** (inchangées).

Deux familles d'images seulement :
- **scènes avec des personnes** (illustrations/scenes/) : premiers pas sur ordinateur et vitrine ;
- **les 4 personnages** (illustrations/troupe/) : états de la plateforme.

| Écran | Scène (illustrations/troupe/) |
|---|---|
| Connexion (téléphone, ordinateur, sombre) | groupe |
| Pas de connexion, hors ligne | hors-ligne (l'équipe rebranche la prise) |
| Maintenance en cours, maintenance annoncée | maintenance |
| Mise à jour (« jobA1 se met à jour ») | mise-a-jour |
| Page introuvable | introuvable |
| Aucune offre | aucune-offre |
| Candidature envoyée | envoyee |
| Objectif ORP atteint | objectif |
| Petits emplacements (premiers pas téléphone, préparation du rendez-vous ORP) | un (le « 1 » seul) |
| Réserve, non placée : écriture de la lettre | ecriture |

- **Mode sombre** : fichiers `-sombre` (bras et jambes en #AEBDFF, ombre au sol en #2C2722, yeux et bouches inchangés). Les originaux haute définition sont dans illustrations/troupe/source/.
- **Ton** : uniquement pour les moments neutres ou positifs. Jamais pour un refus, une échéance ORP dépassée, une perte de données ou une erreur grave : ces écrans gardent une icône sobre (NN/g, ton adapté au contexte).
- **Accessibilité** : images décoratives (`alt=""`, `aria-hidden="true"`), aucune animation si `prefers-reduced-motion`.
- **Chargement** : sous 1 s rien ; de 1 à 10 s un petit indicateur animé (les 4 sautent l'un après l'autre, SVG) ; au-delà, la scène avec un texte qui dit ce qui se passe.
- Les images sont générées : à terme, une version vectorielle fixe garantira des proportions identiques.
