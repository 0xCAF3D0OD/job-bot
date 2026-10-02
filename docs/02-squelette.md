# 02 — Squelette de la plateforme (version 0.1.0)

> Statut : **à valider**. Aucun code avant accord.
> S'appuie sur [01-cadrage.md](01-cadrage.md), qui n'est pas modifié.

## 1. Partage des rôles

| Je code (Claude) | Tu fais (Kevin) |
|---|---|
| L'application : backend Python, worker, frontend TypeScript, base de données, tests | Toute l'infrastructure : Dockerfiles, docker compose, CI/CD, Kubernetes, Helm, Terraform, Ansible, monitoring |
| Le **contrat d'exploitation** (§4) : ce que l'application attend de l'infra et ce qu'elle lui fournit | Les choix d'hébergement, de réseau, de stockage, de secrets |

Concrètement, je ne crée **ni le dossier `deploy/`, ni de Dockerfile, ni de workflow GitHub Actions**. Les lignes du cadrage qui en parlent (§7 colonne « version locale », §8 `deploy/`, §11 « compose » et « CI ») décrivent ce que **toi** tu construiras. De mon côté, l'application est écrite pour s'y brancher sans modification.

Pour que la plateforme tourne avant ton infra, elle se lance **directement sur ton Mac**, sans conteneur : PostgreSQL installé avec Homebrew, et des commandes `make` (§6).

## 2. Ce que fait la version 0.1.0

C'est une plateforme vide, mais complète de bout en bout :

- l'API répond et lit la base ;
- le worker exécute une tâche planifiée de démonstration (`heartbeat`, toutes les 5 minutes), qui écrit dans `job_runs` ;
- l'interface affiche le menu définitif (Offres, Profil, Prérequis, Réglages, Journal, ORP), avec des pages encore vides, plus une page **État** qui montre la santé de l'API, de la base et du worker, et les dernières exécutions de tâches ;
- les tests passent.

Les vraies fonctions arrivent à partir de la 0.2.0 (collecte Gmail), comme prévu au §11 du cadrage.

## 3. Arborescence créée

```
job-bot/
├── backend/
│   ├── pyproject.toml          dépendances, ruff, mypy, pytest (géré avec uv)
│   ├── alembic.ini
│   ├── alembic/versions/       0001 : tables settings + job_runs
│   ├── src/jobbot/
│   │   ├── __main__.py         point d'entrée unique : `jobbot <commande>` (§4.2)
│   │   ├── settings.py         lecture et validation des variables d'environnement
│   │   ├── logging.py          structlog : JSON ou console
│   │   ├── metrics.py          métriques Prometheus
│   │   ├── api/
│   │   │   ├── app.py          création de l'application FastAPI
│   │   │   ├── health.py       /healthz, /readyz, /version
│   │   │   └── routes/status.py  /api/status, /api/job-runs
│   │   ├── worker/
│   │   │   ├── app.py          procrastinate + petit serveur HTTP de santé/métriques
│   │   │   └── tasks/heartbeat.py
│   │   ├── db/
│   │   │   ├── base.py         moteur et sessions SQLAlchemy
│   │   │   └── models.py       Setting, JobRun
│   │   ├── core/               vide en 0.1 (règles métier pures à partir de 0.3)
│   │   └── storage/
│   │       ├── base.py         interface Storage
│   │       └── local.py        implémentation disque local
│   └── tests/
│       ├── test_health.py
│       ├── test_settings.py
│       ├── test_heartbeat.py
│       └── test_no_personal_data.py   échoue si un fichier de data/ est suivi par git
├── frontend/
│   ├── package.json            Vue 3, Vite, TypeScript, vue-router, vitest
│   ├── vite.config.ts          proxy /api → backend en développement
│   └── src/
│       ├── api/schema.d.ts     types générés depuis l'OpenAPI du backend
│       ├── api/client.ts       client fetch typé (openapi-fetch)
│       ├── router.ts
│       └── views/              État + pages vides du menu
├── data/                       ignoré par git (documents, exports ORP)
├── docs/
├── .env.example                toutes les variables, commentées (§4.1)
├── .gitignore                  Python + Node + data/ + .env
├── Makefile                    commandes de développement (§6)
└── README.md                   installation, lancement, lien vers le contrat d'exploitation
```

