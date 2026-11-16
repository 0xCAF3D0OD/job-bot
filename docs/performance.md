# Performance : le budget de poids

> Décidé par Kevin le 2026-11-10 (« budget = taille compressée actuelle + 5 % maximum, vérifié en CI à chaque PR »). Ce document remplace la liste des hausses de docs/117 §3, qui reste l'historique.

## Ce qui est mesuré

Après `vite build`, `frontend/scripts/poids.mjs` mesure ce que le navigateur télécharge. Chaque taille est donnée trois fois :

- **brute** : le fichier tel qu'il est sur le disque ;
- **gzip** : ce que le serveur envoie, puisque Caddy compresse en zstd ou gzip (`deploy/*/Caddyfile`, `encode zstd gzip`) ;
- **brotli** : pour comparer. Le serveur ne l'envoie pas aujourd'hui.

La limite porte sur **gzip** pour le JavaScript et le CSS. Pour les **images**, elle porte sur le poids **brut**, parce que le WebP est déjà compressé.

| Mesure | Ce qu'elle compte |
|---|---|
| `js-premier` | ce que charge le premier écran : l'application et Aujourd'hui |
| `js-total`, `css-total` | tout le code, tout le CSS |
| `js-accueil`, `css-accueil` | Aujourd'hui (`TodayView`), donc aussi le CSS du premier écran |
| `js-candidatures`, `css-candidatures` | Candidatures › Offres (`JobsView` + `OffersView`) |
| `js-bilan`, `css-bilan` | Bilan › ORP (`BilanView` + `BilanOrpView`) |
| `js-compte`, `css-compte` | Compte (`AccountView`) |
| `css-<page>` | le CSS de chacune des 30 pages de l'application (`CSS_PAGES` dans `poids.mjs`), voir « Le CSS page par page » |
| `images` | toutes les images servies (`dist/`, donc `public/` et les images importées par le code) |

Une page compte l'application et tout ce que sa vue importe d'emblée. Les fenêtres et les sous-pages chargées plus tard n'y sont pas.

**Règle des illustrations** : dans `illustrations/`, `personnage/`, `troupe/`, `avatars/` et les images importées par le code (`assets/`), seuls le WebP et le SVG sont admis. Une autre image fait échouer le budget. Les icônes de l'application (favicon, écran d'accueil) restent en PNG, parce que les navigateurs le demandent. Une seule exception : les 8 anciens avatars PNG, en attendant que Kevin accepte de les retirer (voir plus bas).

## Les chiffres du 2026-11-10 et les limites

