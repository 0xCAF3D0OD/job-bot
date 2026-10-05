# job-bot

Assistant de recherche d'emploi : il collecte les offres reçues par alerte e-mail (jobup, Indeed, Job-Room), écarte celles qui ne respectent pas tes prérequis, note les autres par rapport à ton profil, prépare lettre et CV, et tient le journal des candidatures exportable pour l'ORP. Tu valides chaque envoi.

- Cadrage : [docs/01-cadrage.md](docs/01-cadrage.md)
- Version en cours : [docs/03-collecte-gmail.md](docs/03-collecte-gmail.md) (0.2.0)
- Contrat d'exploitation, pour l'infrastructure : [docs/exploitation.md](docs/exploitation.md)

## Versions

| Version | Contenu | État |
|---|---|---|
| 0.1.0 | Squelette : API, worker, base, page État | livrée |
| 0.2.0 | Collecte Gmail, journal des recherches, dédoublonnage | collecte, analyseurs Indeed et jobup livrés ; Job-Room à venir |
| 0.3.0 | Documents, blocs de profil, prérequis et réglages, filtre | livrée |
| 0.3.1 | Lien de candidature et texte complet des offres jobup | livrée |
| 0.4.0 | Page Offres avec filtres, note et résumé IA, notifications | livrée |
| 0.4.1 | Propositions de blocs de profil par l'IA depuis un document | livrée |
| 0.5.0 | Suivi des candidatures (a), lettre (b) et CV adapté (c) | livrée |
| 0.6.0 | Export ORP (a) et rappels (b) | livrée |
| 0.6.1 | Offres expirées (a), prise en main (b), filtres au choix (c) | livrée |
| 0.7.0 | Expiration signalée (a), mots-clés (b), sites ajoutés : jobs.ch, LinkedIn (c) | en cours (a) |
| 0.7.1 | Détail allégé et adresse de l'annonce (a), registre IDE (b) | livrée |
| 0.7.2 | Adresse cherchée sur Internet par l'IA | en cours |

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
| `make check` | vérifie configuration et base |
| `make dev` | API + worker + frontend |
| `make test` | tests backend (sur `jobbot_test`) et frontend |
| `make lint` | ruff, mypy, eslint |
| `make openapi` | régénère le contrat OpenAPI et les types TypeScript du frontend |
| `make check-openapi` | échoue si les types du frontend ne correspondent plus au backend |

## Organisation

```
backend/    Python 3.13 (uv) : FastAPI, SQLAlchemy, Alembic, procrastinate
frontend/   Vue 3 + Vite + TypeScript, types générés depuis l'OpenAPI du backend
docs/       cadrage, documents de version, contrat d'exploitation
data/       fichiers personnels, ignoré par git
```

L'infrastructure (conteneurs, CI, Kubernetes, Terraform, Ansible, supervision) n'est pas dans ce dépôt pour l'instant : elle se construit à partir de [docs/exploitation.md](docs/exploitation.md).

## Données personnelles

Le dépôt est public. CV, profil, offres, lettres et exports ORP restent dans `data/` et dans la base, jamais dans git ; un test le vérifie (`backend/tests/test_no_personal_data.py`).

## Licence

GPL-3.0, voir [LICENSE](LICENSE).
