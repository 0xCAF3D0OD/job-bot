# jobA1 : modifications du 8 novembre au soir (lots 11 à 18), version finale

Ce document **remplace toutes les versions précédentes** de ce fichier et les anciens §8 à §14 de `PROMPT_CLAUDE_CODE.md`.
Il est complet : avec lui, il te faut seulement le zip et `PROMPT_CLAUDE_CODE.md` §0 à §7 (règles générales, jetons, rayons, lots 0 à 10).
Tout a été validé par Kevin le 2026-11-08. Les maquettes et les captures du zip sont à jour : elles font foi.

---

## 0. Règles de travail (non négociables)

1. **Ne rien improviser.** Tout ce qui ne se trouve ni ici, ni dans le LISEZMOI, ni dans une capture va dans « Questions pour Kevin » de la PR.
2. **Couleurs** : uniquement des jetons (table du §3 de `PROMPT_CLAUDE_CODE.md`, plus les jetons ajoutés au §2.6 ci-dessous). **Rayons** : 8, 18, 34 ou 999 (D7).
3. **Seuil** : téléphone <= 820 px, ordinateur > 820 px (D8).
4. **Une PR par lot**, dans l'ordre du §1.2. Chaque PR contient :
   - la liste des points du lot, cochés un par un ;
   - « Règles vérifiées : … » ;
   - les captures avant et après, en clair **et** en sombre, à 1440 px et 390 px quand les deux changent ;
   - une entrée dans `changelog.d/`.
5. Chaque écart à la maquette va dans « Écarts connus » de `docs/143-maquette-8-novembre.md`.
6. Les maquettes ne s'ouvrent pas seules (`support.js` absent). Le rendu se lit dans les PNG :
   - `captures/<Fichier>.png` : état par défaut ;
   - `captures/etats/<Fichier>--<état>.png` : états ouverts ;
   - `captures/etats/<Fichier>--bas.png` : bas de page après défilement.
7. **Mise en place** : remplace `docs/mobile/` par le contenu du zip (maquettes, captures, LISEZMOI, ce fichier, `PROMPT_CLAUDE_CODE.md`), et `frontend/public/personnage/` par `illustrations/personnage/` (mêmes noms, plus les bustes).

---

## 1. Vue d'ensemble

### 1.1 Tableau des changements

| Lot | Écran ou sujet | Ce qui change | Maquettes | Captures (dans `captures/`) |
|---|---|---|---|---|
| 17 | Zone de saisie (Composer) | Bug du champ dans la pilule, focus, + et micro | Assistant, AssistantOrdinateur | `Assistant.png`, `etats/AssistantOrdinateur--plus.png` |
| 11.1 | Tous les formulaires | Style unique des champs | RendezVous, CandidaturesOrdinateurB, Connexion | `etats/CandidaturesOrdinateurB--tab-rv-ajouter.png` |
| 11.2 | En-tête ordinateur | Groupe, 44 px, cloche sans notification | toutes les pages ordinateur | `etats/CandidaturesOrdinateurB--cloche-sans-nouvelle.png` |
| 11.3 | Assistant | Indicateur « écrit » | AssistantOrdinateur, Assistant | `etats/AssistantOrdinateur--attente.png`, `etats/Assistant--ecrit.png` |
| 11.4 | Mes alertes e-mail | Retour, liste sans cadre | AlertesOrdinateur, AlertesTel | `AlertesOrdinateur.png`, `AlertesTel.png` |
| 11.5 | Nouveau rendez-vous (ordinateur) | Formulaire sans carte | CandidaturesOrdinateurB | `etats/CandidaturesOrdinateurB--tab-rv-ajouter.png` |
| 12 | Envoyées, détail (ordinateur) | Deux colonnes | CandidaturesOrdinateurB | `etats/CandidaturesOrdinateurB--tab-en.png`, `--tab-en-bas.png` |
| 13.1 | À traiter, détail (ordinateur) | Deux colonnes | CandidaturesOrdinateurB | `CandidaturesOrdinateurB.png`, `etats/CandidaturesOrdinateurB--tab-tr-bas.png` |
| 13.2 | Profil, Premiers pas (ordinateur) | Libellé au-dessus de la valeur | ProfilOrdinateur, OnboardingOrdinateur | `ProfilOrdinateur.png` |
| 14 | Rendez-vous, détail (ordinateur) | Sans pastille « Noté », 3 sections | CandidaturesOrdinateurB | `etats/CandidaturesOrdinateurB--tab-rv.png`, `--tab-rv-bas.png` |
| 15.1 | Préparer (ordinateur) | En-tête, Mise en page, Pour cette offre | PreparerOrdinateur | `PreparerOrdinateur.png`, `etats/PreparerOrdinateur--colonne-bas.png` |
| 15.2 | À traiter | « J'ai déjà postulé » | CandidaturesOrdinateurB, Offre | `CandidaturesOrdinateurB.png` |
| 16.1 | Assistant | Pastilles de suggestion | Assistant | `Assistant.png` |
| 16.2 | Personnage | Pantalon | tous | `illustrations/personnage/` |
| 16.3 | Personnage | Buste dans les écrans chargés | RendezVous, Connexion, OnboardingC | `etats/RendezVous--vide.png`, `Connexion.png`, `etats/OnboardingC--etape-1.png` |
| 16.4 | Justificatifs ORP | Mots et phrase d'aide | Orp, Explorer, BilanOrdinateur | `Orp.png`, `BilanOrdinateur.png` |
| 18 | Style « blocs » | Règles D28 à D34, écrans refaits | voir §10 | voir §10 |

### 1.2 Ordre des PR

1. **Lot 17** (bug de production, en premier).
2. Lot 11, puis 12, 13, 14, 15.
3. Lot 16.
4. Lot 18 : une PR téléphone (clair et sombre), puis une PR ordinateur.

Le lot 18 change des règles utilisées par les lots 11 à 16 (couleur des boutons secondaires, flèches, statut). **Code les lots 11 à 16 directement avec les règles finales du §2**, pour ne pas refaire le travail deux fois.

