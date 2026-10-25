# jobA1

> **Less searching. More living.** (anciennement job-bot : le dépôt, le paquet `jobbot`, la commande `jobbot` et les variables `JOBBOT_*` gardent leur nom technique.)

Assistant de recherche d'emploi : il collecte les offres reçues par alerte e-mail (jobup et Indeed, les autres sites lus par l'IA), écarte celles qui ne respectent pas tes prérequis, note les autres par rapport à ton profil, prépare lettre et CV, et tient le journal des candidatures exportable pour l'ORP. Tu valides chaque envoi.

- Cadrage : [docs/01-cadrage.md](docs/01-cadrage.md)
- Versions : [CHANGELOG.md](CHANGELOG.md) ; le cadrage en cours : [docs/135-echelles.md](docs/135-echelles.md)
- Règles de sécurité : [docs/securite.md](docs/securite.md) ; signaler une faille : [SECURITY.md](SECURITY.md)
- Règles de l'interface (illustrations, mouvement, clic) : [docs/interface.md](docs/interface.md)
- Contrat d'exploitation, pour l'infrastructure : [docs/exploitation.md](docs/exploitation.md)

## Versions

L'historique des versions, une ligne par version : [CHANGELOG.md](CHANGELOG.md).

## Lancer en local

Prérequis (macOS) :

```bash
brew install uv postgresql@17
```

```bash
brew services start postgresql@17
```

Puis, à la racine du dépôt :

```bash
make setup
```

```bash
make migrate
```

```bash
make dev
```

L'interface est sur http://localhost:5173 (page Aujourd'hui), l'API sur http://127.0.0.1:8000 (documentation sur `/api/docs`). `Ctrl-C` arrête tout.

| Commande | Effet |
|---|---|
| `make setup` | dépendances backend et frontend, bases `jobbot` et `jobbot_test`, copie de `.env.example` en `.env` |
| `make migrate` | applique les migrations |
| `make update` | met la plateforme à jour : maintenance annoncée, `git pull`, dépendances, migrations, maintenance levée ; il reste à redémarrer `make dev` (docs/79) |
| `make check` | vérifie configuration et base |
| `make dev` | API + worker + frontend |
| `make demo` | la démo, avec des données fictives du jour, sur sa propre base (`jobbot_demo`) et ses propres ports (http://localhost:5200), à côté de `make dev` ; ouvre le navigateur ; Ctrl-C l'arrête |
| `make test` | tests backend (sur `jobbot_test`) et frontend |
| `make lint` | ruff, mypy, eslint |
| `make openapi` | régénère le contrat OpenAPI et les types TypeScript du frontend |
| `make check-openapi` | échoue si les types du frontend ne correspondent plus au backend |

## Réglages d'installation

L'interface renvoie ici pour ce qui se règle sur l'ordinateur qui fait tourner la plateforme, dans le fichier `.env` à la racine (créé par `make setup` à partir de `.env.example`), puis `make dev` relancé. Ne mets jamais ces valeurs dans le dépôt.

| Pour | Réglage |
|---|---|
| Créer le compte de connexion, ou changer son mot de passe | `cd backend && uv run jobbot set-password` (saisie masquée ; ferme les sessions ouvertes) |
| Lire les e-mails d'alerte | `JOBBOT_IMAP_USER`, `JOBBOT_IMAP_PASSWORD` (mot de passe d'application Gmail), `JOBBOT_IMAP_FOLDER` |
| Noter les offres et rédiger avec l'IA | `JOBBOT_ANTHROPIC_API_KEY` |
| Notifications sur le téléphone (application ntfy) | `JOBBOT_NTFY_TOPIC` : un sujet difficile à deviner, auquel tu t'abonnes dans l'application |
| Essai local sans connexion | `JOBBOT_AUTH_ENABLED=false` |

La liste complète est dans [docs/exploitation.md](docs/exploitation.md) (section Configuration).

## Organisation

```
backend/    Python 3.13 (uv) : FastAPI, SQLAlchemy, Alembic, procrastinate
frontend/   Vue 3 + Vite + TypeScript, types générés depuis l'OpenAPI du backend
docs/       cadrage, documents de version, règles de l'interface, contrat d'exploitation
data/       fichiers personnels, ignoré par git
```

L'infrastructure (conteneurs, CI, Kubernetes, Terraform, Ansible, supervision) n'est pas dans ce dépôt pour l'instant : elle se construit à partir de [docs/exploitation.md](docs/exploitation.md).

## Données personnelles

Le dépôt est public. CV, profil, offres, lettres et exports ORP restent dans `data/` et dans la base, jamais dans git ; un test le vérifie (`backend/tests/test_no_personal_data.py`).

## Licence

GPL-3.0, voir [LICENSE](LICENSE).

Les illustrations de `frontend/src/assets/illustrations/` viennent d'[unDraw](https://undraw.co) (Katerina Limpitsouni), sous la licence unDraw ; elles sont animées et préparées par `frontend/scripts/illustrations.mjs` (docs/58), sans changer leurs formes.
