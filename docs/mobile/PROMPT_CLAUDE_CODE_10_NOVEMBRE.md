# Prompt Claude Code, 10 novembre 2026

À installer par-dessus le paquet du 9 novembre. Ce fichier prime sur les précédents pour les points ci-dessous.
Maquettes à jour : `OffreProvisoire`, `CandidaturesOrdinateurB`, `CandidaturesOrdinateurBSombre`, `CandidaturesOrdinateurAjouter`, `CandidaturesOrdinateurSpontanee`, `CandidaturesOrdinateurStatut`.
Ordre des PR : 13, 14, 15, 16. Pour chaque PR : captures avant/après à 360 et 390 px (téléphone) et 1440 px (ordinateur), en clair et en sombre.

## PR 13. Annonce complète lue automatiquement (téléphone et ordinateur)

Décision : l'utilisateur ne doit pas aller chercher une information que jobA1 peut récupérer seul (ISO 9241-110, adéquation à la tâche ; loi de Tesler). On ne lui demande le texte que si la lecture automatique échoue.

- Quand une offre arrive par une alerte avec un lien, récupérer le texte complet en arrière-plan (tâche asynchrone) : récupération du HTML, extraction du contenu principal, respect de robots.txt et des conditions des sites, délai maximal 15 s, 1 seul nouvel essai.
- États de la carte de la note (voir `OffreProvisoire`, variable `st`) :
  - `reading` (par défaut) : note provisoire visible avec le badge « Provisoire », sous-titre « Calculée sur l’extrait de l’alerte, en attendant l’annonce complète. », puis une ligne « jobA1 lit l’annonce complète… » avec un petit indicateur circulaire (`role="status"`, `aria-live="polite"`). Aucun bouton.
  - `done` : note recalculée, badge « Provisoire » retiré, message « Note refaite sur l’annonce complète. », texte complet dans « Le poste ».
  - `refused` (blocage, connexion obligatoire comme LinkedIn, 404, annonce expirée) : bloc « jobA1 n’a pas pu lire l’annonce », texte « Ce site bloque la lecture automatique. Colle le texte : la note sera refaite tout de suite. », un bouton tonal « Coller le texte » (ouvre la feuille de collage existante) et un lien « Ouvrir l’annonce ».
- Supprimer le bouton « Lire l’annonce » et le bandeau orange « Il manque l’annonce complète ».
- Téléphone : le bloc reste DANS la carte (séparé par un filet), jamais en pleine largeur qui dépasse le contour. Pas d’espace vide sous le bloc.
- Journaliser la raison de l’échec par domaine, pour voir quels sites posent problème.

## PR 14. Ligne profil de l’écran Compte (téléphone, clair et sombre)

