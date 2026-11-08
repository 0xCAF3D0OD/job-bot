# 143 — La maquette du 8 novembre 2026 : l'ordinateur et les éléments partagés

> Statut : **validé par Kevin le 2026-11-08** (consigne `docs/mobile/PROMPT_CLAUDE_CODE.md`, maquette
> `jobA1_maquette_2026-11-08.zip`, `docs/mobile/LISEZMOI.md`). La maquette fait foi pour le téléphone et pour
> l'ordinateur, à la place de Figma (exception du 2026-11-08 dans `CLAUDE.md`).

## 1. Les sources

Dans l'ordre, de la plus forte à la plus faible :

1. `docs/mobile/PROMPT_CLAUDE_CODE.md`, en particulier les décisions D18 à D27 (§3 ci-dessous) ;
2. `docs/mobile/LISEZMOI.md` ;
3. les captures `docs/mobile/captures/` et `docs/mobile/captures/etats/` (le rendu) ;
4. le HTML de `docs/mobile/maquettes/*.dc.html` (textes, tailles, espacements) ;
5. `docs/mobile/tokens.css` et `frontend/src/style.css` (jetons) ;
6. `docs/regles-ui-ergonomie.md` et les docs existantes.

Les maquettes Get'emAll (`AutoriserGetemall`, `ConfidentialiteGetemall`, `ReglagesConnexions`, `ReglagesRetirer`)
restent dans `docs/mobile/maquettes/` : elles ne sont pas dans le paquet du 8 novembre et restent la référence de
docs/140.

## 2. Les lots

Une PR par lot, dans cet ordre. Chaque PR vise `main` et contient les lots précédents tant qu'ils ne sont pas
fusionnés : on fusionne dans l'ordre 0, 1, 2… et chaque PR ne montre plus que son lot une fois la précédente fusionnée.

| Lot | Contenu |
|---|---|
| 0 | Mise en place, sans interface : maquettes, captures, LISEZMOI, avatars, ce document, exception de `CLAUDE.md`, décisions dans `regles-ui-ergonomie.md`. |
| 1 | Jetons et mécanique commune : 3 jetons, 4 ombres, keyframes `ja-slide-r`, `ja-slide-l`, `ja-pop`, composable `useDismissLayer`. |
| 2 | Composants partagés : `Composer`, `SuggestionChips`, `CalendarDate`, `DateTimeField` et `DateTimePanel`, `ProfileImage` et `AvatarPicker`. |
| 3 | En-tête et panneaux de l'ordinateur : recherche en bulle, cloche et compte en panneaux non modaux de 420 px, Assistant en panneau de 480 px. |
| 4 | Candidatures sur ordinateur (`CandidaturesOrdinateurB`) : filtres à la place de la liste, menu « … », ajout d'une offre, Envoyées, Rendez-vous. |
| 5 | Aujourd'hui sur ordinateur : bande, H1 d'action, carte Mois ORP à cheval, tâches sur 880 px. |
| 6 | Bilan, Préparer, Profil sur ordinateur. |
| 7 | Notifications, Alertes, Réglages sur ordinateur. |
| 8 | Pages d'état, Connexion, Premiers pas sur ordinateur. |
| 9 | Téléphone : éléments partagés (Assistant, Préparer, Offre provisoire, Ajouter une offre, Envoyées, Rendez-vous, Compte, Alertes, Réglages, Bilan, Extension). |
| 10 | Vérification finale et « Écarts connus ». |

## 3. Les décisions D18 à D27

