# 139 — La nouvelle identité mobile (et les tokens partagés avec l'ordinateur)

> Statut : **validé** le 2026-11-02, avec les décisions D1 à D10 et les réponses Q2 à Q7 (voir §0 et
> `docs/regles-ui-ergonomie.md`, « Décisions du 2 novembre 2026 »). Les maquettes font foi pour ce chantier
> (exception datée dans `CLAUDE.md`), corrigées par ces décisions.
> Références : `docs/mobile/tokens.css` (source de vérité des valeurs), `docs/mobile/maquettes/` (écrans, dont
> `Systeme.dc.html`, `ModeSombre.dc.html`, `Emoticones.dc.html`, `Animations.dc.html`), `docs/mobile/logo_svg_calques/`.
> Le gel du design jusqu'au test utilisateurs est levé pour ce travail, à ta demande.

## 0. Les décisions du 2 novembre, et comment lire les maquettes

Le détail est dans `docs/regles-ui-ergonomie.md` (fin du document). Là où une décision garde la règle, **la maquette
se lit corrigée** :

- **Onglets** (D1, D2) : 5 sur téléphone, **« Bilan »** à la place de « Progresser » (sous-onglets ORP, Bilan,
  Formations), **« Accueil »** à la place d'« Aujourd'hui » ; l'ordinateur garde ses 3 entrées.
- **Note** (D3) : l'anneau gradué de `Systeme.dc.html` (règle 1) sans le chiffre au centre ; le **mot** en premier
  plan ; **4 mots** et seuils 85 / 70 / 50 au lieu de 3 mots et 80 / 60 ; le chiffre seulement dans la fiche.
- **« À creuser »** (D5) : gris chaud `--score-dig`, partout où la maquette le montre en orange (Candidatures,
  Filtres, Systeme). L'orange reste à « À joindre » et aux relances. `docs/mobile/tokens.css` est corrigé.
- **Sélection** (D4) : rond plein seulement dans la barre du bas ; les segments gardent la pastille teintée.
- **Objectif ORP** (D6) : cercle liquide, « x sur y » toujours écrit.
- **Rayons** (D7) : 8, 18, 34, 999 seulement ; les autres rayons des maquettes (6, 10, 12, 14, 20, 22) se rangent sur
  le plus proche de ces quatre.
- **Seuil** (D8) : 820 px, un seul.
- **Chargement** (D9) : feston seul sur téléphone, visage transformé une fois sur ordinateur.
- **Illustrations** (D10) : visages d'humeur pour les écrans vides, erreurs et chargements ; illustrations pour les
  premiers pas et les grandes réussites.
- **Candidatures** (Q5) : À traiter · Envoyées · Rendez-vous, aussi sur ordinateur (renommage prévu).

## 1. En clair

- La même app Vue, responsive : **sous 820 px**, la nouvelle identité mobile ; au-dessus, l'ordinateur garde sa
  structure mais prend **les mêmes tokens**, en clair comme en sombre (sombre chaud).
- On adapte `tokens.css` au système existant (`frontend/src/style.css`, un seul `:root`) **en gardant ses noms de
  rôles** (`--primary`, `--surface`, `--warning`…). Les anciens noms (`--accent`, `--muted`, `--border`…) deviennent
  des alias vers les nouveaux, puis disparaissent page par page : rien ne casse d'un coup sur ordinateur.
- Petites PR, une par étape, dans ton ordre. Après chaque étape : captures 390 px et 1440 px, clair et sombre.

## 2. Ce que j'ai lu

- 32 maquettes (texte, structure, valeurs) et `canvas.json`. Elles ne s'ouvrent pas seules dans un navigateur
  (`support.js` est le moteur du canevas claude.ai, non fourni). **Le rendu se lit dans `docs/mobile/captures/`**
  (un PNG par écran et par planche, clair et sombre), les valeurs exactes dans le HTML, couleurs et tailles dans
  `tokens.css`.
- Le code : `style.css` (4 254 lignes, 166 `@media`), `router.ts`, `App.vue`, 150 composants, `usePhone.ts`
  (déjà 820 px pour « téléphone », 600 px pour la « structure téléphone »).
- Figma (fichier jobA1) : **aucune page pour la nouvelle identité**. Les pages « Écran · … » et « Planche · … »
  montrent l'identité actuelle (fond blanc, accent `#2340c8`, sombre bleu froid).

## 3. Les tokens

