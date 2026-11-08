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