| N° | Décision | Remplace |
|---|---|---|
| D18 | **Seuil unique 820 px (D8 reste).** Les mentions « < 600 px » et « >= 1024 px » de l'ancien LISEZMOI sont fausses. Téléphone : largeur <= 820 px. Ordinateur : > 820 px. Entre 821 et 1327 px, les conteneurs de 1280 et 880 px prennent `max-width` avec 24 px de marge de chaque côté. | — |
| D19 | **Rayons D7 (8, 18, 34, 999) restent.** Traduction des rayons de la maquette dans le §4 de la consigne. | — |
| D20 | **Couleurs** : traduction obligatoire par le tableau du §3 de la consigne, avec 3 jetons nouveaux (`--line-strong`, `--field-border`, `--text-disabled`) et 4 ombres nouvelles (`--shadow-panel`, `--shadow-menu`, `--shadow-band-card`, `--shadow-composer`). | — |
| D21 | **Barre du bas du téléphone** : elle s'appelle « Bilan », pas « Progresser » (D2 reste), et « Accueil » (D1 reste). Les maquettes affichent encore « Progresser » : ignorer ce mot. | — |
| D22 | **Carte = cliquable.** Une carte (fond `--surface` + bordure) est toujours entièrement cliquable. Une information seule n'a pas de cadre : lignes séparées par `--line-soft`. Dans une carte cliquable, jamais de bouton ni de pastille d'action : un libellé coloré (couleur du ton, 15 px, 700) suivi de « › ». | §4 (cartes), en partie |
| D23 | **Icônes sans fond.** Aucune pastille ou rond coloré derrière une icône décorative, sur téléphone et sur ordinateur. Exception : l'icône Assistant de la barre du bas du téléphone garde son cercle. | — |
| D24 | **Panneaux latéraux non modaux** (cloche, compte, Assistant) sur ordinateur : 420 px (Assistant 480 px), sans voile. Un clic à l'extérieur ferme tout. Les filtres de Candidatures **remplacent la colonne liste** au lieu de s'ouvrir en popover. Le panneau du compte porte Mon compte, Affichage, Aide et Se déconnecter. | docs/32 §2.2 (voile), maquette CandidaturesOrdinateur état `f`, docs/89 (contenu du menu du compte) |
| D25 | **Zone de saisie unique (Composer)** pour tout message libre envoyé tel quel. Les champs de formulaire restent des champs de formulaire. | — |
| D26 | **Date et heure** : déclencheurs en pilule, sélecteur qui prend la place du formulaire (plein écran sur téléphone), icône calendrier qui contient la date (CalendarDate) au lieu des carrés colorés. Remplace les `<input type="date">` et `<input type="time">` natifs (`OrpMeetingForm.vue`, `OrpOutcomeSheet.vue`). | docs/22 en partie |
| D27 | **Personnage sur ordinateur** : 240 px de haut sur les pages d'état, 360 px aux premiers pas. La note « 290 px sur ordinateur » de docs/141 §4 est remplacée. Liste fermée de docs/141 §3 inchangée. | docs/141 §4 |

Autres décisions qui restent valables : D12 (chiffre au centre de l'anneau), D13 (mouvement), D14 (une hauteur par
ligne de liste), D15, D16, D17.

## 4. Écarts connus

Ce qui ne suit pas la maquette, avec la raison. Rempli au fil des lots, complété au lot 10.