## 4. Contrat d'exploitation

C'est la partie qui prépare ton infrastructure. Elle sera recopiée dans `docs/exploitation.md` et tenue à jour à chaque version : c'est **ton** document de référence pour écrire Dockerfiles, manifestes et charts.

### 4.1 Configuration : uniquement des variables d'environnement

- Préfixe `JOBBOT_` partout.
- L'application refuse de démarrer si une variable obligatoire manque ou est invalide, avec un message clair. `jobbot check` fait la même vérification sans rien lancer.
- Chaque variable secrète accepte une variante `_FILE` (par exemple `JOBBOT_DATABASE_URL_FILE=/run/secrets/db_url`). Ça fonctionne directement avec les secrets Docker et les Secrets Kubernetes montés en fichier.
- Dans `.env.example`, chaque variable est marquée **secret** ou **config**, pour te faciliter le partage entre Secret et ConfigMap.

| Variable | Type | Défaut | Rôle | Depuis |
|---|---|---|---|---|
| `JOBBOT_DATABASE_URL` | secret | — (obligatoire) | `postgresql+psycopg://user:pass@host:5432/jobbot` | 0.1 |
| `JOBBOT_ENV` | config | `dev` | `dev` / `prod` (en prod : logs JSON forcés, docs OpenAPI masquées) | 0.1 |
| `JOBBOT_API_HOST` | config | `127.0.0.1` | à passer à `0.0.0.0` dans un conteneur | 0.1 |
| `JOBBOT_API_PORT` | config | `8000` | port de l'API | 0.1 |
| `JOBBOT_WORKER_HTTP_PORT` | config | `8001` | santé et métriques du worker | 0.1 |
| `JOBBOT_LOG_LEVEL` | config | `INFO` | | 0.1 |
| `JOBBOT_LOG_FORMAT` | config | `console` en dev, `json` en prod | | 0.1 |
| `JOBBOT_SCHEDULER_ENABLED` | config | `true` | `false` : le worker n'exécute plus les tâches périodiques, que tu déclenches alors toi-même (`CronJob` + `jobbot run-job`) | 0.1 |
| `JOBBOT_STORAGE_BACKEND` | config | `local` | `local` ; `s3` arrivera si tu en as besoin | 0.1 |
| `JOBBOT_STORAGE_PATH` | config | `./data` | dossier des fichiers : le seul endroit où l'application écrit, donc ton volume | 0.1 |
| `JOBBOT_CORS_ORIGINS` | config | vide | seulement si le frontend est servi sur un autre domaine que l'API | 0.1 |
| `JOBBOT_VERSION` | config | `dev` | renvoyé par `/version`, à remplir au build avec le tag ou le SHA git | 0.1 |
| `JOBBOT_IMAP_*` | secret | — | collecte Gmail | 0.2 |
| `JOBBOT_ANTHROPIC_API_KEY` | secret | — | IA | 0.4 |
| `JOBBOT_NTFY_URL`, `JOBBOT_NTFY_TOPIC` | config | — | notifications | 0.4 |

Les réglages métier (prérequis, seuils, objectif ORP) ne sont **pas** des variables d'environnement : ils sont en base et se modifient dans l'interface (cadrage §4).

### 4.2 Processus : une seule commande, plusieurs rôles

Un seul paquet Python, qui pourra donc être une seule image. Le rôle est choisi par la commande :