---

## 2. Règles transverses finales

Ces règles s'appliquent partout où ce document ne dit pas autre chose. Ajoute-les à `docs/regles-ui-ergonomie.md` (section « Décisions du 8 novembre 2026 ») et à `docs/143`.

### 2.1 Blocs et lignes (D28, D29) : remplacent D22 « carte = cliquable »

- **D28. Un bloc est une section, jamais cliquable en entier.**
  - Une page de lecture est une pile de blocs `var(--surface)`, **sans bordure ni ombre**, rayon `--radius-card`.
  - Fond de page : rôle `--page-blocks` (§2.6).
  - Écart entre deux blocs : 8 px sur téléphone, 16 px sur ordinateur.
  - Marge intérieure : 22 px en haut et en bas, 20 px sur les côtés (téléphone) ; 24 px (ordinateur).
  - Sur-titre de bloc (« Candidature », « Mon parcours ») : 13 px, 700, capitales, `letter-spacing: .06em`, `var(--text-secondary)`, 8 à 10 px dessous.
  - Titre de bloc : 18 px, 700, line-height 24 px. Phrase d'aide : 14 px, line-height 21 px, `var(--text-secondary)`, 6 px sous le titre.
- **D29. Une ligne à flèche est cliquable en entier.**
  - Fond : rôle `--row-blocks` (§2.6), rayon `--radius-sm` (12 px dans la maquette, traduit par D7).
  - `min-height: 72px` (56 px s'il n'y a qu'une ligne de texte), `padding: 14px 12px 14px 16px`, 10 px entre deux lignes.
  - Texte : titre 16 px, 700, line-height 22 px ; lignes secondaires 14 px, line-height 20 px, `var(--text-secondary)`, **4 px entre chaque ligne**, coupées avec « … » si trop longues.
  - À droite, **un cercle à contour** de 40 px : sans remplissage, `border: 2px solid var(--primary-graphic)`, `box-sizing: border-box`, flèche → de 18 px en `var(--primary-text)`. 36 px dans les lignes de réglages sur ordinateur.
  - Toute la ligne est le lien (un seul arrêt de tabulation) ; le cercle est décoratif (`aria-hidden="true"`).

### 2.2 Hiérarchie des actions (D30, D34)

Tout ce qui est cliquable est en bleu. Le reste (fonds, blocs, étiquettes, textes secondaires) reste léger. L'intensité du bleu suit l'importance (NN/g, hiérarchie visuelle ; Material 3, bouton plein puis à contour) :

| Niveau | Quand | Style |
|---|---|---|
| 1. Plein | **Une seule action principale par écran** (« Préparer ma candidature », « Marquer comme déclarée », « Enregistrer », « Se connecter », « Voir ma feuille », « Ajouter le rendez-vous »…), plus le bouton Envoyer du Composer et le bouton central de la barre du bas | fond `var(--action)`, texte ou icône `var(--on-action)` |
| 2. Contour | Actions secondaires (« Ignorer », « Écarter », « J'ai déjà postulé », « Exporter le formulaire (PDF) », « Ouvrir Job-Room », « Changer d'image », « Modifier », « Voir », « Remplacer », « + Ajouter une recherche », « Rédiger un message », « Rédiger la nouvelle version »…) et boutons copier | fond `var(--surface)`, `border: 1.5px solid var(--primary-graphic)`, texte `var(--primary-text)` |
| 3. Cercle | Flèche des lignes D29, flèche de l'action des tâches d'Aujourd'hui | cercle à contour de 2 px (§2.1) |
| Texte | Liens dans une phrase ou sous un bloc (« Le détail de la note › », « Voir l'annonce complète ») | `var(--primary-text)`, 15 px, 700 |

- Contrôle par écran : **au plus un bouton plein visible**, en plus du bouton central de la barre du bas et du bouton Envoyer. S'il y en a deux, le second passe au niveau 2.
- **Plus aucun contour gris** (`#C9C5BA`) sur un bouton.
- Les icônes et mots de statut gardent leur couleur de ton (`--success`, `--warning`, `--peach-text`) et ne sont jamais cliquables seuls.
- L'orange n'est **jamais** une couleur d'action : il signifie retard, à faire ou à joindre (D5).

### 2.3 Statut d'un élément (D31)

- Le statut est **un mot coloré juste après le titre**, sur la même ligne, 8 px après : « justificatif joint » (`var(--success)`), « justificatif à joindre », « infos à compléter » (`var(--warning)`). 14 px, 700.
- Plus de pastille de statut à droite dans une liste sur téléphone.
- Sur ordinateur, dans les listes à traits (Bilan, Recherches du mois), le statut reste à droite en texte coloré, suivi du cercle D29.

### 2.4 Champs à recopier (D32)

- Libellé (13 px, `var(--text-secondary)`) **au-dessus** de la valeur (16 px, 700, line-height 22 px), 4 px entre les deux ; 14 px au-dessus et en dessous de chaque champ ; trait `var(--line-soft)` entre les champs.
- À droite, bouton **copier** de 44 px (niveau 2 : contour bleu, icône bleue), nom accessible « Copier <libellé> ». Au clic, la valeur va dans le presse-papiers et une annonce `aria-live` dit « Copié ».
- Une case à cocher sur un site externe s'indique par une étiquette grise « ☐ case à cocher dans Job-Room » (12 px, 700, fond `var(--surface-muted)`), **jamais par un lien bleu**.
- Une valeur absente s'écrit « Non renseigné » (400, `var(--text-secondary)`), jamais un tiret long.

### 2.5 Mode sombre

En sombre, ce qui est devant est plus clair : l'ordre des fonds s'inverse.

| Élément | Clair | Sombre |
|---|---|---|
| Fond de page des écrans en blocs | `--surface-muted` (#ECE9E1) | `--bg` (#171411) |
| Blocs | `--surface` (#FFFFFF) | `--surface` (#221E1A) |
| Lignes D29, étiquettes | `--bg` (#F7F5F0) | `--surface-muted` (#2C2722) |
| Bouton plein (niveau 1) | `--action` #2445C2, texte blanc | `--action` #7D95FF, texte #171411 |
| Contours, cercles, icônes d'action | `--primary-graphic` #2445C2 | `--primary-graphic` #7D95FF |
| Textes de lien, flèches | `--primary-text` #1A3496 | `--primary-text` #AEBDFF |
| Cercle liquide ORP | fond `--surface-muted`, vague `--water` | fond `--surface-muted`, vague `--water` sombre |

- Ne passent **pas** au bleu clair (pas interactifs) : logos d'entreprise en tuile, points « non lu », barres de progression, miniatures de modèles, pastilles de compte, bulle des messages de l'utilisateur. Ils gardent `var(--primary)`.
- Contrastes : `--on-action` sur `--action` environ 6,7:1 (WCAG 1.4.3) ; contours et flèches bleus à plus de 3:1 sur les fonds sombres (WCAG 1.4.11).

### 2.6 Jetons à ajouter

Dans `docs/mobile/tokens.css` **et** `style.css` (clair, `prefers-color-scheme: dark`, `[data-theme="dark"]`). `tokens.test.ts` doit passer.

| Jeton | Clair | Sombre | Usage |
|---|---|---|---|
| `--action` | #2445C2 | #7D95FF | fond des éléments pleins (niveau 1) |
| `--on-action` | #FFFFFF | #171411 | texte et icône sur `--action` |
| `--page-blocks` | `var(--surface-muted)` | `var(--bg)` | fond de page des écrans en blocs |
| `--row-blocks` | `var(--bg)` | `var(--surface-muted)` | fond des lignes D29 |

Rappel des jetons déjà ajoutés au lot 1 : `--line-strong`, `--field-border`, `--text-disabled`, `--shadow-panel`, `--shadow-menu`, `--shadow-band-card`, `--shadow-composer`.

### 2.7 Gabarit « deux colonnes » (détails sur ordinateur)

Utilisé par les lots 12, 13.1 et 14. Crée **un seul composant** `DetailTwoColumns.vue` (slots `main` et `aside`, prop `asideLabel`).

- Au-dessus des colonnes, sur toute la largeur : en-tête du détail (logo ou CalendarDate, H2 24 px 800 `var(--text)`, sous-titre 15 px `var(--text-secondary)`, menu « … »), étiquettes, boutons d'action.
- Trait `1px solid var(--line-soft)`, puis la grille `display: grid; grid-template-columns: minmax(0, 1fr) 240px; column-gap: 48px` (lot 14 : `minmax(0, 560px) 240px` et `justify-content: space-between`).
- Colonne principale : sections `padding: 32px 0 36px`, séparées par un trait `var(--line-soft)`, sans trait pour la première.
- Colonne d'appui : `<aside aria-label="…">`, `padding-left: 40px`, `border-left: 1px solid var(--line-soft)`.
- Titres de section 18 px 700, 16 px dessous ; sur-titres comme au D28.
- Listes « clé : valeur » de la colonne d'appui : `<dl>`, lignes `padding: 12px 0`, trait entre les lignes, `<dt>` 14 px `var(--text-secondary)` au-dessus de `<dd>` 16 px 700 ; valeur absente « Non précisé ».
- Liens de la colonne d'appui : 44 px de haut, `var(--primary-text)`, icône de lien externe 15 px s'ils sortent de jobA1.
- Ordre du DOM : colonne principale puis colonne d'appui (WCAG 1.3.2). Pas d'`order` CSS.
- Formulaires : toujours une seule colonne de champs.
- Le panneau de détail reste **une seule carte** : pas de blocs D28 à l'intérieur. Les boutons y suivent le §2.2.
- Sur téléphone, le gabarit ne s'applique pas : une seule colonne.

### 2.8 Écrans étroits (320, 360, 390 px)

Les maquettes téléphone sont dessinées dans un cadre fixe de 390 px : elles ne montrent **pas** le rendu à 320 et 360 px. Le contrôle CI « Téléphone (320, 360, 390 px) » (`overflow.test.ts`) fait foi.

- Aucun élément ne dépasse la largeur de l'écran à 320 px (WCAG 1.4.10, redistribution).
- Dans une ligne en `flex` ou en `grid`, la partie texte a `min-width: 0` et se coupe avec « … » ; les boutons et les étiquettes gardent leur taille (`flex: none`).
- Une colonne de liste a `max-width: 100%` et `box-sizing: border-box` : jamais de largeur fixe, ni de largeur égale à 100 % plus une marge.
- Un en-tête de liste avec un bouton (« Recherches suivies » + « + Ajouter ») passe le bouton sous le titre si la place manque (`flex-wrap: wrap`).
- Chaque PR qui touche un écran téléphone passe ce contrôle **avant** qu'une autre PR soit empilée dessus.

---

## 3. Lot 17 : bug de la zone de saisie (urgent)

Constaté en production le 8 novembre (Assistant, téléphone, sombre) : dans la pilule grise, on voit un **deuxième champ** arrondi, avec son propre fond, son contour et l'anneau bleu, décalé vers la gauche. Le bouton + et le micro manquent.

- **Cause probable** : la règle de base des champs (lot 11.1) s'applique aussi au `textarea` du Composer, par un sélecteur général.
- **Où** : `Composer.vue`, règle de base des champs dans `style.css`.
- **Quoi** :
  1. Exclus le Composer de la règle de base, par exemple avec `:where(.composer) textarea, :where(.composer) input { … }`. Dans le Composer, le champ a : `border: 0; background: transparent; border-radius: 0; padding: 0 4px; min-height: 24px; height: auto; outline: none`. La hauteur est gérée par `useAutoGrow`, 6 lignes maximum.
  2. Focus sur la **pilule entière** : `.composer:focus-within { outline: 2px solid var(--primary-graphic); outline-offset: 1px; }`. Aucun anneau sur le champ intérieur. Contraste de l'anneau d'au moins 3:1 (WCAG 2.4.7, 1.4.11).
  3. Remets le bouton + (« Joindre un fichier », 44 px, à gauche) et le micro (« Dicter », 44 px, avant Envoyer), comme dans `captures/Assistant.png` et `captures/etats/AssistantOrdinateur--plus.png`. Règles de données : §6 de `PROMPT_CLAUDE_CODE.md`.
  4. Bouton Envoyer : niveau 1 (`--action`, flèche `--on-action`), désactivé si le champ est vide et qu'il n'y a aucune pièce jointe.
  5. Même règle de focus pour les autres champs en pilule : la **bulle de recherche** de l'en-tête et le filtre **« Filtrer par titre ou entreprise »**.
- **À vérifier dans les quatre Composer** : Assistant (téléphone et ordinateur), Préparer (retouche de la lettre), Ajouter une offre, Coller le texte de l'annonce.
- **Fini quand** : au toucher ou au clic, une seule forme est visible, la pilule, avec un seul anneau qui suit son arrondi, en clair et en sombre.

---

## 4. Lot 11 : corrections

### 11.1 Champs de formulaire (téléphone et ordinateur)

- **Où** : règle de base des champs dans `frontend/src/style.css` (vers la ligne 563 au commit `271fae29`).
- **Quoi** :

  | Propriété | Valeur |
  |---|---|
  | `height` (input, select) | 48 px |
  | `border` | `1.5px solid var(--text-secondary)` |
  | `background` | `var(--surface)` |
  | `border-radius` | `var(--radius-sm)` (8 px) |
  | `padding` | `0 14px` (textarea : `12px 14px`) |
  | `font-size` | 16 px |
  | focus | anneau existant, inchangé |

- Vaut pour tous les formulaires, y compris ceux qui ne sont pas dessinés (Coordonnées, Réglages, Pour les formulaires de candidature).
- **Exclus** : le Composer et les champs en pilule (lot 17).
- Écart connu : « Champs : 12 px dans l'ancienne maquette, 8 px (D7). »

### 11.2 En-tête ordinateur

- **Où** : `AppHeader.vue`, `NotificationBell.vue`, `GlobalSearch.vue`, `AccountMenu.vue`.
- **Quoi** :
  - recherche, cloche et avatar dans un seul conteneur `display: flex; align-items: center; gap: 16px` ; les 32 px restent entre logo, menu principal et ce groupe ;
  - les trois font **44 x 44 px** ;
  - cloche **sans** notification : rond 44 px, fond `var(--surface)`, `border: 1.5px solid var(--line-strong)`, icône 20 px `var(--text)`, nom accessible « Notifications, aucune nouvelle » ;
  - cloche **avec** notifications : capsule `var(--peach-soft)`, texte `var(--peach-text)`, 44 px de haut, `padding: 0 14px`, icône 18 px + compte (« 9+ » au-delà de 9), nom accessible « Notifications, n nouvelles » ;
  - avatar 44 px, `--radius-pill`.

### 11.3 Assistant qui écrit (téléphone et ordinateur)

- **Où** : `AssistantPanel.vue` et le composant de message.
- **Quoi** :
  - à l'envoi, ajoute le message de l'utilisateur, **mais aucune bulle de réponse** tant qu'aucun texte n'est arrivé ;
  - à la place : le logo de l'Assistant **sans cercle** (28 px), puis une bulle de 46 px de haut (48 px sur téléphone) avec 3 points de 8 px `var(--text-secondary)` espacés de 6 px ;
  - forme de la bulle : celle d'une réponse (ordinateur : fond `var(--surface-muted)`, rayons 18 18 18 4 traduits en `--radius-card` et `--radius-sm` ; téléphone : fond `var(--surface)`, bordure `var(--line)`) ;
  - animation `ja-dot` : 1,2 s, `ease-in-out`, infinie, décalages 0, 0,15 et 0,3 s, opacité de .25 à 1 et `translateY(-3px)` (keyframes dans `maquettes/AssistantOrdinateur.dc.html`) ;
  - `role="status"`, `aria-live="polite"`, texte masqué « L'Assistant écrit… » ;
  - au premier morceau de texte, la bulle de réponse remplace la ligne d'attente ; supprime l'élément « … » sous la liste ;
  - `prefers-reduced-motion: reduce` : points fixes, opacité .6 ;
  - la carte d'étapes « Je rédige ta lettre… » (`AiWriting`) reste réservée aux tâches longues.

### 11.4 Mes alertes e-mail

- **Où** : `AlertsView.vue`, `AlertsPanel.vue`, `AlertSearchCard.vue`, et le code qui retient la dernière page de Candidatures.
- **Quoi** :
  1. `/candidatures/alertes` n'est plus retenue comme dernière page de Candidatures.
  2. Ordinateur : lien « ‹ Candidatures » au-dessus du H1 (44 px, 15 px, 600, `var(--primary-text)`), qui ramène à la liste avec l'onglet qui était ouvert.
  3. Liste des recherches suivies sans cadre : trait `var(--line-soft)` en haut, en bas et entre les lignes.
  4. « Créer l'alerte » devient un libellé `var(--primary-text)`, 15 px, 700, suivi de « › », cible de 44 px.
  5. « + Ajouter une recherche » : niveau 2 (contour bleu).
  6. À 320 px, la liste, les « ⋯ » et « + Ajouter » restent dans l'écran (§2.8).

### 11.5 Nouveau rendez-vous sur ordinateur

- **Où** : `RendezVousDesktop.vue`, `OrpMeetingForm.vue`.
- **Quoi** : « Ajouter » (à côté de « Aucun rendez-vous à venir ») ouvre le formulaire **dans le panneau de détail**, avec `ja-slide-l`.
  - Pas de carte autour du formulaire (ni fond, ni bordure, ni rayon propres).
  - Contenu : titre « Prochain rendez-vous ORP » (26 px, 800), « jobA1 prépare ta feuille la veille et te le rappelle le matin. », DateTimeField (« Date », « Heure »), « Lieu ou lien (facultatif) », « Ajouter le rendez-vous » (niveau 1, 52 px) et « Annuler » (lien).
  - `max-width: 560px`. Le bouton « Ajouter » porte `aria-expanded`.
  - Sur téléphone, la carte du formulaire reste.

---

## 5. Lot 12 : Envoyées, détail en deux colonnes (ordinateur)

- **Où** : composant du détail d'une candidature envoyée (celui qui affiche Statut, Documents, Contacts, Premier message, Prises de contact). Gabarit du §2.7.
- **En-tête** : H2 24 px, 800, `var(--text)` (aujourd'hui gris et fin en production : à corriger), entreprise et lieu, étiquettes, menu « … ».
- **Colonne principale** :
  1. **Statut** : liste déroulante de 200 px, puis « Sans réponse depuis n jours. » en `var(--peach-text)` suivi de « Relancer › », puis « Relance à faire · Changer ».
  2. **Premier message** (sur-titre) : « Écrire à » puis « Canal », l'un sous l'autre en pleine largeur, 20 px entre les deux, 8 px entre libellé et champ ; puis « Rédiger un message » (niveau 2, 48 px, `--radius-pill`, icône crayon, 24 px au-dessus). Il n'y a **pas** de zone de texte : le bouton ouvre la rédaction existante.
  3. **Prises de contact** (sur-titre) : « Aucun contact pour l'instant. », puis « J'ai contacté quelqu'un › ».
  4. Lien « Pour l'ORP › » vers la fiche du §10.3, si la candidature n'est pas encore déclarée.
- **Colonne d'appui** (`aria-label="Documents et contacts"`) :
  1. **Documents** : « Lettre (Word) » avec l'icône de téléchargement.
  2. **Contacts** : sur-titre « Trouver quelqu'un », puis Recrutement, L'équipe du poste (sans l'intitulé entre parenthèses), Anciens de 42 Lausanne, chacun avec l'icône de lien externe.
- Tous les boutons du détail ont des bords ronds (`--radius-pill`) : plus de bouton rectangulaire à 8 px.
- Téléphone : inchangé (une colonne, dans l'ordre Statut, Documents, Contacts, Premier message, Prises de contact).

---

## 6. Lot 13

### 13.1 À traiter, détail en deux colonnes (ordinateur)

- **Où** : `OfferDetail.vue`, `OfferTextNotice.vue`. Gabarit du §2.7.
- **Au-dessus des colonnes** : logo, H2, entreprise et lieu, menu « … », étiquettes, puis « Préparer ma candidature » (niveau 1), « Écarter » et « J'ai déjà postulé » (niveau 2).
- **Colonne principale** :
  1. **La note** :
     - anneau (chiffre au centre, D12), verdict, étiquette « Provisoire » si besoin, explication ;
     - critères en ligne (coche + mot), `flex-wrap: wrap; gap: 12px 24px` ;
     - si l'annonce manque : bloc `var(--peach-soft)`, bordure `1px solid var(--peach)`, `--radius-card`, `padding: 18px 20px`, texte au-dessus, boutons dessous (« Lire l'annonce » et « Coller le texte », niveau 2, 44 px) ;
     - « Le détail de la note › », 16 px au-dessus.
  2. **Le poste** : titre, puis le texte (15 px, line-height 23 px, `var(--text-tertiary)`), lignes de 80 caractères au plus (WCAG 1.4.8).
- **Colonne d'appui** (`aria-label="L'offre en bref"`) : titre « L'offre en bref », `<dl>` Lieu, Contrat, Taux d'activité, Reçue, puis « Voir l'annonce sur le site » (icône externe).

### 13.2 « Ce que je cherche » (Profil et Premiers pas, ordinateur)

- Libellé (14 px, `var(--text-secondary)`) au-dessus de la valeur (16 px, 700), à gauche, 2 px entre eux ; lignes de 68 px ; cercle D29 de 36 px à droite (au lieu du chevron gris). La valeur n'est plus collée au bord droit (Laws of UX, proximité).
- Téléphone : inchangé.

---

## 7. Lot 14 : rendez-vous ORP (ordinateur)

1. **Pastilles « Noté » et « Pas encore noté » supprimées**, dans la liste et le détail, sur ordinateur **et** sur téléphone. Les groupes « À noter » et « Passés » (`<h3>`) donnent l'information. Garde le nom accessible du groupe.
2. **En-tête du détail** : CalendarDate 56 px, H2, « Vendredi 30 octobre, 11 h · EPFL », menu « … ». Aucune ligne vide sous l'en-tête.
3. **Grille** : §2.7, en `minmax(0, 560px) 240px`.
4. **Colonne principale** : un `<form>` avec le sur-titre « Ce qui a été convenu », puis trois `<fieldset>` (`padding: 28px 0 32px`, trait au-dessus sauf le premier), chacun avec un `<legend>` (18 px, 700), une phrase d'aide (14 px, `var(--text-secondary)`, 4 px au-dessus, 16 px dessous) et le contrôle :

   | Legend | Phrase d'aide | Contrôle |
   |---|---|---|
   | Objectif de recherches | Le nombre de recherches que l'ORP te demande chaque mois. | compteur − n + (44 px) et « Comme le mois dernier » |
   | Mesures décidées (facultatif) | Un cours, un stage ou un programme proposé par ta conseillère. | champ texte (11.1) |
   | Prochain rendez-vous (facultatif) | jobA1 prépare ta feuille la veille et te le rappelle le matin. | DateTimeField (« Date », « Heure ») |

   « (facultatif) » : 15 px, 400, `var(--text-secondary)`. En bas, après un trait, « Enregistrer » (niveau 1, 52 px).
5. **Colonne d'appui** (`aria-label="Le rendez-vous"`) : titre « Le rendez-vous », `<dl>` Date, Heure, Lieu, Objectif jusqu'ici.
6. **Date dans la pilule** : format court « Mar. 10 nov. 2026 » dès que la pilule fait moins de 280 px, `white-space: nowrap`. Format long dans le sélecteur et dans « Le rendez-vous ». Utilise `dates.ts`.
7. Le sélecteur de date remplace tout le contenu sous l'en-tête, comme avant.
8. Sur téléphone : seulement le point 1.

---

## 8. Lot 15

### 15.1 Préparer (ordinateur)

**Décision** : la disposition de la production est gardée (lettre à gauche, colonne d'aide à droite). La maquette `PreparerOrdinateur` a été refaite dans ce sens et remplace l'ancienne.

- **Où** : `PreparationView.vue`.
- **En-tête** : une ligne de 64 px, `align-items: center`, 20 px entre les blocs :
  1. « ‹ Retour à l'offre » (44 px, 15 px, 700, `var(--primary-text)`), centré verticalement ;
  2. trait vertical 1 x 32 px `var(--line)` ;
  3. logo 44 px ;
  4. **H1 = intitulé du poste** (24 px, 800), entreprise et lieu dessous (15 px) ;
  5. anneau de 48 px (piste `var(--line)`, arc de la couleur du verdict, trait 4 px), chiffre au centre (D12), verdict à droite en couleur (D5 : Proche `--success`, À creuser `--score-dig`, Loin `--neutral`) avec « de ton profil » dessous ;
  6. étapes « 1. Lettre », « 2. CV », « 3. Postuler ».
  - « Ma candidature » disparaît de l'écran ; il reste dans le `<title>` : « Ma candidature, <poste>, jobA1 ».
- **Grille** : `minmax(0, 1fr) 360px`, `gap: 24px`. La colonne de droite défile seule.
- **Colonne de gauche** : carte « Lettre de motivation » (18 px, 700) avec le SegmentedControl FR, DE, EN à droite, puis l'aperçu sur `var(--surface-muted)`. « Consigne : Plus court » disparaît. À l'étape CV, même carte avec le CV.
- **Colonne de droite**, trois cartes (`padding: 20px 24px`, 16 px entre elles) :
  1. **Mise en page** : « Le modèle s'applique à la lettre et au CV. », pastilles Sobre, Moderne, Bandeau, Classique (40 px, `aria-pressed`, sélection `var(--primary-soft)` + bordure `var(--primary-graphic)`), trait, « Tient sur une page A4 · n mots ». Visible aux étapes Lettre et CV. Réutilise les modèles du téléphone (nom interne « serif », affiché « Classique » partout).
  2. **Pour cette offre** : « n points forts · n à vérifier » ; plus de verdict ni d'onglet « À creuser » ; groupes « Points forts (n) » (coche `--success`) et « À vérifier (n) » (point d'attention `--peach-text`) ; chaque élément : sujet en gras 15 px (partie avant les deux-points des données), détail 14 px `var(--text-tertiary)`, `padding: 10px 0` ; la couleur n'est jamais le seul repère (WCAG 1.4.1) ; plus de « Afficher moins ».
  3. **Nouvelle version** : « Repartir de zéro avec l'annonce et ton CV. », « Rédiger la nouvelle version » (niveau 2, 48 px), lien « Ce qui part à l'IA › ».
- **Bas de page** : grille `minmax(0, 1fr) 360px`. À gauche, suggestions (Plus court, Plus formel, Insister sur <compétence>, En allemand) puis Composer ; à droite « J'ai relu la lettre » (niveau 1, 52 px). « Insister sur <compétence> » vient d'une compétence du profil présente dans l'annonce ; sans cette donnée, n'affiche que les trois autres.

### 15.2 « J'ai déjà postulé » (téléphone et ordinateur)

- Ordinateur : bouton niveau 2 à droite de « Écarter ». Téléphone : dans le menu « … » du détail d'une offre.
- Au clic : parcours existant « Marquer comme envoyée » (écran `ApplicationSent`, puis l'offre passe dans Envoyées avec la date du jour, modifiable).

---

## 9. Lot 16 : retours sur le téléphone

### 16.1 Pastilles de suggestion de l'Assistant (téléphone et ordinateur)

- `min-height: 48px`, `padding: 10px 20px`, `border-radius: 24px` (`--radius-pill`), texte aligné à gauche, `line-height: 21px`, niveau 2 (contour bleu). Le texte n'est plus collé à la bordure.
- Nom d'entreprise raccourci : s'il contient « - », la partie après (« … - ICRC » donne « ICRC ») ; sinon coupe à 24 caractères avec « … ». Le libellé tient sur une ligne ; le nom complet reste dans `aria-label`.

### 16.2 Personnage : pantalon

- Les 12 poses du zip (`illustrations/personnage/perso-*-400.webp` et `-800.webp`) ont un pantalon bleu foncé (#2B3A8F) au lieu du short.
- Remplace les fichiers de `frontend/public/personnage/`, mêmes noms. Aucun changement de code. Vide le cache des images si le service worker les garde.
- #2B3A8F appartient à l'illustration : ce n'est pas un jeton.

### 16.3 Buste du personnage dans les écrans chargés (téléphone)

Quand le personnage partage l'écran avec un formulaire, on ne garde que le haut du corps, avec un fondu en bas. Il « sort » de la colline du décor.

| Écran (téléphone) | Pose | Fichier | Taille affichée |
|---|---|---|---|
| Rendez-vous vide | 01 debout | `perso-01-buste-400.webp` | 72 px de large, `align-self: flex-end` |
| Connexion (clair et sombre) | 02 bonjour | `perso-02-bonjour-buste-400.webp` | 118 px de haut (au lieu de 140) |
| Premiers pas, étape « Ton CV » | 03 cv | `perso-03-cv-buste-400.webp` | 100 px (au lieu de 122) |
| Premiers pas, dernière étape | 07 révélation | `perso-07-revelation-buste-400.webp` | 150 px (au lieu de 186) |

- Le bas du buste est posé sur la ligne de sol du décor, à la même position que le personnage en pied.
- Restent en pied : pages d'état plein écran (Page introuvable, Maintenance, Pas de connexion, Candidature envoyée, Objectif atteint, Aucune offre) et toutes les pages ordinateur.
- Ajoute ces quatre lignes à la liste fermée de docs/141 §3. `personnage.test.ts` doit en tenir compte.

### 16.4 Justificatifs ORP (téléphone et ordinateur)

| Avant | Après |
|---|---|
| Preuve | justificatif joint |
| À joindre | justificatif à joindre |
| Voir tout le mois et les preuves | Voir tout le mois et les justificatifs |
| Les preuves d'octobre sont en retard | Les justificatifs d'octobre sont en retard |
| Électronique (canal) | En ligne |

- Sous le titre de la liste : « L'ORP peut demander un justificatif pour chaque recherche : l'e-mail de confirmation ou une capture. »
- Placement du statut : §2.3. Structure de l'écran : §10.2.

---

## 10. Lot 18 : style « blocs » (à la manière des CFF)

Référence visuelle : le détail d'un trajet sur sbb.ch. Règles : §2.1 à §2.6.

### 10.1 Téléphone, Détail d'une offre

- **Maquettes** : `Offre`, `OffreSombre`. **Captures** : `Offre.png`, `etats/Offre--bas.png`, `OffreSombre.png`, `etats/OffreSombre--bas.png`.
- **Où** : `OfferDetail.vue` (téléphone).
- **Contenu, dans l'ordre** :
  1. En-tête (fond `var(--page-blocks)`) : retour, garder, « … » (icônes `var(--primary-text)`, 44 px).
  2. Bloc : logo 52 px, intitulé (22 px, 800), entreprise · lieu ; étiquettes grises (taux, contrat, télétravail, publiée), 14 px au-dessus.
  3. Bloc : anneau de la note 56 px (chiffre au centre), verdict en couleur (18 px, 700), « Selon ton profil et tes préférences » ; raisons (coche ou point d'attention, 15 px, `padding: 8px 0`) ; lien « Le détail de la note › ».
  4. Bloc : « Le poste », résumé (15 px, line-height 23 px), lien « Voir l'annonce complète » (icône externe).
  5. Barre du bas fixe (fond `var(--bg)`, trait en haut) : « Ignorer » (niveau 2) et « Préparer ma candidature » (niveau 1, toute la largeur restante). « J'ai déjà postulé » est dans le menu « … ».

### 10.2 Téléphone, Suivi ORP et onglet ORP de Bilan

- **Maquettes** : `Orp`, `OrpSombre`, onglet ORP de `Explorer` et `ProgresserSombre`. **Captures** : `Orp.png`, `etats/Orp--bas.png`, `OrpSombre.png`, `etats/OrpSombre--bas.png`, `Explorer.png`, `ProgresserSombre.png`.
- **Où** : `BilanOrpView.vue` (téléphone) et l'onglet ORP de Bilan.
- **Contenu** :
  1. Bloc : **cercle liquide** de 96 px (vague `var(--water)`, contour `var(--primary-graphic)`, « 8/10 » au centre avec un contour de texte de la couleur du bloc), sur-titre du mois, « n recherches à faire », « Objectif fixé par ta conseillère. À remettre avant le 5 <mois suivant>. ».
  2. Bloc « À déclarer à l'ORP · n » : « Envoyées, pas encore sur ta feuille de recherches. », puis une ligne D29 par candidature : entreprise (+ « infos à compléter » si besoin, D31), « poste · En ligne », « Envoyée le … ». La ligne ouvre la fiche « Pour l'ORP » (§10.3). Plus de 3 éléments : « Afficher les n autres » sous la liste.
  3. Bloc « Recherches du mois · n » : phrase sur le justificatif (16.4), une ligne D29 par recherche : entreprise + statut D31, « date · poste » ; puis « Exporter le formulaire (PDF) » (niveau 2).
- La date limite vient d'une constante `ORP_DEADLINE_DAY = 5`, pas d'un texte en dur. **Kevin doit la confirmer** avec le texte officiel avant la mise en production : note-le dans « Questions pour Kevin ».
- Dans l'onglet ORP de Bilan, les mêmes blocs s'affichent sous les onglets ORP, Bilan, Formations. Les onglets Bilan et Formations ne changent pas.
- Barre du bas : le libellé reste « Bilan » (D21), même si les maquettes affichent « Progresser ».

### 10.3 Téléphone, Pour l'ORP (une candidature), écran nouveau

- **Maquettes** : `OrpFiche`, `OrpFicheSombre`. **Captures** : `OrpFiche.png`, `etats/OrpFiche--bas.png`, `OrpFicheSombre.png`, `etats/OrpFicheSombre--bas.png`.
- **Ouvert depuis** : une ligne « À déclarer » de Suivi ORP, ou le lien « Pour l'ORP › » du détail d'une candidature envoyée. Sur ordinateur : panneau latéral de 480 px (`SidePanel`) avec le même contenu.
- **Remplace** l'ancienne section « Pour l'ORP » de la production (libellé à gauche et valeur à droite, « à cocher : » en bleu, tiret long pour une valeur absente).
- **Contenu** :
  1. En-tête : retour, « Pour l'ORP ».
  2. Bloc : sur-titre « Candidature », entreprise (18 px, 700), poste, « Envoyée le … · sans réponse depuis n jours ».
  3. Bloc : « Déclarer dans Job-Room », « Recopie ces infos dans ton formulaire de recherches. Le bouton copie copie la valeur. », « Ouvrir Job-Room » (niveau 2, icône externe, nouvel onglet).
  4. Bloc, sur-titre « La recherche » : Date, Mode (case à cocher), Poste (D32).
  5. Bloc, sur-titre « L'entreprise » : Nom, Rue et n°, NPA et lieu, Pays (case à cocher), Case postale · Personne contactée (« Non renseigné » si vide).
  6. Barre du bas fixe : « Marquer comme déclarée » (niveau 1), puis « Elle passe dans « Recherches du mois ». » (14 px, centré).

### 10.4 Téléphone, Compte

- **Maquettes** : `Compte`, `CompteSombre`. **Captures** : `Compte.png`, `etats/Compte--bas.png`, `CompteSombre.png`, `etats/CompteSombre--bas.png`.
- **Où** : `AccountView.vue`.
- **Contenu** :
  1. Bloc : une ligne D29 avec l'image de profil (52 px), le nom, « CV, compétences, postes recherchés ».
  2. Blocs avec sur-titre, une ligne D29 par élément :
     - « Mon parcours » : Formations ; CV et lettres (« n documents ») ;
     - « Préférences » : Critères de recherche (« Postes, lieux, taux d'activité ») ; Notifications ; Apparence (« Automatique ») ;
     - « Confidentialité et aide » : Mes données ; Charte d'utilisation de l'IA ; Aide et contact.
  3. « Se déconnecter » reste en `--danger`, sous les blocs.

### 10.5 Ordinateur, pages de lecture

| Page | Captures | Où | Changements |
|---|---|---|---|
| Aujourd'hui (travail et repos) | `AujourdhuiOrdinateurTravailD.png`, `AujourdhuiOrdinateurReposD.png` | `TodayView.vue` | Fond `--page-blocks` (la bande `--primary-soft` reste). Cartes de tâche sans bordure. Action de chaque tâche : le mot (« Envoyer », « Trier », « Remettre », « Préparer », « Relancer ») dans la couleur de son ton, puis le cercle D29 de 40 px, 12 px entre les deux. Toute la carte de tâche est le lien. |
| Bilan | `BilanOrdinateur.png`, `etats/BilanOrdinateur--tab-res.png`, `--tab-form.png` | `BilanView.vue`, `components/bilan/*` | Fond, blocs sans bordure, cercles D29 de 36 px au lieu des chevrons gris, boutons secondaires niveau 2. |
| Profil | `ProfilOrdinateur.png`, `etats/ProfilOrdinateur--pick.png` | `ProfileView.vue` | Idem ; « Changer d'image », « Modifier », « Voir », « Remplacer » en niveau 2. |
| Réglages | `ReglagesOrdinateur.png` | `SettingsView.vue` | Idem. Interrupteurs et SegmentedControl inchangés (interrupteur activé : `--action`). |
| Notifications, Alertes | `NotificationsOrdinateur.png`, `AlertesOrdinateur.png` | `NotificationsView.vue`, `AlertsView.vue` | Fond et blocs sans bordure ; « + Ajouter une recherche » niveau 2. |

- **Pages de travail** (Candidatures, Préparer) : le panneau reste une seule carte (§2.7). Seuls le §2.2 (niveaux d'action) et le §2.3 (statut) s'y appliquent. Les listes de la colonne de gauche restent des cartes cliquables, une par offre, avec le style de sélection actuel.
- **En-tête, panneaux latéraux, Assistant** : inchangés.

### 10.6 Écrans sombres

- Dessinés : `OffreSombre`, `OrpSombre`, `OrpFicheSombre`, `CompteSombre`, `ProgresserSombre` (onglet ORP). Les autres écrans sombres suivent le §2.5 sans dessin dédié.
- Sur **tous** les écrans sombres, les éléments pleins interactifs passent à `--action` / `--on-action` (§2.5) : boutons pleins, Envoyer, bouton central de la barre du bas, langue choisie et numéro de l'étape en cours dans Préparer, interrupteurs activés. Voir `AccueilSombre.png`, `PreparerSombre.png`, `RendezVousSombre.png`, `ConnexionSombre.png`.
- La planche système `ModeSombre` n'est pas à jour : ce document prime.

---

## 11. Vérification finale (après le lot 18)

1. Chaque écran du §1.1 et du §10 comparé à sa capture, en haut et en bas de page, en clair et en sombre, à 390 et 1440 px.
2. `grep` dans `frontend/src` :
   - plus de pastille « Noté » / « Pas encore noté » ;
   - plus de « Preuve », « À joindre », « Électronique » affichés ;
   - plus de « Ma candidature » affiché dans Préparer (le `<title>` seul est permis) ;
   - plus de `border-radius: 12px`, plus de bordure de bouton `#C9C5BA`, plus de chevron gris en fin de ligne cliquable ;
   - aucun hexadécimal hors jetons, sauf illustrations et logos de marque.
3. Par écran : au plus un bouton plein visible (hors barre du bas et Envoyer).
4. Clavier : chaque ligne D29 et chaque carte de tâche est un seul arrêt de tabulation ; dans les détails en deux colonnes, la tabulation parcourt la colonne principale puis la colonne d'appui ; focus visible partout ; le Composer montre un seul anneau, sur la pilule.
5. Lecteur d'écran : chaque `<aside>` a son nom ; chaque `<fieldset>` annonce son `<legend>` ; une ligne D29 annonce titre, statut et lignes secondaires une seule fois ; « L'Assistant écrit… » annoncé une fois ; « Copié » annoncé après une copie.
6. Contrastes (WCAG 1.4.3, 1.4.11) : texte bleu sur `--surface` et `--row-blocks` d'au moins 4,5:1 ; contours, cercles et flèches d'au moins 3:1 ; `--on-action` sur `--action` d'au moins 4,5:1, en clair et en sombre.
7. À 320, 360 et 390 px : le contrôle « Téléphone » de la CI passe sans défaut (§2.8). Entre 821 et 1327 px : les grilles ne débordent pas ; les colonnes d'appui gardent leur largeur, la colonne principale rétrécit.
8. `prefers-reduced-motion: reduce` : aucune animation.
9. Tests verts (§0.7 de `PROMPT_CLAUDE_CODE.md`), plus : `DetailTwoColumns.vue` (ordre du DOM, nom de l'aside), ligne d'attente de l'Assistant (aucune bulle vide), Composer (un seul anneau au focus), jetons `--action`, `--on-action`, `--page-blocks`, `--row-blocks`.