**Où :** dans `frontend/src/style.css`, en tête, à la place du bloc `:root` actuel et de son
`@media (prefers-color-scheme: dark)`. Pas de second fichier de variables : la règle §4 bis dit « toute valeur passe
par une variable de `style.css` », et la CI (`scales.test.ts`, `contrast.test.ts`) lit ce fichier.
`docs/mobile/tokens.css` reste la référence ; un test vérifie que chaque valeur y est identique dans `style.css`.

**Clair** (repris tel quel) : `--bg` `--surface` `--surface-muted` `--line` `--line-soft` · `--text`
`--text-secondary` `--text-tertiary` · `--primary` `--primary-graphic` `--primary-text` `--primary-soft` `--water`
`--on-primary` · `--spark` `--peach` `--peach-soft` `--scribble` · `--success(-soft)` `--warning(-soft)`
`--neutral(-soft)` `--danger` `--danger-line` · `--radius-card` `--radius-block` · `--btn-primary` `--btn-secondary`
`--btn-tertiary` `--btn-compact` `--target-min` · `--title-tab` `--title-sub` `--label-caps` · `--icon-stroke` ·
`--ease-*` `--spring-*` `--t-fast` `--t-standard` `--t-joy` `--t-party` · `--nav-height` `--nav-spacer` `--mood-box`.

**Sombre chaud** : les valeurs de `tokens.css`, sous `prefers-color-scheme: dark` **et** `:root[data-theme="dark"]`
(forcé), avec `:root[data-theme="light"]` qui force le clair.

**Ce qu'on garde du projet** : `--space-*`, `--font-*` (sauf les deux titres ajoutés), `--weight-*`, `--leading-*`,
`--page-*`, `--field-*` (recalculés sur la nouvelle palette, 3:1 vérifié), `--radius-sm`.

**Alias de transition** (supprimés quand plus rien ne les lit) :