| Écran ou élément | Écart | Raison | Lot |
|---|---|---|---|
| En-tête de l'ordinateur | Le menu principal reste centré ; la maquette le place à gauche, après le logo. | §7 de la consigne : ne pas changer le menu principal. Question posée à Kevin dans la PR du lot 3. | 3 |
| Assistant (ordinateur) | Pas de « + » ni de micro dans la zone de saisie, donc pas de pièce jointe (CV) dans la conversation. | Aucun fichier ne part à l'IA sans règle (I-1, E-5) et la dictée est masquée (O-4) ; le serveur de l'Assistant ne reçoit pas de fichier. | 3 |
| Assistant (ordinateur) | La bulle de l'Assistant prend `--panel` au lieu de #F1EFE9. | #F1EFE9 n'est pas un jeton de tokens.css. | 3 |
| Assistant (ordinateur) | Le panneau garde son propre gabarit (classes du SidePanel non modal) au lieu du composant SidePanel. | Le panneau de l'Assistant est aussi la page Assistant du téléphone ; le découper aurait recréé le composant. | 3 |
| Panneau du compte | Les icônes « Réglages » et la roue de la maquette : on garde l'icône Réglages de jobA1 (curseurs). | Iconographie docs/101 : pas de nouvelle icône pour un sens qui en a déjà une. | 3 |
| Titres des panneaux | 20 px dans la maquette, `--font-section` (22 px) ; intertitres 13 px, `--label-caps`. | Échelle de jetons (docs/135). | 3 |
| Ajouter une offre | Pas de menu « + » (Importer le PDF de l'annonce, Importer une capture d'écran). | Aucun fichier ne part à l'IA sans règle (I-1, E-5) ; le serveur ne lit qu'un lien ou un texte. Question posée à Kevin dans la PR du lot 4. | 4 |
| Ajouter une offre | Les exemples propres au métier sous le champ (« Ex. Menuisier à Sion… ») disparaissent. | La zone de saisie commune (Composer) n'a qu'un placeholder, celui de la maquette. | 4 |
| Menu « ⋯ » de la fiche (ordinateur) | Après les entrées dessinées, un trait puis les autres actions de la fiche (J'ai postulé, expirée, Assistant). | Ces actions n'ont pas d'autre place sur ordinateur ; les retirer en supprimerait l'usage. | 4 |
| Envoyées (ordinateur) | Le détail à droite reprend le contenu du panneau de candidature, pas le tableau « Suivi » ni « Ce que dit jobA1 ». | Ces deux blocs n'ont pas de données côté serveur ; question posée à Kevin dans la PR du lot 4. | 4 |
| Rendez-vous (ordinateur) | « À noter » ouvre toujours le dialogue « Ce qui a été convenu » ; la maquette le montre dans le détail, à droite. | Le formulaire est celui de la feuille (OrpOutcomeSheet) ; le déplacer dans le détail est prévu au lot 10 si Kevin le confirme. | 4 |
| Champs date et heure | Il reste des champs natifs ailleurs (entretien, candidature, contacts, entraînement, réglages). | Hors des écrans du lot 4 ; traités au lot 10. | 4 |
| Aujourd'hui (ordinateur) | La phrase sous le titre dit « N offres sont à trier » au lieu de « N nouvelles offres sont arrivées cette nuit ». | Le serveur ne donne pas l'heure d'arrivée des offres ; la phrase dit ce qu'on sait. | 5 |
| Aujourd'hui (ordinateur) | « À retenir » (l'écart du Bilan) et la bande « Tri du jour » disparaissent de l'ordinateur ; le tri devient une tâche « Trier N offres ». | Absents de la maquette. « À retenir » reste lisible dans le Bilan. Question posée à Kevin dans la PR du lot 5. | 5 |
| Aujourd'hui (ordinateur) | Titres sans maquette : « En pause. », « Tout est à jour. » (objectif atteint ou sans objectif), « Commence par les premiers pas. » (sans accent manuscrit). | La maquette ne dessine que le jour de travail et le jour de repos ; mêmes règles (une fin manuscrite au plus). | 5 |
| Aujourd'hui (ordinateur) | Le titre de la page n'est plus « Aujourd'hui » : c'est l'action du jour (exception ajoutée à titles.test.ts). | LISEZMOI : « H1 = action du jour ». | 5 |
| Police manuscrite | Le sous-ensemble de Caveat Brush gagne « à », « y » et « j » (3,8 → 4,6 Ko). | Les fins du titre d'Aujourd'hui ; scripts/regles.py les lit désormais. | 5 |
| Bilan › Résultats et Formations (ordinateur) | Seule la bande change ; le contenu reste celui d'avant (pas encore « Le mois en bref », « Ce qui bloque » ni la bande de trois chiffres à cheval). | « Ce qui bloque » (réponses par site, jamais relancées) demande des données que l'API des résultats ne donne pas sous cette forme. Question posée à Kevin dans la PR du lot 6. | 6 |
| Préparer (ordinateur) | Les réglages à gauche (modèle, langue, mis en avant, longueur), la lettre au centre et « J'ai relu la lettre » en bas à droite ne sont pas repris ; seules les retouches et la zone de saisie le sont. | Refaire la mise en page de Préparer dépasse le lot ; les blocs actuels gardent leurs tests. | 6 |
| Préparer | Pas de menu « + » (Joindre l'annonce complète, Joindre un document) ni de micro. | Aucun fichier ne part à l'IA sans règle (I-1, E-5) ; l'annonce part déjà avec la demande ; la dictée est masquée (O-4). | 6 |
| Profil (ordinateur) | L'en-tête (image, nom, « Changer d'image », « Modifier ») est repris ; les blocs Mon CV, Compétences trouvées et Ce que je cherche restent dans leurs onglets (Critères, Parcours, Coordonnées). | Le sous-titre « Junior DevOps » n'existe pas dans les coordonnées : seule la ville s'affiche. Question posée à Kevin dans la PR du lot 6. | 6 |
| Bilan › ORP (ordinateur) | « Ajouter une recherche » ouvre le formulaire dans le Suivi ORP du mois (/bilan/orp?ajouter=1). | Le formulaire d'ajout vit dans le Suivi ORP ; pas de second formulaire. | 6 |
| Mes alertes e-mail (ordinateur) | Une ligne par recherche et par site (« DevOps · jobup », « DevOps · LinkedIn »…), pas une ligne par recherche ; « … » agit sur toute la recherche (Modifier la recherche, Supprimer la recherche). | Une recherche jobA1 se crée sur chaque site ; la maquette montre un site par recherche. Question posée à Kevin dans la PR du lot 7. | 7 |
| Mes alertes e-mail (ordinateur) | La phrase du bas « jobA1 lit seulement les e-mails d'alerte transférés par ton filtre Gmail. Les autres sont supprimés à la réception. » n'est pas reprise. | Le Transfert Gmail (D) attend encore la validation de Kevin ; la phrase promettrait un traitement des e-mails pas encore en place (R-1, docs/regles-securite-donnees.md). | 7 |
| Mes alertes e-mail (ordinateur) | Sous la liste restent les codes des sites, les alertes reçues et les premières offres. | Absents de la maquette, mais le bandeau « code de vérification » y renvoie ; les retirer couperait cet usage. | 7 |
| Réglages (ordinateur) | Les sections gardent leur contenu actuel : pas de « Rappels ORP », « Relances conseillées », « E-mail en plus des notifications » (résumé du lundi), Langue (Deutsch, English), Taille du texte, ni Canva dans Connexions. | Ces réglages n'existent pas encore ; les ajouter serait les inventer. Question posée à Kevin dans la PR du lot 7. | 7 |
| Réglages (ordinateur) | Les boutons des lignes gardent leur forme actuelle (coins de 8 px) au lieu de la pilule. | Le style commun des boutons secondaires ; le changer touche toutes les pages (lot 10). | 7 |
| Mes alertes e-mail | Titre possessif accepté (exception dans titles.test.ts). | Repris tel quel de la maquette du 8 novembre. | 7 |