Modèle : `CompteImage`. Cause probable du bug : le badge crayon est positionné par rapport à un conteneur plus large que l’avatar.
- Conteneur `position: relative` de la taille exacte de l’avatar : `display: inline-flex; width: 52px; height: 52px; flex: none;` sans padding.
- Avatar 52 × 52 rond : image choisie dans Profil si elle existe, sinon les initiales (clair #E8ECFB / #2445C2, sombre #232B45 / #AEBDFF).
- Badge 22 × 22 rond, `right: -3px; bottom: -3px`, fond = fond de la carte, bordure 1 px (#E5E2D9 clair, #3A352E sombre), crayon 12 px, `aria-hidden="true"` : toute la ligne est le lien.
- Ne pas reprendre les tailles de ProfilOrdinateur (72 / 28 px), réservées à l’ordinateur.
- Ligne : padding 14 px, gap 14 px. Sous-titre « CV, compétences, postes recherchés » sur 2 lignes maximum, sans troncature.

## PR 15. Détail d’une offre (téléphone)

- Lien du bas de la carte de la note : texte aligné à gauche (même retrait que le contenu de la carte), chevron à droite, libellé « Le détail de la note ». Ne pas reprendre le retrait de 98,5 px de l’ordinateur.

## PR 16. Onglet Rendez-vous (téléphone, clair et sombre)

- Si un rendez-vous passé attend « Noter ce qui a été convenu », la section « À noter » s’affiche EN PREMIER, avant le formulaire.
- Titre de l’état vide : « Aucun rendez-vous à venir ».
- Contenu : `padding-bottom` = hauteur de la barre du bas + dépassement du bouton central + 16 px. Rien ne passe dessous (WCAG 2.4.11).
- Champs Date et Heure sur une même ligne (Date `flex: 1.4`, Heure `flex: 1`), comme dans la feuille « Ce qui a été convenu ».
- Texte d’exemple du lieu : « Ex. : ORP Renens, rue de Lausanne 35 ».
- Ne pas changer la casse du lieu saisi (garder « EPFL »).
- Carte à noter : titre « Rendez-vous ORP », sous-titre « Vendredi 30 octobre, 11 h · EPFL ».
- Supprimer le titre « Derniers rendez-vous ORP » : la ligne « Carnet ORP » suffit.
- Personnage de l’état vide : en attente, la nouvelle scène sera livrée dans un prochain paquet. Ne pas utiliser le personnage à capuche (réservé aux notifications).

## Typographie (partout)
- Espace fine insécable (U+202F) avant « : ; ? ! » dans tous les textes en français.
- Apostrophe typographique ’ partout (pas d’apostrophe droite).

---

# Suite du 10 novembre (après-midi) : PR 17 à 20

Nouvelles maquettes : `OnboardingOrdinateurProfil`, `OnboardingOrdinateurProfilSombre`, `OnboardingProfil`, `OnboardingProfilSombre`.
Maquettes mises à jour : `Assistant`, `AssistantOrdinateur`, `OffreCompatibilite`, `OffreCompatibiliteSombre`.

## PR 17. Parcours sans CV lu : plus aucune impasse

Modèle : `OnboardingOrdinateurProfil` (ordinateur) et `OnboardingProfil` (téléphone), clair et sombre.

1. Accueil, échec ou absence de CV : afficher l’étape « Complétons ton profil » (reste l’étape 1 sur 3).
   - Fichier en erreur avec la raison en clair (« C’est une image scannée : le texte n’est pas lisible. ») et le lien « Essayer un autre fichier ».
   - Expériences : poste, employeur, début, fin (désactivée et grisée si « J’y travaille encore » est coché), tâches principales (textarea). Lien « Ajouter une expérience ». Exemples adaptés aux postes recherchés.
   - Langues : français, allemand, italien, anglais, chacune avec Non renseigné (défaut) / Notions / Courant / Langue maternelle. Lien « Ajouter une langue ».
   - Coordonnées : prénom et nom (seul champ obligatoire, indiqué « (obligatoire) »), adresse, NPA + localité, téléphone, e-mail pré-rempli avec le compte.
   - Actions : « Retour », « Plus tard » (lien), « Continuer » (principal). Téléphone : barre du bas fixe avec « Continuer » pleine largeur et « Plus tard » dessous.
   - Ordinateur : encadré « À quoi ça sert » à droite.
   - Quand le CV EST lu : ajouter quand même l’étape Langues, pré-remplie.
2. Critères : « Repris de ton CV » / « Trouvé dans ton CV » uniquement pour les valeurs réellement extraites.
3. Langues : « Non renseigné » n’écarte jamais une offre et ne baisse pas la note ; afficher « Langue à vérifier » dans le détail. Remplacer « Langues non parlées » par « Langues » avec les niveaux.
4. Offre « Pas encore notée » faute de profil : « Il manque ton profil pour noter cette offre » + bouton « Compléter mon profil » (ouvre le même formulaire, puis revient et note l’offre).
5. Préparer ma candidature : remplacer « Aucun bloc de profil actif » + « Réessayer » par « Ajoute au moins une expérience pour écrire une lettre sans invention. » + bouton « Ajouter une expérience » (même formulaire en panneau) ; relancer la préparation au retour. Nom ou adresse manquants : les demander avant la génération.
6. Profil › Expériences : supprimer la mention d’un bouton absent, remplacer « bloc » par « expérience » ou « compétence » dans tous les textes visibles.
Test obligatoire : parcours complet avec un compte sans CV lu (employée de commerce) jusqu’à une lettre, sans détour. Captures à chaque étape.

## PR 18. « Comment la note est calculée »

Modèle : `OffreCompatibilite` et `OffreCompatibiliteSombre`, état `calc` (capture `captures/etats/OffreCompatibilite--calcul-ouvert.png`).
- Bouton accordéon (`aria-expanded`, `aria-controls`), chevron bas fermé / haut ouvert.
- Contenu : une phrase d’intro, puis 5 critères avec points et barre : Compétences demandées /40, Expérience /20, Lieu et trajet /15, Langues /15, Taux et contrat /10. Total = note sur 100.
- Pour chaque critère : une phrase claire en français (ce qui est trouvé, ce qui manque). Pas d’anglais ni de jargon (« collent », « DB reliability »).
- Barre : vert si plein, bleu si partiel, orange si point à vérifier. Le chiffre est toujours écrit (WCAG 1.4.1), barre en `role="img"` avec `aria-label`.
- Encadré « Pour faire monter la note » avec une action concrète (ex. « Ajouter une compétence »).
- Pied : date et source du calcul (annonce complète ou extrait) + « jobA1 ne lit pas d’informations personnelles comme l’âge ou la nationalité. »
- Les points viennent du vrai calcul : si le moteur ne les expose pas, les exposer (API) plutôt qu’inventer.

## PR 19. Zone de saisie de l’Assistant (téléphone et ordinateur)

Modèle : `Assistant` et `AssistantOrdinateur` (même principe que la zone de saisie de Claude).
- Marges 16 px de chaque côté. Boîte : radius 24 px, padding 14 px 16 px 9 px, bordure 1 px #E5E2D9, ombre légère.
- Ligne 1 : textarea (pas input), 16 px / 24 px, s’agrandit de 1 à 6 lignes puis défile.
- Ligne 2 dans la boîte : + à gauche, micro et Envoyer à droite, zones tactiles 44 px. Envoyer = rond 36 px, gris (#E5E2D9, icône #8A8F9C, `aria-disabled`) si vide, bleu #2445C2 s’il y a du texte. Entrée envoie, Maj+Entrée = nouvelle ligne.
- Fichier joint (ordinateur) : puce alignée sur le texte (padding 10 px 16 px 0).
- Focus : bordure 1,5 px #2445C2 à l’intérieur de la boîte, rien ne dépasse (pas d’outline extérieur).
- Avertissement : 10 px sous la boîte, 12 px / 16 px, #596070.
- Discussions récentes : titre `flex: 1; min-width: 0` avec ellipsis, date `flex: none` jamais coupée. Rien ne dépasse la colonne.
Vérifier à 360, 390 et 1440 px, vide / 1 ligne / 8 lignes, clair et sombre.

## PR 20. Compte, Profil, Critères, Administration

1. Ordinateur : pas de page Compte façon téléphone. L’avatar ouvre le menu « Mon compte » (voir `ProfilOrdinateur`).
2. Profil ordinateur ET téléphone : page unique, sans onglets (décision B), ordre de `ProfilOrdinateur` : en-tête, Mon CV, Compétences trouvées, Ce que je cherche, puis groupe « Mon parcours » en lignes (Formations, Expériences, Documents et certificats, Coordonnées, avec un résumé chacune). Rien caché derrière « Modifier ». Supprimer « Changer d’image » (le badge crayon le fait). Lister où chaque ancienne fonction se retrouve.
3. Partout : pas de tuile grise dans une carte blanche (D28). Lignes d’un groupe séparées par un filet 1 px #E5E2D9, comme `Compte`.
4. Profil téléphone, documents : nom de fichier tronqué sur 1 ligne, bouton sous le nom (plus de chevauchement). Filtres sur une seule ligne qui défile.
5. Critères : lignes au format de `ProfilOrdinateur` (libellé gris, valeur en gras, cercle flèche gris #596070). « Écartées surtout pour » : une ligne par raison (« 95 offres pour le lieu »).
6. Administration : « … » sur la ligne du nom, à droite (48 px). Champ « Plafond IA par mois » avec suffixe « CHF » dans le champ. Texte : « IA 0,00 CHF utilisés ce mois » (sans répéter le plafond).
7. Apostrophes ’ et espaces fines insécables avant : ; ? ! partout.