Mesurés sur main après la PR 20 (#628). Chaque limite vaut la taille + 5 %, arrondie à la centaine d'octets inférieure.

| Mesure | Brut | gzip | brotli | Limite |
|---|---:|---:|---:|---:|
| js-premier | 290,5 Ko | 106,2 Ko | 94,2 Ko | 111,5 Ko (gzip) |
| js-total | 1107,4 Ko | 382,2 Ko | 339,9 Ko | 426,0 Ko (gzip) |
| js-accueil | 290,5 Ko | 106,2 Ko | 94,2 Ko | 111,5 Ko (gzip) |
| js-candidatures | 429,1 Ko | 154,7 Ko | 137,2 Ko | 168,0 Ko (gzip) |
| js-bilan | 290,2 Ko | 108,0 Ko | 95,8 Ko | 113,4 Ko (gzip) |
| js-compte | 259,5 Ko | 94,2 Ko | 83,2 Ko | 98,8 Ko (gzip) |
| css-premier | 327,1 Ko | 57,0 Ko | 45,4 Ko | 59,8 Ko (gzip) |
| css-total | 484,3 Ko | 92,2 Ko | 75,7 Ko | 117,0 Ko (gzip) |
| css-accueil | 327,1 Ko | 57,0 Ko | 45,4 Ko | 59,8 Ko (gzip) |
| css-candidatures | 360,1 Ko | 65,1 Ko | 52,3 Ko | 69,0 Ko (gzip) |
| css-bilan | 335,5 Ko | 59,4 Ko | 47,5 Ko | 62,4 Ko (gzip) |
| css-compte | 332,6 Ko | 58,3 Ko | 46,5 Ko | 61,2 Ko (gzip) |
| images | 4660,1 Ko | n/a | n/a | 4893,1 Ko (brut) |

La limite de css-total est relevée de 96,8 Ko à 100,0 Ko le 12 novembre 2026 (décision de Kevin, PR 39) : ce total compte les pages chargées à la demande, et la limite du premier écran (css-premier, 59,8 Ko) ne change pas.

Le 13 novembre 2026 (PR 44), trois limites de totaux sont relevées une fois pour la fin du paquet récapitulatif et le lot « Tri et visuel » du 11 novembre : css-total à 115,0 Ko, js-total à 420,0 Ko, js-candidatures à 168,0 Ko. Mesures à la dernière branche du lot : 111,6 Ko, 414,7 Ko et 165,1 Ko. Les limites du premier écran (js-premier, css-premier) ne changent pas.

Le 14 novembre 2026, js-total passe à 425,0 Ko (décision de Kevin) : main mesurait 421,0 Ko après les PR #708 et #712 de la maquette du 14 novembre. Les autres limites ne changent pas ; l'allègement reste suivi dans le ticket #664.

Le 15 novembre 2026 (#722, liaison carte → détail sur Candidatures ordinateur), css-total passe à 116,0 Ko et js-total à 426,0 Ko, une seule fois (décision de Kevin). Mesures avec main et #721 : 115,5 Ko et 425,4 Ko. Le CSS mort avait déjà été retiré par #720. Pas de nouveau relèvement automatique : une PR qui dépasse s'arrête, et on dit à Kevin de combien et pourquoi avant de toucher à une limite.

Le 15 novembre 2026 (#726, ticket #664), css-total passe à 117,0 Ko et css-candidatures à 69,0 Ko, une seule fois (décision de Kevin : « liaison, code jobup, sous-pages téléphone ; #726 a tout tenté côté CSS »). Mesures sur main + #722 + #724 + #723 + #725 : 116,7 Ko et 68,3 Ko. Les pistes CSS essayées sont dans « Regrouper ce qui se charge ensemble » ; le thème Auto posé par le JS et le regroupement des composants de Candidatures sont écartés, parce qu'ils dégradent l'écran ou d'autres pages. Pas de nouveau relèvement automatique.

## Le CSS page par page (16.11.2026)

Décision de Kevin du 16 novembre 2026 (issue #797, `docs/decisions/2026-11-16-1510-css-limites-par-page.md`) : le CSS a une limite **par page**. On ne charge pas tout le CSS d'un coup, seulement celui de la page qu'on ouvre ; c'est lui qui ralentit vraiment l'écran. Chaque page de `router.ts` est mesurée : le socle de l'application, plus le CSS de sa vue et de sa page parente (Candidatures, Bilan). Une vue qui n'est dans aucune page fait échouer le budget : une nouvelle page reçoit sa limite dans la PR qui la crée.

Chaque limite vaut le CSS de la page sur main le 16.11 (après #796), + 3 %, arrondi à la centaine d'octets inférieure. `css-total` est refixé une seule fois de la même façon, à 123,1 Ko (119 581 o + 3 %). Il ne sert plus que de garde-fou. `css-premier` disparaît : c'était la même mesure que `css-accueil`.

| Page | Vue(s) | gzip le 16.11 | Limite |
|---|---|---:|---:|
| css-accueil | `TodayView` | 58,9 Ko | 60,6 Ko |
| css-trier | `TriageView` | 62,0 Ko | 63,8 Ko |
| css-candidatures | `JobsView` + `OffersView` | 69,1 Ko | 71,1 Ko |
| css-preparer | `PreparationView` | 67,2 Ko | 69,2 Ko |
| css-suivi | `JobsView` + `ApplicationsView` | 70,1 Ko | 72,2 Ko |
| css-alertes | `JobsView` + `AlertsView` | 60,0 Ko | 61,8 Ko |
| css-rendez-vous-orp | `JobsView` + `OrpMeetingView` | 63,2 Ko | 65,0 Ko |
| css-relances | `FollowUpsView` | 57,5 Ko | 59,1 Ko |
| css-bilan | `BilanView` + `BilanOrpView` | 59,2 Ko | 60,9 Ko |
| css-resultats | `BilanView` + `InsightsView` | 57,2 Ko | 58,9 Ko |
| css-formations | `BilanView` + `TrainingsView` | 58,1 Ko | 59,8 Ko |
| css-fiche-orp | `OrpFicheView` | 58,7 Ko | 60,4 Ko |
| css-entrainement | `PracticeView` | 58,1 Ko | 59,8 Ko |
| css-notifications | `NotificationsView` | 59,3 Ko | 61,1 Ko |
| css-compte | `AccountView` | 57,5 Ko | 59,2 Ko |
| css-profil | `ProfileView` | 61,3 Ko | 63,1 Ko |
| css-reglages | `SettingsView` | 58,7 Ko | 60,4 Ko |
| css-diagnostic | `DiagnosticView` | 56,2 Ko | 57,9 Ko |
| css-connexion | `LoginView` | 58,0 Ko | 59,7 Ko |
| css-inscription | `SignupView` | 56,6 Ko | 58,2 Ko |
| css-acces | `AccessView` | 56,6 Ko | 58,2 Ko |
| css-bienvenue | `WelcomeView` | 63,6 Ko | 65,4 Ko |
| css-getemall | `GetemallAuthorizeView` | 57,3 Ko | 59,0 Ko |
| css-extension | `ExtensionLinkView` | 56,2 Ko | 57,9 Ko |
| css-la-plateforme | `DiscoverView` | 56,2 Ko | 57,9 Ko |
| css-tes-donnees | `PrivacyView` | 56,5 Ko | 58,1 Ko |
| css-accessibilite | `AccessibilityView` | 56,2 Ko | 57,9 Ko |
| css-conditions | `TermsView` | 56,2 Ko | 57,9 Ko |
| css-a-propos | `AboutView` | 56,2 Ko | 57,9 Ko |
| css-introuvable | `NotFoundView` | 57,2 Ko | 58,9 Ko |

Le socle commun à toutes les pages (l'application seule) pèse 56,2 Ko ; une page sans CSS propre (À propos, Conditions…) pèse exactement le socle. Une règle ajoutée à `style.css` compte donc sur toutes les pages à la fois, une règle d'un composant ne compte que sur les pages qui le chargent.

Pas de coupe de contenu pour gagner du poids (Kevin, 16.11). Une PR qui dépasse la limite d'une page s'arrête et dit de combien ; la limite ne se relève qu'avec l'accord de Kevin.

Les « 93 Ko » de l'ancien budget étaient la taille **gzip** de tout le CSS. Il pesait alors 92,2 Ko : 484,3 Ko bruts, 75,7 Ko en brotli.

## Les commandes

```sh
make poids            # construit, puis mesure ; échoue au-delà d'une limite
cd frontend && node scripts/poids.mjs --releve   # après un build : les limites à + 5 % des tailles du jour
make css-inutilise    # le CSS inutilisé (voir plus bas)
```

En CI, la tâche « Interface (vitest, types, poids) » (`.github/workflows/tests.yml`) lance `npm run poids:ci` (`scripts/poids-ci.sh`) à chaque PR. **La PR échoue si une mesure dépasse sa limite** ou si une illustration n'est pas en WebP. Le message dit quels fichiers pèsent le plus. Exception (Kevin, 16.11) : si main (HEAD^1 du commit de fusion) dépassait déjà cette limite, la mesure passe quand la branche ne l'alourdit pas ; une branche qui ajoute du poids à une mesure en dépassement reste bloquée.

**Relever une limite** : seulement avec l'accord de Kevin. La PR donne la raison et ce qui a été retiré ailleurs en compensation, puis change `LIMITS` dans `poids.mjs` et le tableau ci-dessus.

## Le CSS inutilisé

`frontend/scripts/css-inutilise.mjs` lit la couverture de Chrome (l'onglet Coverage des DevTools) sur Accueil, Candidatures et Bilan. Il les mesure à 390 et 1440 px, en clair et en sombre. Pour le lancer, il faut un build servi par `vite preview`, avec l'API de démo derrière :

```sh
cd frontend && npm run build
JOBBOT_DEV_API_URL=http://127.0.0.1:8200 npx vite preview --port 4173   # l'API de démo tourne sur 8200
make css-inutilise
```

Relevé du 2026-11-10 :

| Page | CSS chargé (brut) | CSS qui sert |
|---|---:|---:|
| Accueil | 333,6 Ko | 33,0 Ko (10 %) |
| Candidatures | 366,6 Ko | 53,7 Ko (15 %) |
| Bilan | 342,0 Ko | 36,6 Ko (11 %) |

La cause : `style.css` (327 Ko bruts) est chargé en entier dès le premier écran, pour toutes les pages. Le script classe les règles qui ne servent sur aucune des trois pages :

- **Sert ailleurs** : 2787 règles, 275,5 Ko bruts. Une de leurs classes est écrite dans un composant : une autre page, un état, une fenêtre. Elles restent.
- **Retiré le 2026-11-11** (accord de Kevin) : 15 règles, 1,2 Ko bruts. Leurs classes ne sont écrites nulle part dans `src/`, ni en toutes lettres ni par un gabarit (`` `xxx-${…}` `` dans un `:class`, une concaténation) :

| Règles retirées (style.css) | Classe absente du code |
|---|---|
| `.bilan-row-more`, `.bilan-row-more svg` | `bilan-row-more` |
| `.info-card`, `.info-card .summary-rows`, `.info-card .summary-rows>div+div`, `.info-card>.edit-round`, `.criteria-summary.info-card` | `info-card` (son exception dans `scales.test.ts` est retirée aussi) |
| `.alerts-list-head`, `.alerts-list-head h2` | `alerts-list-head` |
| `.orp-rows-link`, `… .orp-row`, `… .orp-row:hover`, `… .orp-what`, `… .orp-what strong` | `orp-rows-link` |
| `.offer-bar-spark` (téléphone) | `offer-bar-spark` |

- **Gardé** : `.ft-orp-meeting .ft-tie` et `.ft-orp-meeting .ft-tie-swing`, qui figuraient dans la première liste. La classe est construite par `` `ft-${kind}` `` dans `FaceTransform.vue`, avec `kind = "orp-meeting"` (la transition vers le rendez-vous ORP). Le script reconnaît désormais un gabarit à n'importe quel préfixe (`ft-` ici, pas seulement `ft-orp-`).
- **Déjà retirées** : 4 règles trouvées ensuite par ce contrôle plus strict (`.orp-row-state`, `.orp-row-state.ok`, `.orp-row-state.todo`, `.orp-row-chevron`). Leurs classes avaient quitté les composants avec la PR 6 du 9 novembre ; la PR 38 les a retirées de `style.css`.

Retirer ces règles ferait gagner environ 0,3 Ko en gzip. Le gain important viendrait de découper `style.css` par page, comme le JavaScript (docs/117 §3) : Accueil chargerait environ 33 Ko de CSS brut au lieu de 334. C'est un chantier à part, à proposer.

**Les 8 avatars PNG** (`public/avatars/avatar-N-256.png`, 610 Ko) : retirés le 2026-11-13 avec l'accord de Kevin. L'avatar affiché (en-tête, menu du compte, choix de l'image) passe par `ProfileImage.vue`, qui appelle `avatarSrc()` de `useProfileImage.ts` : `/avatars/avatar-N-128.webp` jusqu'à 48 px, `/avatars/avatar-N-256.webp` au-delà. Aucun code ne lisait les PNG : c'étaient les mêmes dessins que les WebP, et des copies de `docs/mobile/illustrations/avatars/`, qui restent dans la maquette. Il n'y a plus d'exception au WebP dans `poids.mjs`.

## Regrouper ce qui se charge ensemble (#664, 15.11.2026)

`js-total` et `css-total` additionnent **tous** les fichiers, chacun compressé à part. Découper davantage (une page ou un bloc chargé à la demande) n'allège donc pas ces deux mesures : chaque nouveau fichier perd le contexte de compression des autres. Essai du 15.11 : `JobupCodeBox` en chargement différé, + 0,6 Ko de JS total. Découper ne sert qu'aux mesures d'une page (`js-premier`, `js-candidatures`…).

Ce qui allège le total, c'est l'inverse : regrouper des fichiers **toujours chargés ensemble**. `vite.config.ts` met dans un seul fichier, `commun-*.js`, ce que toute page charge avec l'application : Vue, vue-router, openapi-fetch (`node_modules`) et nos modules que l'entrée importe toujours (`api/client.ts`, `icons.ts`, `dates.ts`, `brandPaths.ts`, `AppIcon.vue`). Avant, Vue faisait deux fichiers (`runtime-core`, `runtime-dom`) dont le nom long revenait dans l'import de 84 pages. `includeDependenciesRecursively: false` empêche le groupe d'aspirer leurs dépendances (sinon l'entrée et des pages chargées plus tard s'y retrouvent).

Mesure sur main + #722 + #724 + #723 + #725 : JS total 427,4 → 422,6 Ko (− 4,8). Chaque page télécharge 1,6 à 2,6 Ko de JS en moins ; le CSS ne change pas.

Pistes mesurées sans gain suffisant (même ensemble) :

| Piste | Gain gzip | Retenue |
|---|---|---|
| Icônes : SVG en ligne dupliqués entre composants | < 0,1 Ko (seules les flèches de liaison se répètent, dans un même fichier) | non |
| Dépendances remplacées par du natif | 0 : seules Vue, vue-router, openapi-fetch et la police ; aucune bibliothèque de dates ou d'utilitaires | sans objet |
| Doublons clair/sombre de `style.css` passés par les jetons | 0,0 Ko (gzip les compresse déjà ; − 1,2 Ko brut seulement) | non |
| Cible CSS relevée (Chrome 120, Safari 17, Firefox 121) | − 0,1 Ko, et des navigateurs encore pris en charge perdraient des préfixes | non |
| Thème Auto posé par le JS, copies `@media (prefers-color-scheme: dark)` retirées | environ − 0,5 Ko CSS, mais un éclair clair au chargement en sombre avant le JS | non, dégrade l'écran |
| Regrouper aussi les composants partagés de Candidatures | − 8,0 Ko JS et − 0,7 Ko CSS de plus, mais + 13 à + 21 Ko à télécharger sur Connexion, Inscription, Réglages, Alertes… | non |

Relèvement du 15.11.2026 (Kevin, une seule fois) : JS total 426 000 → 426 700 o et CSS total 117 500 → 117 750 o, pour le dos des cartes Trier ordinateur (verdicts, étiquettes, anneau). Mesure sur main d4f2bec sans autre PR ouverte : JS 425 880 → 426 689 o, CSS 117 440 → 117 736 o. Puis, avec les PR 739 et 740 ouvertes (main + 739 + 740 + Trier : JS 426 777 o, CSS 117 775 o), relèvement du reste seulement : JS 426 700 → 426 780 o, CSS 117 750 → 117 780 o (Kevin, 15.11.2026, 18 h 05).