| Commande | Rôle | Durée | Pour ton infra |
|---|---|---|---|
| `jobbot api` | API HTTP (uvicorn) | permanent | `Deployment`, plusieurs réplicas possibles |
| `jobbot worker` | exécute la file de tâches + tâches planifiées | permanent | `Deployment` ; plusieurs réplicas possibles (verrouillage par PostgreSQL) |
| `jobbot migrate` | applique les migrations Alembic puis s'arrête | ponctuel | `Job` ou initContainer, avant le déploiement |
| `jobbot run-job <nom>` | exécute une tâche une fois puis s'arrête (code retour 0 ou 1) | ponctuel | `CronJob`, si tu désactives le planificateur interne |
| `jobbot check` | valide la configuration et la connexion à la base | ponctuel | test de démarrage, débogage |

Règles :
- **L'API et le worker n'appliquent jamais les migrations au démarrage.** Si le schéma n'est pas à jour, `/readyz` répond 503 et l'explique.
- Le frontend est un **build statique** (`frontend/dist/`) qui appelle l'API en chemin relatif, `/api/...`. Aucune URL n'est figée dans le build. C'est ton reverse proxy ou ton Ingress qui envoie `/api` vers le backend et le reste vers les fichiers statiques.

### 4.3 Santé

| Point d'entrée | Processus | Répond 200 si | Usage |
|---|---|---|---|
| `GET /healthz` | api, worker | le processus tourne (aucun appel à la base) | sonde liveness |
| `GET /readyz` | api, worker | base joignable **et** schéma à la dernière migration | sonde readiness |
| `GET /version` | api | toujours ; renvoie version et révision de migration | vérification après déploiement |

Ces points d'entrée sont hors de `/api`, sans authentification, et ne journalisent rien en dessous du niveau DEBUG (pour ne pas noyer les logs sous les sondes).

### 4.4 Métriques Prometheus

`GET /metrics` sur l'API (port 8000) et sur le worker (port 8001). Métriques livrées en 0.1 :

| Nom | Type | Étiquettes |
|---|---|---|
| `jobbot_http_requests_total` | counter | `method`, `route`, `status` |
| `jobbot_http_request_duration_seconds` | histogram | `method`, `route` |
| `jobbot_job_runs_total` | counter | `job`, `status` (`success`/`failure`) |
| `jobbot_job_duration_seconds` | histogram | `job` |
| `jobbot_job_last_success_timestamp_seconds` | gauge | `job` |
| `jobbot_db_up` | gauge | — |

`route` est le modèle de route (`/api/offers/{id}`), jamais l'URL réelle, pour garder un nombre d'étiquettes borné. Les versions suivantes ajouteront leurs métriques (offres collectées, coût IA…), listées dans `exploitation.md`.

### 4.5 Logs

- Uniquement sur **stdout**, jamais dans un fichier.
- En JSON en prod, une ligne par événement : `timestamp`, `level`, `event`, `logger`, plus `request_id` (API) ou `job` et `run_id` (worker).
- L'API accepte un en-tête `X-Request-ID` entrant, ou en génère un, et le renvoie dans la réponse.
- **Aucune donnée personnelle** dans les logs : ni contenu de CV, ni blocs de profil, ni texte de lettre, ni adresse e-mail. Un test le vérifie sur les cas connus.

### 4.6 Comportement attendu par un orchestrateur

- **Sans état local** : en dehors de `JOBBOT_STORAGE_PATH`, l'application n'écrit qu'éventuellement dans le dossier temporaire du système. Elle supporte un système de fichiers en lecture seule.
- **Pas besoin de root**, aucun port privilégié.
- **SIGTERM** : l'API termine les requêtes en cours, le worker finit sa tâche en cours ou la remet dans la file. Arrêt en moins de 25 secondes, ce qui tient dans les 30 secondes par défaut de Kubernetes.
- **Démarrage tolérant** : si la base n'est pas encore là, l'API démarre quand même. `/healthz` répond 200 et `/readyz` répond 503 jusqu'à ce qu'elle soit joignable. Pas de plantage en boucle.
- **Tâches idempotentes** : relancer une tâche ne crée pas de doublon (cadrage §2). Un `CronJob` qui s'exécute deux fois n'est donc pas un problème.

## 5. Base de données en 0.1