| Ancien | Devient | Remarque |
|---|---|---|
| `--accent` | `--primary-text` pour le texte et les liens, `--primary-graphic` pour les traits | aujourd'hui un seul nom pour les deux ; en sombre ils diffèrent |
| `button.primary` (fond `--accent`) | `--primary` + `--on-primary` | en sombre, le bouton reste `#2445C2` texte blanc (aujourd'hui bleu clair, texte foncé) |
| `--accent-soft` | `--primary-soft` | |
| `--muted` | `--text-secondary` | |
| `--border` `--divider` | `--line` `--line-soft` | |
| `--band` `--panel` | `--bg` / `--surface-muted` | le fond devient crème `#F7F5F0`, ordinateur compris (Q6) |
| `--ok-text` `--ok` | `--success` | |
| `--orange-text` `--orange` `--orange-soft` | `--warning` `--warning-soft` | |
| `--down-text` `--down` | `--danger` | |
| `--score-dig` | `--score-dig` | gardé : « À creuser » reste en gris chaud (D5), nouvelle valeur chaude |
| `--mint` `--sky` `--mint-soft` | supprimés | absents de la nouvelle palette |

**Police** : Figtree est déjà là (`@fontsource-variable/figtree`). `Caveat Brush` (trait crayon) est nouvelle :
je propose `@fontsource/caveat-brush`, servie par l'app (pas Google Fonts : nLPD), chargée seulement sur l'onboarding
et l'objectif atteint.

**Apparence** : `data-theme` posé sur `<html>` avant le premier rendu (script court dans `index.html`), choix gardé
dans le navigateur (`localStorage`), « Automatique » par défaut. Réglage dans Compte › Apparence.

## 4. Les composants

| Besoin (maquettes) | Existant | Proposition |
|---|---|---|
| **BottomNav** (5 onglets, rond plein dans un creux, zone vide de 22 px) | `TabBar.vue` (3 onglets, pastille teintée) | reprendre `TabBar` sous le nom `BottomNav` ; le creux en SVG ; `--nav-spacer` réservé sous le contenu |
| **AppHeader** (onglet : logo + 30 px ; sous-page : retour + 22 px ; accueil : logo + cloche) | `PageHero`, `CardHead`, lien « ← » | nouveau `AppHeader` avec 3 variantes, téléphone seulement |
| **Boutons 4 niveaux** | `button`, `.primary`, `.secondary`, `.small`, `.link` | des classes, pas un composant : `.primary` 54, `.secondary` 52, `.tertiary` 48, `.compact` 40, toujours en pilule ; `.link` devient `.tertiary` |
| **ScoreRing** (anneau gradué 25 %, chiffre, mot dessous) | `ScoreRing.vue` (cercle, sans graduation), `ScoreWord.vue` (visage + mot) | faire évoluer `ScoreRing` ; `ScoreWord` reste pour l'ordinateur tant que Q3 n'est pas tranchée |
| **FaceMood** (visage dans sa forme : soleil, arche, feston, carré, triangle ; zone 156 px + texte) | `FaceMark.vue` (visage, humeurs), `FaceState.vue`, `FaceTile.vue` | nouveau `FaceMood` qui pose `FaceMark` dans sa forme ; `FaceState` l'utilise sur téléphone |
| **MoodAnimation** (11 animations d'`Animations.dc.html`) | `FaceTransform.vue` (8 animations en boucle), `FaceMark` (`wink`, `waiting`) | `FaceTransform` joué une fois ; nouveau `MoodAnimation` pour les animations nouvelles |
| **Assistant** (mascotte ronde, eau pendant le travail) | `AssistantMascot.vue`, `AssistantPanel.vue` (panneau latéral) | réutiliser ; l'Assistant devient une page sur téléphone (Q2) |
| **LiquidCircle** (objectif ORP qui se remplit) | `dash/OrpGauge.vue` (jauge), `OrpMonth.vue` | nouveau `LiquidCircle` |
| **BottomSheet** (Filtres, Actions d'une offre, confirmation) | `BottomSheet.vue`, `FormSheet.vue`, `OfferFilterSheet.vue` | réutiliser, nouveau style |
| **Snackbar** (« Annuler ») | `UndoToast.vue`, `AppToast.vue` | réutiliser, au-dessus de la barre du bas |
| **StepTabs** (Lettre, CV, Postuler, avec coche) | `StepProgress.vue` (barre), `SegmentedControl.vue` | nouveau `StepTabs` |
| **SegmentedControl** (Toutes / Non lues, ORP / Bilan / Formations) | `SegmentedControl.vue` | réutiliser |
| **Carte d'offre**, **ligne de réglage**, **groupe en capitales 13 px** | `OfferCard`, `SettingRow`, `GroupedList` | réutiliser, nouveau style |
| **Icônes au trait 2,2 px** | `AppIcon.vue`, `icons.ts` | `stroke-width: var(--icon-stroke)` partout, bouts ronds |

## 5. L'ordre (une PR par ligne)

0. **Cette PR** : les fichiers dans `docs/mobile/` et ce plan. Si tu valides, j'y ajoute la mise à jour de
   `docs/regles-ui-ergonomie.md` et du `CLAUDE.md` (Q1), avant tout code.
1. **Tokens clair et sombre** + alias + test de contraste et de concordance avec `tokens.css` (PR 461). Le choix
   forcé (`data-theme`) passe à l'étape Compte › Apparence.
2. **FaceTransform joué une fois** (WCAG 2.2.2) : fait, PR 460. Le pouls d'attente de FaceMark reste en boucle
   (une vraie attente, D9).
3. **Barre du bas** (`BottomNav`) et `AppHeader`.
4. **Accueil** (`AccueilSmile`), 5. **Candidatures** (+ `Filtres`, `ActionsOffre`, `AucuneOffre`, `ErreurConnexion`),
   6. **Détail d'une offre**, 7. **Ma candidature** (`Preparer`, `StepTabs`), 8. **Progresser** (`Explorer`, `Orp`,
   `LiquidCircle`, `ObjectifAtteint`), 9. **Notifications**, 10. **Compte** (+ `Reglages`, Apparence),
   11. **le reste** : Assistant, Onboarding C.
12. **Animations d'`Animations.dc.html`** (`MoodAnimation`).

Chaque PR : `make audit-telephone` (320/360/390), captures 390 et 1440 en clair et en sombre, un fragment
`changelog.d/`, et la liste « Règles vérifiées » de §10.4.

## 6. Ce qui manque dans les maquettes ou contredit le code et les règles

**Contre `docs/regles-ui-ergonomie.md`** (source n° 1, §0 : « si une contradiction est trouvée, la signaler ») :

1. §2 « Trois entrées, pas une de plus » : les maquettes en ont **cinq** (Accueil, Candidatures, Assistant,
   Progresser, Compte).
2. §5 interdit le mot **« Progresser »** (et l'app l'a remplacé par « Bilan » : `/progresser` redirige vers `/bilan`).
   « Aujourd'hui » devient « Accueil ».
3. §4 « Note d'une offre » : visage + mot, **pas de chiffre sur 100** ; les maquettes montrent un anneau avec le chiffre.
   « À creuser » en **gris chaud, jamais l'orange** ; les maquettes le mettent en orange (`--warning`).
4. §4 « Sélection unique » : pastille teintée, **jamais de pastille pleine** ; l'onglet actif des maquettes est un
   rond bleu plein.
5. §4 « Couleur orange » réservée à « ce qui demande d'agir » ; les maquettes : orange = « à vérifier ».
6. §4 « Progression ORP : 10 cases » ; les maquettes : un cercle liquide.
7. §4 bis : rayons 8 · 12 · 999 ; les maquettes : 18 (carte) et 34 (bloc). Titres 30 px hors de l'échelle
   (26 ou 32).
8. §4 « Structure téléphone (< 600 px) » : « notre identité ne change pas ». La nouvelle identité s'applique sous
   820 px, et change l'identité.
9. §6 : « une animation par page, visage du 1 transformé » ; les maquettes fixent 4 vitesses et 11 animations.

**Contre le code** :

- Les écrans ne recoupent pas les routes : « Candidatures » montre À traiter / Envoyées / Rendez-vous (le code :
  Offres / Suivi / Alertes) ; le suivi ORP est dans Progresser (le code : Candidatures › Suivi) ; « Compte » réunit
  Profil et Réglages ; Notifications est une page (le code : panneau de la cloche) ; l'Assistant est un onglet (le
  code : panneau latéral).
- `Systeme.dc.html` règle 4 dit « accueil : logo seul + grand bonjour », ta demande dit « logo + cloche ». Je suis ta
  demande.

**Absent des maquettes** : Alertes, Relances, Tri du jour, Rendez-vous ORP, Profil (Parcours, Coordonnées),
Formations hors Progresser, Diagnostic, connexion et pages publiques, 404 ; Réglages, Assistant, Filtres et Onboarding
en sombre ; la largeur 600–820 px (tablette) ; l'ordinateur en sombre chaud (seulement « à aligner »). Des textes à
remplacer : « [Préciser ici l'usage réel des données.] », « Commune [nom] », le résumé d'annonce entre crochets.

## 7. Questions

- **Q1. Figma et les règles.** Le `CLAUDE.md` impose de ne coder que ce qui est dans Figma, et
  `regles-ui-ergonomie.md` §10.5 dit qu'une règle change dans ce document d'abord. Rien de la nouvelle identité n'est
  dans Figma. Je propose : `docs/mobile/maquettes/` devient la référence pour ce chantier (exception datée dans
  `CLAUDE.md`, comme celle du 23 octobre), et je mets `regles-ui-ergonomie.md` à jour (points 1 à 9 ci-dessus) dans
  cette PR, avant le code. Ou préfères-tu que les écrans passent d'abord dans Figma ?
- **Q2. Navigation.** Sur ordinateur, la barre du haut garde-t-elle ses 3 entrées (Aujourd'hui, Candidatures, Bilan)
  et ses noms, ou prend-elle les 5 du mobile ? Je propose : l'ordinateur ne change que ses couleurs pour l'instant.
- **Q3. Score.** Le chiffre sur 100 et l'orange pour « À creuser » valent-ils aussi sur ordinateur ? Je propose :
  oui, même composant partout, pour ne pas avoir deux langages.
- **Q4. Où vivent les écrans.** Je propose de garder les adresses actuelles et de changer la présentation sous
  820 px : Accueil = `/aujourdhui`, Progresser = `/bilan` (avec l'onglet ORP), Compte = `/profil` + `/reglages`,
  et deux adresses nouvelles : `/notifications` et `/assistant` (téléphone seulement). D'accord ?
- **Q5. Candidatures.** À traiter / Envoyées / Rendez-vous remplacent-ils Offres / Suivi / Alertes ? Et où vont les
  Alertes (le lien « Alertes » en haut de l'écran) ?
- **Q6. Ordinateur en clair.** Le fond passe-t-il aussi du blanc à la crème `#F7F5F0` ? `tokens.css` le dit
  (« mobile + ordinateur »), je le fais sauf avis contraire.
- **Q7. Apparence.** Le choix gardé dans le navigateur suffit-il, ou doit-il suivre le compte d'un appareil à l'autre
  (il faudrait un champ côté serveur) ?
- **Q8. `support.js`.** As-tu ce fichier, pour que les maquettes s'ouvrent dans un navigateur et que je compare mes
  captures aux leurs ? Sans lui, je compare à la lecture du code des maquettes.
