# Prompt pour Claude Code : maquette jobA1 du 8 novembre 2026

Dépôt : `0xCAF3D0OD/job-bot` (app Vue 3 + Vite, `frontend/`).
Base vérifiée : `main` au commit `271fae29` (8 novembre 2026, après les PR #559, #561 et #562).
Ce document est la consigne complète. Lis-le en entier avant d'écrire une ligne de code.

---

## 0. Règles de travail (non négociables)

1. **Ne rien improviser.** Chaque élément d'interface que tu codes doit se trouver dans une maquette de ce zip ou dans ce document. Une valeur, un texte, un état ou un comportement introuvable : tu t'arrêtes, tu l'écris dans la PR sous « Questions pour Kevin », et tu continues sur le reste. Tu ne choisis jamais à sa place.
2. **Ordre des sources**, de la plus forte à la plus faible :
   1. ce document (et en particulier les résolutions de conflits du §2) ;
   2. `LISEZMOI.md` du zip ;
   3. les captures `captures/` et `captures/etats/` (le rendu) ;
   4. le HTML de `maquettes/*.dc.html` (valeurs exactes : textes, tailles, espacements) ;
   5. `docs/mobile/tokens.css` et `frontend/src/style.css` (jetons) ;
   6. `docs/regles-ui-ergonomie.md` et les docs existantes.
3. **Les maquettes ne s'ouvrent pas seules** : `support.js`, le moteur du canevas, n'est pas fourni. Le rendu se lit dans les PNG. Les états d'une maquette se lisent dans son script (`renderVals`, objet `s` = état) et dans `captures/etats/<Fichier>--<état>.png`.
4. **Aucune valeur en dur.** Toute couleur, tout rayon, toute ombre et toute durée passent par une variable de `style.css`. Le §3 traduit chaque couleur des maquettes en jeton. Le §4 traduit les rayons.
5. **Une PR par lot**, dans l'ordre du §5. Chaque PR contient :
   - la liste des points du lot cochés un par un ;
   - « Règles vérifiées : … » (sections 3, 4, 5 et 7 de `docs/regles-ui-ergonomie.md`, comme d'habitude) ;
   - des captures 390 px et 1440 px, en clair et en sombre, de chaque écran touché, à côté de la capture de la maquette ;
   - une entrée dans `changelog.d/` selon `changelog.d/README.md`.
6. **Données des utilisateurs** : `docs/regles-securite-donnees.md` s'applique à l'image de profil, aux pièces jointes de l'Assistant et à la dictée (§6). La PR cite les règles (R-1).
7. **Tests** : garde verts `scales.test.ts`, `contrast.test.ts`, `tokens.test.ts`, `personnage.test.ts`, `iconography.test.ts` et `overflow.test.ts`. Ajoute un test par composant nouveau (§5, lot 2).
8. Tu ne modifies pas les maquettes. Un défaut de maquette se signale dans la PR.

---

## 1. Mise en place (lot 0, sans interface)

1. Remplace le contenu de `docs/mobile/maquettes/` par `maquettes/` du zip (67 écrans + `canvas.json`).
   - **Garde** les fichiers Get'emAll déjà présents dans le dépôt : `AutoriserGetemall`, `ConfidentialiteGetemall`, `ReglagesConnexions`, `ReglagesRetirer`. Ils ne sont pas dans le zip et restent la référence de docs/140.
2. Remplace `docs/mobile/captures/` par `captures/` du zip, sous-dossier `etats/` compris.
3. Copie `LISEZMOI.md` dans `docs/mobile/LISEZMOI.md`, et ce fichier dans `docs/mobile/PROMPT_CLAUDE_CODE.md`.
4. Copie `illustrations/icones/calendrier-date.html` dans `docs/mobile/calendrier-date.html`.
5. Copie `illustrations/avatars/*` dans `frontend/public/avatars/` sans rien renommer (`avatar-1-128.webp` … `avatar-8-256.png`).
6. Ne recopie pas `illustrations/personnage/`. Les poses sont déjà dans `frontend/public/personnage/`. Vérifie seulement que les 12 poses y sont, en `-400` et `-800`, et liste celles qui manqueraient.
7. Dans `CLAUDE.md`, complète l'exception du 2026-11-02 par cette ligne :
   « Exception (décidée le 2026-11-08) : la maquette du 8 novembre (docs/mobile/LISEZMOI.md, docs/143) fait foi pour le téléphone **et pour l'ordinateur**, à la place de Figma. Mêmes limites : un écran absent des index du LISEZMOI suit la règle "s'arrêter et le signaler". »
8. Crée `docs/143-maquette-8-novembre.md` :
   - en-tête « Statut : validé par Kevin le 2026-11-08 » ;
   - le plan des lots du §5 ;
   - les décisions D18 à D27 du §2 ;
   - un tableau « Écarts connus » vide au départ.
9. Ajoute à la fin de `docs/regles-ui-ergonomie.md` une section « Décisions du 8 novembre 2026 : la maquette ordinateur et les éléments partagés (Kevin, docs/143) », qui reprend le tableau D18 à D27 du §2 avec sa colonne « Remplace ».
10. **Supprime du dépôt** les maquettes abandonnées, si elles y sont encore : `CandidaturesOrdinateur`, `RendezVousOrdinateur`, `AujourdhuiOrdinateur`, `AujourdhuiOrdinateurTravail`, `AujourdhuiOrdinateurTravailB`, `AujourdhuiOrdinateurTravailC`, `Onboarding1`, `Onboarding2`, `Onboarding3`, `OnboardingB`, `Cercles`, `Main`, `Personnage`.

---

## 2. Conflits déjà tranchés (à appliquer tels quels)

La maquette se lit corrigée par ces décisions. Elles sont validées par Kevin le 2026-11-08.

| N° | Décision | Remplace |
|---|---|---|
| D18 | **Seuil unique 820 px (D8 reste).** Les mentions « < 600 px » et « >= 1024 px » de l'ancien LISEZMOI sont fausses. Téléphone : largeur <= 820 px. Ordinateur : > 820 px. Entre 821 et 1327 px, les conteneurs de 1280 et 880 px prennent `max-width` avec 24 px de marge de chaque côté. | — |
| D19 | **Rayons D7 (8, 18, 34, 999) restent.** Traduction des rayons de la maquette dans le §4. | — |
| D20 | **Couleurs** : traduction obligatoire par le tableau du §3, avec 3 jetons nouveaux et 4 ombres nouvelles. | — |
| D21 | **Barre du bas du téléphone** : elle s'appelle « Bilan », pas « Progresser » (D2 reste), et « Accueil » (D1 reste). Les maquettes affichent encore « Progresser » : ignorer ce mot. | — |
| D22 | **Carte = cliquable.** Une carte (fond `--surface` + bordure) est toujours entièrement cliquable. Une information seule n'a pas de cadre : lignes séparées par `--line-soft`. Dans une carte cliquable, jamais de bouton ni de pastille d'action : un libellé coloré (couleur du ton, 15 px, 700) suivi de « › ». | §4 (cartes), en partie |
| D23 | **Icônes sans fond.** Aucune pastille ou rond coloré derrière une icône décorative, sur téléphone et sur ordinateur. Exception : l'icône Assistant de la barre du bas du téléphone garde son cercle. | — |
| D24 | **Panneaux latéraux non modaux** (cloche, compte, Assistant) sur ordinateur : 420 px (Assistant 480 px), sans voile. Un clic à l'extérieur ferme tout. Les filtres de Candidatures **remplacent la colonne liste** au lieu de s'ouvrir en popover. | docs/32 §2.2 (voile), maquette CandidaturesOrdinateur état `f` |
| D25 | **Zone de saisie unique (Composer)** pour tout message libre envoyé tel quel. Les champs de formulaire restent des champs de formulaire. | — |
| D26 | **Date et heure** : déclencheurs en pilule, sélecteur qui prend la place du formulaire (plein écran sur téléphone), icône calendrier qui contient la date (CalendarDate) au lieu des carrés colorés. Remplace les `<input type="date">` et `<input type="time">` natifs (`OrpMeetingForm.vue` l. ~90, `OrpOutcomeSheet.vue` l. ~158). | docs/22 en partie |
| D27 | **Personnage sur ordinateur** : 240 px de haut sur les pages d'état, 360 px aux premiers pas. La note « 290 px sur ordinateur » de docs/141 §4 est remplacée. Liste fermée de docs/141 §3 inchangée. | docs/141 §4 |

Autres décisions qui restent valables : D12 (chiffre au centre de l'anneau), D13 (mouvement), D14 (une hauteur par ligne de liste), D15, D16, D17.

---

## 3. Couleurs : de la maquette au jeton

Toute couleur hexadécimale d'une maquette se remplace par le jeton de cette table. Une couleur absente de la table, hors logos de marque tiers et intérieur des illustrations : tu t'arrêtes et tu la signales.

| Hex maquette (clair) | Hex maquette (sombre) | Jeton à utiliser | Usage |
|---|---|---|---|
| #F7F5F0 | #171411 | `--bg` | fond |
| #FFFFFF | #221E1A | `--surface` | cartes, panneaux |
| #ECE9E1, #F1EFE9, #F2F1EC | #2C2722, #3A342D | `--surface-muted` pour un fond de puce ou de segment, `--line-soft` pour un séparateur | |
| #E5E2D9 | #38322B | `--line` | bordures de carte et de panneau |
| #EFECE5, #ECE9E1 (traits) | #2C2722 | `--line-soft` | traits entre lignes |
| #D8D4CA, #CFCBC1 | #4E473E | **nouveau `--line-strong`** (clair #D8D4CA, sombre #4E473E) | bordure de la bulle de recherche, des champs au repos |
| #8C8478 | #8C8478 | **nouveau `--field-border`** (clair et sombre #8C8478) | bordure 1,5 px des pilules date et heure ; ton « passé » de CalendarDate |
| #B8B3A8 | — | **nouveau `--text-disabled`** (clair #B8B3A8, sombre #5E574F) | jours passés désactivés du calendrier, texte désactivé (exempté de contraste, WCAG 1.4.3) |
| #1B1F2A | #F3EEE6 | `--text` | |
| #3D4250 | #D6CFC4, #D9D2C7, #C8C0B4 | `--text-tertiary` | texte et icônes gris foncé |
| #596070 | #ABA398 | `--text-secondary` | |
| #6B6157 | — | `--score-dig` | libellé « Provisoire » |
| #2445C2 | #7D95FF (graphique) | `--primary` (fond de bouton) / `--primary-graphic` (icône, trait, anneau) | |
| #1D3B91, #1A3496 | #AEBDFF | `--primary-text` | liens, survol d'un bouton plein |
| #E8ECFB, #F5F7FE | #232B45 | `--primary-soft` | bande bleu pâle, sélection, encadré « Valider » |
| #D5DCF5 | — | `--water` | bordure de la carte Mois ORP sur la bande |
| #8A4A16, #8F4710 | #F2B98E | `--peach-text` (déjà dans `style.css`) | ton « en retard » |
| #B4631F | #F2B98E | `--warning` | ton « orp » de CalendarDate (ORP ou à noter) |
| #FDEDE3, #FBF4EE | #3A281E | `--peach-soft` | bandeau pêche (alerte Indeed, note provisoire) |
| #F3D3BF | — | `--peach` | bordure du bandeau pêche |
| #17734A | #62D497, #7FD3A6 | `--success` | |
| #B4371F | #FF8A73 | `--danger` | « Se déconnecter », destructif seulement |
| #C9C5BA / #A9A397 | — | `--scrollbar-thumb` / `--scrollbar-thumb-hover` (déjà dans `style.css`) | |
| #D9DCE6 / #36312B | — | `--btn-disabled` (déjà dans `style.css`) | |

Restent en valeurs fixes : logos de marque tiers (Google, Microsoft, Indeed…) et intérieur des illustrations (personnage, confettis d'Objectif atteint).

**Ombres** (nouvelles variables, valeurs exactes) :
- `--shadow-panel: -12px 0 32px rgba(27,31,42,.12)` (panneaux latéraux) ;
- `--shadow-menu: 0 12px 32px rgba(27,31,42,.16)` (menu « … », menus du Composer) ;
- `--shadow-band-card: 0 4px 16px rgba(36,69,194,.10)` (carte à cheval sur la bande) ;
- `--shadow-composer: 0 2px 10px rgba(27,31,42,.07)`.

Ajoute les 3 jetons et les 4 ombres dans `docs/mobile/tokens.css` **et** dans `style.css`, en clair et en sombre (bloc `prefers-color-scheme` et bloc `[data-theme="dark"]`). `tokens.test.ts` doit passer.

---

## 4. Rayons (D7)

| Rayon dans la maquette | Variable |
|---|---|
| égal à la moitié de la hauteur (pilules 52/26, 56/28, 44/22, bulle de recherche, Envoyer) | `--radius-pill` |
| 6, 8, 10, 12 | `--radius-sm` (8) |
| 14, 16, 18, 20, 22, 24 | `--radius-card` (18) |
| 28 et plus sur un bloc qui n'est pas une pilule | `--radius-block` (34) |

Cas fréquents :
- panneau latéral, coin haut gauche 24 → 18 ;
- menu 16 → 18 ;
- Composer de plusieurs lignes 24 → 18 ;
- champ de formulaire 12 → 8.

---

## 5. Les lots, dans l'ordre

Chaque point indique : **Voir** (maquette, état, capture), **Où** (fichiers du dépôt à modifier en priorité), **Quoi** (changements exacts), **Fini quand** (critères d'acceptation). Les fichiers « Où » sont ceux que j'ai trouvés au commit `271fae29`. Si un fichier a bougé, cherche le composant par son commentaire d'en-tête, sans le recréer ailleurs.

### Lot 1 : jetons et mécanique commune

- **Quoi**
  - Jetons et ombres du §3.
  - Keyframes `ja-slide-r`, `ja-slide-l`, `ja-pop` dans `style.css` (copier depuis `maquettes/CandidaturesOrdinateurB.dc.html`, bloc `<style>`), dans `@media (prefers-reduced-motion: no-preference)`.
  - Composable `useDismissLayer` (nouveau, `frontend/src/composables/`) :
    - un seul panneau ou menu ouvert à la fois dans toute l'app ;
    - couche transparente plein écran (z-index 35) sous le panneau, qui ferme tout au clic ;
    - l'en-tête reste au-dessus (z-index 38) : cliquer sur la cloche quand Compte est ouvert bascule directement ;
    - Échap ferme et rend le focus au déclencheur.
- **Fini quand** : tests unitaires de `useDismissLayer` (ouvrir A ferme B, clic sur la couche ferme, Échap rend le focus).

### Lot 2 : composants partagés (nouveaux)

Un fichier `.vue` et un test par composant. Spécifications complètes : LISEZMOI, « COMPOSANTS PARTAGÉS ».

1. **`Composer.vue`**
   - **Voir** : `captures/AssistantOrdinateur.png`, `captures/etats/AssistantOrdinateur--plus.png`, `captures/etats/PreparerOrdinateur--plus.png`, `captures/etats/CandidaturesOrdinateurB--menu-ajouter.png` et `--menu-ajouter-plus.png`, `captures/etats/OffreProvisoire--sheet.png`, `captures/etats/Assistant--done.png`.
   - **Props** : `modelValue`, `placeholder`, `rows` (1 = pilule, plus de 1 = zone haute), `mic` (booléen), `sendLabel` (nom accessible d'Envoyer), `plusItems` (liste du menu +), `plusDirection` (`up` | `down`), `minChars` (Envoyer désactivé en dessous), `attachments`.
   - **Événements** : `send`, `attach`.
   - **Comportement** :
     - Entrée envoie, Maj + Entrée passe à la ligne ;
     - le champ s'agrandit jusqu'à 6 lignes (réutiliser `useAutoGrow`) ;
     - Envoyer est désactivé si le champ est vide et qu'il n'y a aucune pièce jointe ;
     - glisser-déposer accepté ;
     - pièces jointes en pastilles avec un bouton « Retirer » ;
     - menu + animé `ja-pop` depuis son coin.
2. **`SuggestionChips.vue`**
   - Pastilles au-dessus du Composer. Un clic remplit le Composer, sans envoyer.
   - **Voir** : `captures/PreparerOrdinateur.png`, `captures/Preparer.png`.
3. **`CalendarDate.vue`**
   - **Props** : `day`, `month`, `tone` (`blue` | `orp` | `past`), `size` (36 | 44 | 48 | 56), `label`.
   - **Voir** : `captures/icone_calendrier.png` et `docs/mobile/calendrier-date.html` (géométrie exacte du SVG).
   - **Tons** : blue = `--primary-graphic`, orp = `--warning`, past = `--field-border`.
   - `aria-hidden="true"`, sauf si `label` est fourni.
4. **`DateTimeField.vue`** (deux pilules date et heure) et **`DateTimePanel.vue`** (le sélecteur)
   - **Voir** : `captures/etats/CandidaturesOrdinateurB--tab-rv-dp-cal.png` (ordinateur), `captures/etats/RendezVous--dp.png` (téléphone), `captures/etats/RendezVous--vide.png` et `--noter.png` (pilules).
   - Sur ordinateur, le panneau **remplace le formulaire dans son conteneur** (pas de popover).
   - Sur téléphone, le panneau est plein écran, avec « Valider » collé en bas.
   - Raccourcis, grille de 6 semaines (lundi en premier), créneaux de 30 min de 8 h à 16 h, saisie libre : valeurs exactes dans le LISEZMOI, « Date et heure ».
   - Clavier : flèches pour les jours, Page haut et Page bas pour les mois, Entrée valide, Échap annule.
   - Formats : réutiliser `dates.ts` (« Mardi 10 novembre 2026 », « 9 h 30 »).
5. **`ProfileImage.vue`** (affiche initiales, avatar ou photo, tailles 40, 48 et 72) et **`AvatarPicker.vue`** (la fenêtre « Ton image »)
   - **Voir** : `captures/etats/ProfilOrdinateur--pick.png`, `captures/etats/ProfilOrdinateur--avatar.png`, `captures/CompteImage.png`.
   - Noms des avatars, dans l'ordre 1 à 8 : Souriant, Clin d'œil, Casque, Lunettes, Bonnet, Écharpe, Café, Étoile.
   - Stockage : §6.

**Fini quand** : chaque composant a son test (rendu, clavier, désactivation, nom accessible) et une capture dans la PR.

### Lot 3 : en-tête et panneaux de l'ordinateur

- **Voir**
  - `captures/etats/AujourdhuiOrdinateurTravailD--recherche.png`, `--menu-notif.png`, `--menu-compte.png` ;
  - `captures/etats/CandidaturesOrdinateurB--menu-notif.png`, `--menu-compte.png`, `--recherche.png` ;
  - `captures/AssistantOrdinateur.png`.
- **Où** : `AppHeader.vue`, `GlobalSearch.vue`, `NotificationBell.vue`, `AccountMenu.vue`, `SidePanel.vue`, `AssistantPanel.vue`, `AssistantMascot.vue`, `App.vue`.
- **Quoi**
  1. **AppHeader** commun à toutes les pages connectées, aligné sur 1280 px. Logo seul sur Maintenance, Pas de connexion, Premiers pas et Connexion.
  2. **GlobalSearch** devient une bulle de 44 px (bordure 1,5 px `--line-strong`) :
     - au clic, elle s'élargit à 380 px en 220 ms ;
     - bordure 2 px `--primary-graphic`, placeholder « Offres, candidatures, entreprises », bouton Fermer ;
     - Échap ferme ;
     - sans transition si `prefers-reduced-motion`.
  3. **NotificationBell** ouvre un SidePanel de 420 px :
     - groupes « Nouvelles » et « Plus tôt », point bleu sur les non lues ;
     - pied « Voir toutes les notifications » vers `/notifications`.
  4. **AccountMenu** devient un SidePanel de 420 px :
     - en-tête : ProfileImage 48 px, nom, e-mail, Fermer ;
     - « Mon compte » : Mon profil et mon CV, Mes alertes e-mail, Réglages ;
     - « Affichage » : SegmentedControl Clair, Auto, Sombre, appliqué tout de suite (`useTheme`) ;
     - « Aide » : Aide et contact ;
     - pied « Se déconnecter » en `--danger`.
     - La décision de docs/89 (« ne garde que Compte et Se déconnecter ») est remplacée : cite-la dans « Remplace » de D24.
  5. **SidePanel** en version non modale :
     - sans voile, sous l'en-tête, coin haut gauche `--radius-card`, ombre `--shadow-panel`, animation `ja-slide-r` 220 ms ;
     - focus sur le titre à l'ouverture, retour au déclencheur à la fermeture ;
     - `role="complementary"` ;
     - passe par `useDismissLayer`.
  6. **Assistant** :
     - bouton flottant en bas à droite, qui ouvre un SidePanel de 480 px ;
     - en-tête avec le logo de l'Assistant **sans cercle** (32 px) ;
     - chaque message de l'Assistant a le logo sans cercle de 28 px à sa gauche ; pas d'avatar pour l'utilisateur ;
     - Composer d'une ligne, placeholder « Demander à l'Assistant », mention dessous « L'Assistant peut se tromper. Relis toujours avant d'envoyer. » ;
     - le bouton flottant est masqué quand un autre panneau, les filtres ou le sélecteur de date sont ouverts.
  7. L'image choisie (ProfileImage) remplace le K partout : en-tête 40 px, nom accessible « Compte de Kevin » (prénom de l'utilisateur).
- **Fini quand** :
  - un seul panneau à la fois ;
  - cloche puis K bascule sans fermer d'abord ;
  - clic à l'extérieur ferme ;
  - Échap rend le focus ;
  - captures identiques aux maquettes, à la traduction des jetons près.

### Lot 4 : Candidatures sur ordinateur (maquette `CandidaturesOrdinateurB`)

Ce lot remplace ce que les PR #559 et #561 ont codé d'après l'ancienne maquette `CandidaturesOrdinateur` / `RendezVousOrdinateur`.

- **Voir**
  - `captures/CandidaturesOrdinateurB.png` (à traiter) ;
  - `captures/etats/CandidaturesOrdinateurB--tab-en.png`, `--tab-rv.png`, `--tab-rv-dp-cal.png`, `--menu-actions.png`, `--menu-filtres.png`, `--menu-ajouter.png`, `--menu-ajouter-plus.png`.
- **Où** : `ApplicationsView.vue`, `OffersView.vue`, `JobsView.vue`, `ListCard.vue`, `OfferCard.vue`, `SentCard.vue`, `OfferDetail.vue`, `OfferFilterPopover.vue` (à supprimer), `OfferFilterSheet.vue` (contenu à réutiliser), `MoreMenu.vue`, `ManualOfferForm.vue`, `RendezVousDesktop.vue`, `OrpMeetingForm.vue`, `OrpOutcomeSheet.vue`, `OrpMeetingView.vue`.
- **Quoi**
  1. Onglets « À traiter · Envoyées · Rendez-vous » (Q5).
  2. Colonne liste :
     - champ « Filtrer par titre ou entreprise » (icône entonnoir) et bouton « Plus de filtres » ;
     - **pas de seconde loupe** (la recherche globale est dans l'en-tête) ;
     - cartes de liste et style de sélection **inchangés** par rapport à ce qui est en production (Kevin a refusé tout changement de sélection).
  3. « Plus de filtres » : le panneau **remplace la colonne liste** (même largeur, toute la hauteur, `ja-slide-l` 200 ms) :
     - en-tête « ‹ Retour à la liste » + titre « Filtres » ;
     - pastilles `aria-pressed` ;
     - pied fixe avec « Tout effacer » et « Afficher n offres » (compteur en direct) ;
     - le détail reste visible à droite ;
     - les choix sont gardés si on ferme par un clic à l'extérieur.
     - Supprime `OfferFilterPopover.vue` et ses tests. Réutilise la logique de `useOfferFilters` et le contenu de `OfferFilterSheet.vue`.
  4. Détail : jamais vide (premier élément choisi par défaut). Bloc de note sans cadre, traits pleine largeur. « Objectif ORP » est une carte cliquable vers Bilan, avec « › ».
  5. Menu « … » (`MoreMenu`, `role="menu"`, 280 px, `ja-pop` depuis le coin haut droit), dans cet ordre :
     - Ouvrir l'annonce sur le site ;
     - Garder pour plus tard ;
     - Voir le détail de la note ;
     - Copier le lien ;
     - séparateur ;
     - Signaler une erreur dans l'offre.
  6. Lien « Mes alertes e-mail » et bouton « + Ajouter une offre » à sa droite. Le bouton ouvre un dialogue :
     - Composer de 3 lignes, placeholder « Lien ou texte de l'annonce » ;
     - menu + vers le bas : Importer le PDF de l'annonce, Importer une capture d'écran ;
     - Envoyer = « Ajouter l'offre » ;
     - branché sur la logique existante de `ManualOfferForm.vue` (docs/111).
  7. Onglet Envoyées : même carte que À traiter, statut à droite (Sans réponse, Entretien, Vue, Envoyée, Refusée), icône de statut **sans fond** (D23).
  8. Onglet Rendez-vous : refais `RendezVousDesktop.vue` d'après `--tab-rv.png` :
     - CalendarDate à la place des carrés de date ;
     - DateTimeField dans le formulaire ;
     - DateTimePanel qui remplace le formulaire (`--tab-rv-dp-cal.png`) ;
     - « Aucun rendez-vous à venir » = ligne de texte + bouton Ajouter, sans carte (D22) ;
     - remplace les `input type="time"` natifs de `OrpMeetingForm.vue` et `OrpOutcomeSheet.vue`.
- **Fini quand** : les 10 captures de ce lot correspondent ; plus aucun popover de filtres ; plus aucun champ date ou heure natif ; tests mis à jour (`OffersView.test.ts`, `ApplicationsView.test.ts`, `OrpMeetingView.desktop.test.ts`).

### Lot 5 : Aujourd'hui sur ordinateur

- **Voir** : `captures/AujourdhuiOrdinateurTravailD.png`, `captures/AujourdhuiOrdinateurReposD.png`.
- **Où** : `TodayView.vue` (partie ordinateur), `OrpMonth.vue`, `RhythmCard.vue`, `FirstSteps.vue`, `PageHero.vue`.
- **Quoi**
  1. Bande `--primary-soft` sur toute la largeur sous l'en-tête. Elle contient la date en petites capitales, le H1 et le sous-titre, centrés sur 880 px.
  2. H1 :
     - jour de travail : l'action du jour (« 2 candidatures à envoyer. »), calculée à partir du rythme nécessaire pour l'objectif ORP ;
     - jour de repos : « Jour de repos. » ;
     - la fin du H1 (« à envoyer. », « repos. ») est en `--font-hand`, 1.45em, `--primary-graphic`, line-height 0 ;
     - le H1 reste **un seul élément** de titre.
  3. Carte « Mois ORP » à cheval sur le bord bas de la bande :
     - bordure `--water`, ombre `--shadow-band-card` ;
     - cliquable vers Bilan ;
     - le mois à gauche, la semaine à droite, séparés par un trait vertical.
  4. Tâches sur une colonne de 880 px, dans l'ordre : en retard, envoyer, trier, préparer un entretien, puis la section « Quand tu as le temps » (relances).
     - Une carte cliquable par tâche ;
     - icône seule de 24 px dans la couleur du ton : retard `--peach-text`, normal `--primary-graphic`, entretien `--success` ;
     - libellé d'action coloré suivi de « › », pas de bouton.
- **Fini quand** : les deux captures correspondent ; un seul accent manuscrit par écran.

### Lot 6 : Bilan, Préparer, Profil sur ordinateur

- **Bilan**
  - **Voir** : `captures/BilanOrdinateur.png`, `captures/etats/BilanOrdinateur--tab-res.png`, `--tab-form.png`.
  - **Où** : `BilanView.vue`, `BilanOrpView.vue`, `TrainingsView.vue`, `components/bilan/*`.
  - **Quoi** : onglets ORP, Résultats, Formations ; même bande et même carte à cheval que sur Aujourd'hui ; CalendarDate de 36 px dans les lignes ; sections en lignes séparées par un trait (pas de points de couleur).
- **Préparer**
  - **Voir** : `captures/PreparerOrdinateur.png`, `captures/etats/PreparerOrdinateur--tab-cv.png`, `--tab-pos.png`, `--plus.png`.
  - **Où** : `PreparationView.vue`.
  - **Quoi** :
    - étapes « 1. Lettre », « 2. CV », « 3. Postuler » (`tab` = let, cv, pos) ;
    - sous la lettre : SuggestionChips (Plus court, Plus formel, Insister sur Terraform, En allemand) + Composer d'une ligne « Demander une modification de la lettre » ;
    - menu + : Joindre l'annonce complète, Joindre un document ;
    - **supprime** le bouton « Modifier le texte avec l'Assistant » ;
    - le bouton flottant de l'Assistant reste masqué sur cette page.
  - « Insister sur Terraform » est un exemple de la maquette. La pastille réelle doit venir d'une compétence du profil qui figure dans l'annonce. Si la donnée n'existe pas, garde les trois premières pastilles seulement et signale-le.
- **Profil**
  - **Voir** : `captures/ProfilOrdinateur.png`, `captures/etats/ProfilOrdinateur--pick.png`, `--avatar.png`.
  - **Où** : `ProfileView.vue`, `IdentityForm.vue`.
  - **Quoi** :
    - ProfileImage 72 px avec pastille crayon, bouton « Changer d'image » ;
    - AvatarPicker : grille, `aria-pressed`, anneau 3 px `--primary-graphic`, Annuler ou Enregistrer ;
    - texte « Elle s'affiche seulement dans jobA1. Elle n'est jamais envoyée aux employeurs. »

### Lot 7 : Notifications, Alertes, Réglages sur ordinateur

- **Voir** : `captures/NotificationsOrdinateur.png`, `captures/etats/NotificationsOrdinateur--tab-un.png`, `captures/AlertesOrdinateur.png`, `captures/ReglagesOrdinateur.png`.
- **Où** : `NotificationsView.vue`, `NotificationRow.vue`, `AlertsView.vue`, `AlertsPanel.vue`, `AlertSearchCard.vue`, `SettingsView.vue`, `SettingRow.vue`, `SettingsSection.vue`.
- **Quoi**
  - contenu centré sur 880 px ;
  - informations seules en listes sans cadre (D22) ;
  - icônes sans fond (D23) ;
  - Notifications : onglets Toutes, Non lues ;
  - Alertes : bandeau `--peach-soft` (bordure `--peach`) avec bouton tonal, puis la liste des recherches suivies et « + Ajouter ».

### Lot 8 : pages d'état, Connexion, Premiers pas sur ordinateur

- **Voir** : `captures/<Fichier>.png` pour PageIntrouvableOrdinateur, MaintenanceOrdinateur, HorsLigneOrdinateur, CandidatureEnvoyeeOrdinateur, ObjectifAtteintOrdinateur, AucuneOffreOrdinateur, ConnexionOrdinateur, OnboardingOrdinateur ; `captures/etats/OnboardingOrdinateur--step-2.png`, `--step-3.png`.
- **Où** : `NotFoundView.vue`, `MaintenanceOverlay.vue`, `NetworkError.vue`, `ApplicationSent.vue`, `GoalReached.vue`, `MomentScreen.vue`, `CharacterState.vue`, `LoginView.vue`, `AuthSplit.vue`, `WelcomeView.vue`.
- **Quoi**
  - centré sur 880 px, personnage de 240 px (360 px aux premiers pas, D27) ;
  - en-tête avec logo seul pour Maintenance, Pas de connexion, Premiers pas et Connexion ;
  - « Aucune offre » garde l'en-tête complet et la colonne de filtres ;
  - Premiers pas en 3 étapes (`step` = 1, 2, 3).
- **Fini quand** : `personnage.test.ts` passe et la liste de docs/141 §3 n'a pas bougé.

### Lot 9 : téléphone (éléments partagés)

| # | Écran | Voir | Où | Quoi |
|---|---|---|---|---|
| 1 | Assistant | `captures/Assistant.png`, `etats/Assistant--done.png` | `AssistantPanel.vue` (téléphone) | Composer pilule (+, champ, micro, Envoyer) ; logo **sans cercle** à gauche des messages de l'Assistant ; l'icône de la barre du bas garde son cercle. |
| 2 | Préparer | `captures/Preparer.png`, `captures/PreparerSombre.png` | `PreparationView.vue` | Le lien « Modifier le texte avec l'Assistant » devient la section « Retoucher la lettre » : SuggestionChips + Composer, placeholder « Que changer ? ». Icône Canva sans fond. |
| 3 | Offre provisoire | `etats/OffreProvisoire--refused.png`, `--sheet.png`, `--done.png` | `OfferTextNotice.vue`, `BottomSheet.vue` | Feuille « Coller le texte de l'annonce » : Composer de 5 lignes ; Envoyer = « Enregistrer et refaire la note », désactivé sous 200 caractères (`minChars`) ; compteur sous la zone. Icônes sans fond. |
| 4 | Ajouter une offre | `captures/AjouterOffreTel.png` | `ManualOfferForm.vue` dans `BottomSheet.vue` | Feuille du bas avec Composer de 4 lignes, même menu + que sur ordinateur. |
| 5 | Envoyées | `captures/Envoyees.png`, `captures/EnvoyeesSombre.png` | `SentCard.vue` | Icônes de statut sans fond. |
| 6 | Rendez-vous | `captures/RendezVous.png`, `etats/RendezVous--vide.png`, `--noter.png`, `--dp.png`, `etats/RendezVousSombre--noter.png` | `RendezVousPhone.vue`, `OrpMeetingForm.vue`, `OrpOutcomeSheet.vue`, `OrpMeetingEmpty.vue` | CalendarDate 48 px ; DateTimeField dans le formulaire vide et dans la feuille « Ce qui a été convenu » ; DateTimePanel plein écran. |
| 7 | Compte | `captures/Compte.png`, `captures/CompteImage.png` | `AccountView.vue` | ProfileImage avec pastille crayon ; un toucher ouvre la feuille du bas « Ton image » (grille de 5 colonnes, AvatarPicker). |
| 8 | Alertes e-mail | `captures/AlertesTel.png` | `AlertsView.vue` (téléphone) | Retour, titre « Alertes e-mail », bandeau pêche Indeed avec bouton tonal, liste des recherches suivies, « + Ajouter ». |
| 9 | Réglages | `captures/Reglages.png` | `SettingsView.vue`, `SettingRow.vue` | Icônes sans fond, 1,5 fois plus grandes qu'avant (taille exacte dans le HTML). |
| 10 | Bilan, résultats | `captures/BilanResultats.png` | `BilanView.vue`, `components/bilan/*` | Sections en lignes séparées par un trait, plus de points ; bouton tonal pleine largeur dans « Le carnet ». Vérifie d'abord : si c'est déjà en production, ne touche à rien et écris-le. |
| 11 | Extension | `captures/ExtAnnonce.png`, `captures/ExtAlerte.png` | `extension/` (`popup`, `annonce.js`, `alertes.js`) | Icônes sans fond, 1,5 fois plus grandes. |
| 12 | Accueil | `captures/AccueilSmile.png` | — | Déjà conforme : ne rien changer. |

### Lot 10 : vérification finale

1. Parcours complet à 390 px et 1440 px, en clair et en sombre : chaque écran des deux index du LISEZMOI, à côté de sa capture.
2. `grep` sur `frontend/src` : aucun hexadécimal du §3 en dur, aucun `type="date"` ni `type="time"`, aucune pastille de fond derrière une icône décorative.
3. Clavier seul : ouvrir et fermer chaque panneau, chaque menu, les filtres, le sélecteur de date, l'AvatarPicker. Le focus revient toujours au déclencheur.
4. `prefers-reduced-motion: reduce` : aucune animation.
5. Remplis « Écarts connus » de docs/143 avec tout ce qui ne suit pas la maquette, avec la raison.

---

## 6. Données (docs/regles-securite-donnees.md)

- **Image de profil**
  - L'avatar choisi est un numéro de 1 à 8, stocké comme les coordonnées de `IdentityForm.vue` (base locale).
  - La photo importée (JPG ou PNG, 5 Mo maximum, recadrée en cercle) reste **locale**. Elle n'est jamais envoyée au serveur, à l'IA ni aux employeurs.
  - Si une règle de sécurité l'interdit ou exige autre chose, arrête-toi et demande.
- **Pièces jointes du Composer** (PDF, Word, image, 10 Mo maximum ; « Joindre mon CV » ; « Joindre une offre de ma liste »)
  - Elles partent vers l'IA seulement à l'envoi, avec la même règle que les autres textes envoyés à l'IA.
  - Cite la règle dans la PR. Si aucune règle ne couvre l'envoi d'un fichier à l'IA, code le menu + **sans** « Importer un fichier » et signale-le.
- **Dictée (micro)**
  - Utilise l'API de dictée du navigateur seulement si elle existe, sinon cache le bouton.
  - Certains navigateurs envoient l'audio à leur éditeur. Vérifie la règle : si elle l'interdit, cache le micro partout et signale-le.

---

## 7. Ce qu'il ne faut pas faire

- Changer le style de sélection des cartes de liste, le menu principal ou les couleurs de l'en-tête.
- Ajouter un voile derrière les panneaux latéraux.
- Mettre un bouton dans une carte cliquable.
- Mettre un fond coloré derrière une icône décorative.
- Mettre plus d'un accent manuscrit par écran, ou un accent ailleurs que sur un écran « moment ».
- Mettre le personnage sur un écran de travail.
- Garder un popover de filtres, un champ date ou heure natif, ou un carré de date coloré.
- Créer un composant qui existe déjà : réutilise `SidePanel`, `BottomSheet`, `MoreMenu`, `SegmentedControl`, `useAutoGrow`, `useOfferFilters`, `dates.ts`.
- Recréer une maquette abandonnée (liste du §1, point 10).

---

## 8. Lot 11 : corrections du 8 novembre au soir (une PR)

Validé par Kevin le 2026-11-08. Les maquettes et les captures du zip sont déjà corrigées.

1. **Champs de formulaire**
   - **Voir** : `captures/etats/CandidaturesOrdinateurB--tab-rv-ajouter.png`.
   - **Où** : la règle de base des champs dans `style.css` (vers la ligne 563).
   - **Quoi** : hauteur 48 px, bordure 1,5 px `var(--text-secondary)`, fond `var(--surface)`, rayon `var(--radius-sm)`. Une seule règle pour tous les formulaires, Coordonnées compris. Le focus garde l'anneau existant. Le Composer n'est pas un champ de formulaire.
   - Ajoute dans « Écarts connus » : « Champs : 12 px dans l'ancienne maquette, 8 px (D7). »
2. **En-tête ordinateur**
   - **Voir** : `captures/etats/CandidaturesOrdinateurB--cloche-sans-nouvelle.png`, `captures/CandidaturesOrdinateurB.png`.
   - **Où** : `AppHeader.vue`, `NotificationBell.vue`, `GlobalSearch.vue`, `AccountMenu.vue`.
   - **Quoi** :
     - recherche, cloche et avatar dans un seul groupe, écart 16 px ; les 32 px restent entre logo, menu et ce groupe ;
     - les trois éléments font 44 px ;
     - cloche sans notification : rond `var(--surface)`, bordure 1,5 px `var(--line-strong)`, nom accessible « Notifications, aucune nouvelle » ;
     - cloche avec notifications : capsule pêche, 44 px de haut.
3. **Assistant qui écrit**
   - **Voir** : `captures/etats/AssistantOrdinateur--attente.png`, `captures/etats/Assistant--ecrit.png`.
   - **Où** : `AssistantPanel.vue` et le composant de message.
   - **Quoi** :
     - aucune bulle tant qu'aucun texte n'est arrivé ;
     - à la place : le logo sans cercle (28 px) + une bulle de 46 px de haut avec 3 points de 8 px `var(--text-secondary)`, animation `ja-dot` 1,2 s décalée de 0,15 s (keyframes dans `AssistantOrdinateur.dc.html`) ;
     - `role="status"`, `aria-live="polite"`, texte masqué « L'Assistant écrit… » ;
     - au premier morceau de texte, la bulle de réponse remplace les points ; supprime l'élément « … » sous la liste ;
     - avec `prefers-reduced-motion`, points fixes à 60 % d'opacité ;
     - la feuille d'étapes « Je rédige ta lettre… » (`AiWriting`) reste pour les tâches longues.
4. **Mes alertes e-mail**
   - **Voir** : `captures/AlertesOrdinateur.png`, `captures/AlertesTel.png`.
   - **Où** : `AlertsView.vue`, `AlertsPanel.vue`, `AlertSearchCard.vue`, le routeur ou le composable qui retient la dernière page de Candidatures.
   - **Quoi** :
     - `/candidatures/alertes` n'est plus retenue comme dernière page ;
     - sur ordinateur, lien « ‹ Candidatures » au-dessus du H1 (44 px, `var(--primary-text)`), qui ramène à la liste avec l'onglet gardé ;
     - liste des recherches sans cadre, lignes séparées par `var(--line-soft)` ;
     - « Créer l'alerte » devient un libellé `var(--primary-text)`, 15 px, gras, suivi de « › » ;
     - « + Ajouter une recherche » reste le seul bouton à contour.
5. **Nouveau rendez-vous sur ordinateur**
   - **Voir** : `captures/etats/CandidaturesOrdinateurB--tab-rv-ajouter.png`.
   - **Où** : `RendezVousDesktop.vue`, `OrpMeetingForm.vue`.
   - **Quoi** :
     - « Ajouter » ouvre le formulaire dans le panneau de détail, **sans carte autour** (pas de fond, de bordure ni de rayon propres) ;
     - contenu : titre « Prochain rendez-vous ORP » (26 px, 800), phrase d'aide, DateTimeField (Date, Heure), « Lieu ou lien (facultatif) », « Ajouter le rendez-vous » (bouton plein, 52 px) et « Annuler » (texte) ;
     - sur téléphone, la carte reste.

Captures avant et après de chaque point, en clair et en sombre, à 1440 et 390 px.

---

## 9. Lot 12 : détail d'Envoyées en deux colonnes (ordinateur)

Validé par Kevin le 2026-11-08. Le contenu ne change pas, seule la disposition change.

- **Voir** : `captures/etats/CandidaturesOrdinateurB--tab-en.png` (haut du panneau) et `--tab-en-bas.png` (bas du panneau, après défilement).
- **Où** : `OfferDetail.vue` ou le composant du détail d'une candidature envoyée (celui qui affiche Statut, Documents, Contacts, Premier message, Prises de contact), seulement au-dessus de 820 px.
- **Quoi**
  1. En-tête inchangé : logo de l'entreprise, titre H2 **gras 24 px en `var(--text)`** (aujourd'hui gris clair et fin en production : à corriger), entreprise et lieu, étiquettes, menu « … ».
  2. Sous l'en-tête, un trait `var(--line-soft)`, puis une grille : `grid-template-columns: minmax(0, 1fr) 240px`, `column-gap: 48px`.
  3. Colonne de gauche, dans cet ordre :
     - **Statut** : liste déroulante de 200 px, puis « Sans réponse depuis n jours. Relancer › » et « Relance à faire · Changer » ;
     - **Premier message** : « Écrire à » puis « Canal », **l'un sous l'autre**, en pleine largeur (formulaire d'une colonne), puis le bouton à contour « Rédiger un message » (48 px, `--radius-pill`, icône crayon) ;
     - **Prises de contact** : « Aucun contact pour l'instant. » puis « J'ai contacté quelqu'un › ».
  4. Colonne de droite, `<aside aria-label="Documents et contacts">`, `padding-left: 40px`, trait à gauche `var(--line-soft)` :
     - **Documents** : « Lettre (Word) » avec l'icône de téléchargement ;
     - **Contacts** : sous-titre « Trouver quelqu'un », puis les liens Recrutement, L'équipe du poste, Anciens de 42 Lausanne, chacun avec l'icône de lien externe et une cible de 44 px. Raccourcis le libellé en « L'équipe du poste », sans l'intitulé entre parenthèses.
  5. **Espacements** : 32 px au-dessus et 36 px sous chaque section, séparées par un trait `var(--line-soft)` ; 16 px sous chaque titre ; 20 px entre les champs ; 24 px au-dessus de « Rédiger un message ».
  6. **Ordre du DOM** : la colonne de gauche entière, puis la colonne de droite (lecture et tabulation, WCAG 1.3.2).
  7. Les boutons du détail ont tous des bords ronds (`--radius-pill`) : plus de bouton rectangulaire à 8 px.
  8. Sur téléphone (820 px et moins), rien ne change : une seule colonne, dans l'ordre Statut, Documents, Contacts, Premier message, Prises de contact.

Captures avant et après, en clair et en sombre, à 1440 px, en haut et en bas du panneau.

---

## 10. Lot 13 : À traiter en deux colonnes, rendez-vous à 560 px, Profil (ordinateur)

Validé par Kevin le 2026-11-08. Même logique que le lot 12, au-dessus de 820 px seulement.

1. **Détail d'une offre à traiter**
   - **Voir** : `captures/CandidaturesOrdinateurB.png`, `captures/etats/CandidaturesOrdinateurB--tab-tr-bas.png`.
   - **Où** : `OfferDetail.vue` (détail d'une offre de l'onglet À traiter), `OfferTextNotice.vue`.
   - **Quoi** :
     - au-dessus des colonnes, inchangés : logo, titre H2, entreprise, étiquettes, « Préparer ma candidature » et « Écarter » ;
     - grille `minmax(0, 1fr) 240px`, `column-gap: 48px`, trait `var(--line-soft)` au-dessus ;
     - **à gauche** : la note (anneau, verdict, explication, critères en ligne qui passent à la ligne si besoin), le bandeau « Il manque l'annonce complète » en **bloc** `var(--peach-soft)`, bordure `var(--peach)`, `--radius-card`, avec le texte au-dessus et les boutons (44 px) en dessous, puis « Le détail de la note › » ; ensuite la section « Le poste » ;
     - **à droite** : `<aside aria-label="L'offre en bref">`, `padding-left: 40px`, trait à gauche ; titre « L'offre en bref », puis une liste `<dl>` : Lieu, Contrat, Taux d'activité, Reçue, avec le libellé (14 px, `var(--text-secondary)`) **au-dessus** de la valeur (16 px, 700) et un trait entre les lignes ; puis le lien « Voir l'annonce sur le site » avec l'icône de lien externe ;
     - une donnée absente s'écrit « Non précisé », jamais une ligne vide ;
     - espacements du lot 12 (32 px au-dessus et 36 px sous chaque section, 16 px sous les titres) ;
     - ordre du DOM : gauche puis droite.
2. **Formulaires de rendez-vous** (« Ce qui a été convenu » et « Prochain rendez-vous ORP ») : `max-width: 560px` dans le panneau de détail. Pas de deuxième colonne.
3. **« Ce que je cherche »** (Profil et Premiers pas, ordinateur) : dans chaque ligne, le libellé (14 px, `var(--text-secondary)`) **au-dessus** de la valeur (16 px, 700), à gauche ; hauteur 68 px ; chevron à droite. La valeur n'est plus collée au bord droit (Laws of UX, proximité). Sur téléphone, rien ne change.

Captures avant et après, en clair et en sombre, à 1440 px.

---

## 11. Lot 14 : rendez-vous ORP structuré (ordinateur)

Validé par Kevin le 2026-11-08.

- **Voir** : `captures/etats/CandidaturesOrdinateurB--tab-rv.png` (haut) et `--tab-rv-bas.png` (bas du panneau).
- **Où** : `RendezVousDesktop.vue`, `OrpMeetingForm.vue`, `OrpOutcomeSheet.vue` (version ordinateur), cartes de la liste des rendez-vous.
- **Quoi**
  1. **Supprime les pastilles « Noté » et « Pas encore noté »**, dans la liste et dans le détail, sur ordinateur et sur téléphone. Les groupes « À noter » et « Passés » donnent déjà l'information. Garde le nom accessible du groupe.
  2. En-tête du détail inchangé : CalendarDate 56 px, titre H2, date, heure et lieu, menu « … ». Aucune ligne vide sous l'en-tête.
  3. Grille sous un trait `var(--line-soft)` : `grid-template-columns: minmax(0, 560px) 240px`, `justify-content: space-between`, `column-gap: 48px`.
  4. **À gauche**, le formulaire :
     - sur-titre « Ce qui a été convenu » (13 px, capitales, `var(--text-secondary)`) ;
     - trois `<fieldset>`, chacun avec un `<legend>` (18 px, 700), une phrase d'aide (14 px, `var(--text-secondary)`), puis le contrôle :
       1. « Objectif de recherches » : « Le nombre de recherches que l'ORP te demande chaque mois. », puis le compteur − 13 + et « Comme le mois dernier » ;
       2. « Mesures décidées (facultatif) » : « Un cours, un stage ou un programme proposé par ta conseillère. », puis le champ ;
       3. « Prochain rendez-vous (facultatif) » : « jobA1 prépare ta feuille la veille et te le rappelle le matin. », puis DateTimeField avec les libellés « Date » et « Heure » ;
     - fieldsets séparés par un trait, 28 px au-dessus et 32 px en dessous ;
     - « Enregistrer » en bas, bouton plein de 52 px.
  5. **À droite**, `<aside aria-label="Le rendez-vous">`, `padding-left: 40px`, trait à gauche : titre « Le rendez-vous », puis `<dl>` Date, Heure, Lieu, Objectif jusqu'ici (libellé au-dessus de la valeur, comme « L'offre en bref »).
  6. **Date dans la pilule** : format court « Mar. 10 nov. 2026 » dès que la pilule fait moins de 280 px, jamais sur deux lignes (`white-space: nowrap`). Le format long reste dans le sélecteur et dans « Le rendez-vous ».
  7. Sur téléphone : seulement le point 1. Le reste ne change pas.

Captures avant et après, en clair et en sombre, à 1440 px, en haut et en bas du panneau.

---

## 12. Lot 15 : Préparer (ordinateur) et « J'ai déjà postulé »

Validé par Kevin le 2026-11-08. **La disposition de la production est gardée** (lettre à gauche, colonne d'aide à droite) : la maquette PreparerOrdinateur a été refaite dans ce sens et remplace l'ancienne (réglages à gauche).

1. **En-tête de Préparer**
   - **Voir** : `captures/PreparerOrdinateur.png`.
   - **Où** : `PreparationView.vue`.
   - **Quoi** :
     - une seule ligne de 64 px, tout centré verticalement (`align-items: center`) : « ‹ Retour à l'offre », trait vertical, logo 44 px, **H1 = intitulé du poste** (24 px, 800) avec l'entreprise et le lieu dessous, l'anneau de la note, les étapes « 1. Lettre », « 2. CV », « 3. Postuler » ;
     - supprime le texte « Ma candidature » à l'écran ; garde-le dans le `<title>` de la page (« Ma candidature, DevOps Engineer, jobA1 ») ;
     - **anneau** 48 px, le chiffre au centre (D12), et à sa droite le verdict (Proche, À creuser, Loin) dans la couleur du verdict (D5), avec « de ton profil » dessous.
2. **Colonne de droite** : `grid-template-columns: minmax(0, 1fr) 360px`, `gap: 24px`. Trois cartes, dans cet ordre :
   1. **Mise en page** : « Le modèle s'applique à la lettre et au CV. », pastilles Sobre, Moderne, Bandeau, Classique (`aria-pressed`), puis « Tient sur une page A4 · n mots ». Visible aux étapes Lettre **et** CV. Les modèles existent déjà dans le code du téléphone : réutilise-les, mêmes noms (« Classique » partout).
   2. **Pour cette offre** :
      - sous le titre, « n points forts · n à vérifier » ;
      - **plus de verdict ici**, ni l'ancien onglet « À creuser » souligné : il est dans l'en-tête ;
      - deux groupes titrés : « Points forts (n) » avec une coche `var(--success)`, et « À vérifier (n) » avec un point d'attention `var(--peach-text)` ;
      - chaque élément : le sujet en gras (15 px), le détail dessous (14 px, `var(--text-tertiary)`), 10 px au-dessus et en dessous ;
      - la couleur n'est jamais le seul repère (WCAG 1.4.1) ;
      - plus de « Afficher moins » : la colonne défile.
   3. **Nouvelle version** : « Repartir de zéro avec l'annonce et ton CV. », bouton à contour « Rédiger la nouvelle version » (48 px, `--radius-pill`), puis le lien « Ce qui part à l'IA › ».
3. **Lettre** : carte avec l'en-tête « Lettre de motivation » et le SegmentedControl FR, DE, EN à droite ; l'aperçu sur fond `var(--surface-muted)`. La ligne « Consigne : Plus court » disparaît : la consigne passe par les suggestions et la zone de saisie.
4. **Bas de page** : suggestions + Composer sous la lettre ; « J'ai relu la lettre » (bouton plein, 52 px) aligné à droite sous la colonne d'aide.
5. **« J'ai déjà postulé » dans À traiter**
   - **Voir** : `captures/CandidaturesOrdinateurB.png`.
   - **Où** : le détail d'une offre (`OfferDetail.vue`) sur ordinateur, et la même action dans le détail d'une offre sur téléphone (`Offre`), à côté de « Ignorer ».
   - **Quoi** : bouton à contour « J'ai déjà postulé » à droite de « Écarter ». Au clic, réutilise le parcours existant de « Marquer comme envoyée » : écran `ApplicationSent`, puis l'offre passe dans Envoyées avec la date du jour, modifiable. « Préparer ma candidature » reste le seul bouton plein.

Captures avant et après, en clair et en sombre, à 1440 px, aux étapes Lettre et CV.