Migration `0001` : seulement les tables utiles dès maintenant. Chaque version ajoute les siennes, selon le schéma du cadrage §5.

```
settings   key TEXT PRIMARY KEY, value JSONB NOT NULL, updated_at TIMESTAMPTZ
job_runs   id BIGSERIAL, job TEXT, run_id UUID UNIQUE, started_at, finished_at,
           status TEXT (running|success|failure), items_in INT, items_out INT, error TEXT
```

La migration crée aussi les valeurs par défaut de `settings` (seuil ntfy 70, plafond IA 10 CHF, objectif ORP vide). Les tables internes de procrastinate sont créées par la même commande `jobbot migrate`.

## 6. Lancer en local (sans conteneur)

Prérequis à installer une fois. Sur ton Mac, il manque aujourd'hui `uv`, Python 3.13 et PostgreSQL :

```bash
brew install uv postgresql@17
```

```bash
brew services start postgresql@17
```

`uv` installe lui-même Python 3.13 pour le projet, sans toucher au Python du système.

Commandes du `Makefile` :

| Commande | Effet |
|---|---|
| `make setup` | installe les dépendances backend et frontend, crée la base `jobbot` et la base `jobbot_test` si absentes, copie `.env.example` vers `.env` |
| `make migrate` | `jobbot migrate` |
| `make dev` | lance api + worker + frontend (Vite sur http://localhost:5173) |
| `make test` | pytest (sur `jobbot_test`) + vitest + vue-tsc |
| `make lint` | ruff + mypy + eslint |
| `make openapi` | régénère `frontend/src/api/schema.d.ts` depuis le backend |

Le `Makefile` ne sert qu'au développement. Il ne construit pas d'image et ne déploie rien.

## 7. Tests de la 0.1

- `/healthz` répond 200 sans base ; `/readyz` répond 503 sans base, 503 si une migration manque, 200 sinon.
- Une configuration invalide arrête le démarrage avec un message qui nomme la variable fautive ; la variante `_FILE` est bien lue.
- La tâche `heartbeat` écrit une ligne `success` dans `job_runs` et incrémente les métriques ; `jobbot run-job heartbeat` renvoie 0.
- `/metrics` expose les métriques du §4.4.
- `test_no_personal_data` : `git ls-files data/` est vide et `.gitignore` contient `data/` et `.env`.
- Frontend : la page État affiche correctement les trois cas (tout va bien, base absente, worker silencieux depuis plus de 10 minutes).
- Les types `schema.d.ts` correspondent à l'OpenAPI actuel. `make openapi` suivi de `git diff --exit-code` sert de vérification, que tu pourras reprendre dans ta CI.

## 8. Livraison

- Une PR `feat/0.1.0-squelette`, avec le README et `docs/exploitation.md`.
- Je vérifie moi-même que `make setup && make migrate && make dev` fonctionne sur ton Mac et que la page État est verte avant d'ouvrir la PR.
- Le `.gitignore` Python actuel est remplacé par une version Python + Node + `data/` + `.env`.

## Points à valider

1. **Partage des rôles** du §1 : je ne crée ni `deploy/`, ni Dockerfile, ni CI. Le contrat d'exploitation (§4) est ce que je te livre pour ton infra.
2. **Lancement local sans conteneur** : PostgreSQL et uv installés avec Homebrew (§6). Je lance moi-même les deux commandes `brew install` et `brew services start`, ou tu préfères le faire ?
3. **Port et adresse par défaut** : API sur `127.0.0.1:8000`, worker sur `8001`.
4. **Planificateur** : intégré au worker par défaut, désactivable par `JOBBOT_SCHEDULER_ENABLED=false` pour que tu passes à des `CronJob` (§4.2).
5. **Pas d'authentification en 0.1** : l'application n'écoute que sur `127.0.0.1`. La protection d'un accès distant (VPN, authentification devant l'Ingress, ou login dans l'application) sera tranchée avant ton premier déploiement hors de ton Mac.
