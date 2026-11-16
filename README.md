# jobA1

> **Less searching. More living.**

jobA1 lit tes e-mails d'alerte, écarte les offres qui ne respectent pas tes prérequis, note les autres selon ton profil,
prépare lettre et CV, et tient le journal des candidatures pour l'ORP. **Rien ne part sans toi.**

(Nom technique : job-bot. Le paquet, la commande `jobbot` et les variables `JOBBOT_*` gardent ce nom.)

## En 3 schémas

**1. Le trajet d'une offre**

![Trajet d'une offre](docs/schemas/2-trajet-offre.png)

**2. Les pièces de la plateforme**

![Architecture](docs/schemas/1-architecture.png)

**3. Où trouver quoi dans le dépôt**

![Carte du dépôt](docs/schemas/3-carte-du-depot.png)

Les schémas sont modifiables dans Lucidchart : [architecture](https://lucid.app/lucidchart/29221eb0-ea5e-4581-bee5-66c1921f1b70/view),
[trajet](https://lucid.app/lucidchart/f32454d7-89db-4b0c-890c-c415d395a2b8/view),
[carte](https://lucid.app/lucidchart/f4cbd5de-fa98-4e08-b631-fff1d4c8ff27/view).

## Lancer en local (macOS)

```bash
brew install uv postgresql@17 && brew services start postgresql@17
make setup     # dépendances, bases, .env
make migrate   # forme de la base
make dev       # API + worker + interface
```

L'interface s'ouvre sur http://localhost:5173 et l'API sur http://127.0.0.1:8000/api/docs. `Ctrl-C` arrête tout.

| Commande | Effet |
|---|---|
| `make demo` | la démo avec des données fictives, sur http://localhost:5200 |
| `make test` | tous les tests |
| `make audits-ci` | **avant chaque push** : les mêmes contrôles que la CI (tests, types, lint, poids et son écart avec main, historique, audits ordinateur et téléphone), sur la démo lancée par `make demo` (`DEMO_URL` pour une autre adresse) |
| `make lint` | ruff, mypy, eslint |
| `make update` | met à jour (git pull, dépendances, migrations) |
| `make openapi` | régénère les types de l'interface depuis l'API |

## Réglages (fichier `.env`, jamais dans git)

| Pour | Réglage |
|---|---|
| Créer le compte ou changer le mot de passe | `cd backend && uv run jobbot set-password` |
| Lire les e-mails d'alerte | `JOBBOT_IMAP_USER`, `JOBBOT_IMAP_PASSWORD`, `JOBBOT_IMAP_FOLDER` |
| L'IA (note, lettre, assistant) | `JOBBOT_ANTHROPIC_API_KEY` |
| Les notifications sur le téléphone | `JOBBOT_NTFY_TOPIC` |

La liste complète se trouve dans [docs/exploitation.md](docs/exploitation.md).

## Limites de poids

`frontend/scripts/poids.mjs` (lancé par `npm run poids` et par `make audits-ci`) bloque la CI si le JS ou le CSS compressé d'une page dépasse sa limite. **Règle (Kevin, 16.11)** : chacune des 30 pages a ses limites de JS et de CSS, fixées une seule fois et jamais relevées ; une PR qui dépasse compense sur sa propre page ou attend, sauf décision écrite dans docs/decisions/ avec l'accord de Kevin (docs/performance.md, « Les limites par page »). js-total et css-total sont affichés, sans limite. `make audits-ci` affiche aussi l'écart de poids de la branche avec main (`frontend/scripts/poids-delta.sh`). Quand main dépasse déjà une limite, une PR qui n'ajoute rien à cette mesure passe ; seule une PR qui l'alourdit reste bloquée (`frontend/scripts/poids-ci.sh`, décision de Kevin du 16.11).

**Règle (Kevin, 15.11.2026)** : toute PR qui ajoute plus de 0,5 Ko de JS ou de CSS (gzip, total) le justifie dans sa description, avec le détail de ce qui pèse.

| Date | Limite | Avant | Après | Raison |
|---|---|---|---|---|
| 15.11.2026 | JS total (gzip) | 426 000 o | 426 700 o | dos des cartes Trier ordinateur : verdicts, étiquettes, anneau |
| 15.11.2026 | CSS total (gzip) | 117 500 o | 117 750 o | dos des cartes Trier ordinateur : verdicts, étiquettes, anneau |
| 15.11.2026 | JS total (gzip) | 426 700 o | 426 780 o | même raison : le reste, mesuré avec les PR 739 et 740 ouvertes |
| 15.11.2026 | CSS total (gzip) | 117 750 o | 117 780 o | même raison : le reste, mesuré avec les PR 739 et 740 ouvertes |
| 15.11.2026 | JS total (gzip) | 426 780 o | 428 780 o | marge pour les PR en cours : Trier, premiers pas, Google Emplois, notation manuelle |
| 16.11.2026 | JS total (gzip) | 428 780 o | 431 500 o | #764 (code jobup), #770 (recherche dans le CV) et #771 (agences de placement) ensemble, sans découpage ; mesuré : 431 252 o |
| 15.11.2026 | CSS total (gzip) | 117 780 o | 118 780 o | marge pour les PR en cours : Trier, premiers pas, Google Emplois, notation manuelle |
| 16.11.2026 | CSS total (gzip) | 118 780 o | 119 450 o | #764 (code jobup), #770 (recherche dans le CV) et #771 (agences de placement) ensemble, après l'allègement de #777 (−189 o) ; mesuré : 119 403 o |
| 16.11.2026 | toutes | — | — | limites par page (30 pages, JS et CSS, main + 5 %) ; js-total et css-total ne bloquent plus (issue #797) |

## Pour aller plus loin

Le guide de lecture de la doc se trouve dans [docs/README.md](docs/README.md).

## Données personnelles et licence

Le dépôt est public. CV, profil, offres et lettres restent dans `data/` et dans la base, jamais dans git, et un test le
vérifie. Licence GPL-3.0 ([LICENSE](LICENSE)). Les illustrations sont faites pour jobA1 (docs/67) ; seul le dessin de la page de
maintenance vient d'[unDraw](https://undraw.co).
