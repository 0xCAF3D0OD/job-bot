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
| `js-premier`, `css-premier` | ce que charge le premier écran : l'application et Aujourd'hui |
| `js-total`, `css-total` | tout le code, tout le CSS |
| `js-accueil`, `css-accueil` | Aujourd'hui (`TodayView`) |
| `js-candidatures`, `css-candidatures` | Candidatures › Offres (`JobsView` + `OffersView`) |
| `js-bilan`, `css-bilan` | Bilan › ORP (`BilanView` + `BilanOrpView`) |
| `js-compte`, `css-compte` | Compte (`AccountView`) |
| `images` | toutes les images servies (`dist/`, donc `public/` et les images importées par le code) |

Une page compte l'application et tout ce que sa vue importe d'emblée. Les fenêtres et les sous-pages chargées plus tard n'y sont pas.

**Règle des illustrations** : dans `illustrations/`, `personnage/`, `troupe/`, `avatars/` et les images importées par le code (`assets/`), seuls le WebP et le SVG sont admis. Une autre image fait échouer le budget. Les icônes de l'application (favicon, écran d'accueil) restent en PNG, parce que les navigateurs le demandent. Une seule exception : les 8 anciens avatars PNG, en attendant que Kevin accepte de les retirer (voir plus bas).

## Les chiffres du 2026-11-10 et les limites

Mesurés sur main après la PR 20 (#628). Chaque limite vaut la taille + 5 %, arrondie à la centaine d'octets inférieure.

| Mesure | Brut | gzip | brotli | Limite |
|---|---:|---:|---:|---:|
| js-premier | 290,5 Ko | 106,2 Ko | 94,2 Ko | 111,5 Ko (gzip) |
| js-total | 1107,4 Ko | 382,2 Ko | 339,9 Ko | 401,3 Ko (gzip) |
| js-accueil | 290,5 Ko | 106,2 Ko | 94,2 Ko | 111,5 Ko (gzip) |
| js-candidatures | 429,1 Ko | 154,7 Ko | 137,2 Ko | 162,4 Ko (gzip) |
| js-bilan | 290,2 Ko | 108,0 Ko | 95,8 Ko | 113,4 Ko (gzip) |
| js-compte | 259,5 Ko | 94,2 Ko | 83,2 Ko | 98,8 Ko (gzip) |
| css-premier | 327,1 Ko | 57,0 Ko | 45,4 Ko | 59,8 Ko (gzip) |
| css-total | 484,3 Ko | 92,2 Ko | 75,7 Ko | 96,8 Ko (gzip) |
| css-accueil | 327,1 Ko | 57,0 Ko | 45,4 Ko | 59,8 Ko (gzip) |
| css-candidatures | 360,1 Ko | 65,1 Ko | 52,3 Ko | 68,3 Ko (gzip) |
| css-bilan | 335,5 Ko | 59,4 Ko | 47,5 Ko | 62,4 Ko (gzip) |
| css-compte | 332,6 Ko | 58,3 Ko | 46,5 Ko | 61,2 Ko (gzip) |
| images | 4660,1 Ko | n/a | n/a | 4893,1 Ko (brut) |

Les « 93 Ko » de l'ancien budget étaient la taille **gzip** de tout le CSS. Il pesait alors 92,2 Ko : 484,3 Ko bruts, 75,7 Ko en brotli.

## Les commandes

```sh
make poids            # construit, puis mesure ; échoue au-delà d'une limite
cd frontend && node scripts/poids.mjs --releve   # après un build : les limites à + 5 % des tailles du jour
make css-inutilise    # le CSS inutilisé (voir plus bas)
```

En CI, la tâche « Interface (vitest, types, poids) » (`.github/workflows/tests.yml`) lance `npm run poids` à chaque PR. **La PR échoue si une mesure dépasse sa limite** ou si une illustration n'est pas en WebP. Le message dit quels fichiers pèsent le plus.

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
- **À retirer, en attente d'accord** : 4 règles, 0,3 Ko bruts, trouvées par ce même contrôle plus strict. Avant, le préfixe `orp-row-${…}` d'un `data-test` les faisait passer pour construites ; le script ignore maintenant les gabarits des `data-test`, des clés et des `id`, qui ne sont pas des classes. Leurs classes ont quitté les composants avec la PR 6 du 9 novembre (Bilan et Suivi ORP) :

| Règles (style.css) | Classe absente du code |
|---|---|
| `.orp-row-state`, `.orp-row-state.ok`, `.orp-row-state.todo` | `orp-row-state` |
| `.orp-row-chevron` | `orp-row-chevron` |

Retirer ces règles ferait gagner environ 0,3 Ko en gzip. Le gain important viendrait de découper `style.css` par page, comme le JavaScript (docs/117 §3) : Accueil chargerait environ 33 Ko de CSS brut au lieu de 334. C'est un chantier à part, à proposer.

**Les 8 avatars PNG** (`public/avatars/avatar-N-256.png`, 610 Ko) : gardés, décision de Kevin en attente. L'avatar affiché (en-tête, menu du compte, choix de l'image) passe par `ProfileImage.vue`, qui appelle `avatarSrc()` de `useProfileImage.ts` : `/avatars/avatar-N-128.webp` jusqu'à 48 px, `/avatars/avatar-N-256.webp` au-delà. Aucun fichier du code ne lit les PNG. Ce sont les mêmes dessins que les WebP (écart moyen de 1,2 à 1,8 sur 255 par pixel, sur fond blanc : la compression), et des copies à l'octet près de `docs/mobile/illustrations/avatars/avatar-N-256.png`.
