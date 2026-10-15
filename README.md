# jobA1

> **Less searching. More living.** (anciennement job-bot : le dépôt, le paquet `jobbot`, la commande `jobbot` et les variables `JOBBOT_*` gardent leur nom technique.)

Assistant de recherche d'emploi : il collecte les offres reçues par alerte e-mail (jobup et Indeed, les autres sites lus par l'IA), écarte celles qui ne respectent pas tes prérequis, note les autres par rapport à ton profil, prépare lettre et CV, et tient le journal des candidatures exportable pour l'ORP. Tu valides chaque envoi.

- Cadrage : [docs/01-cadrage.md](docs/01-cadrage.md)
- Version en cours : [docs/43-revue-pages.md](docs/43-revue-pages.md) (0.35.0)
- Contrat d'exploitation, pour l'infrastructure : [docs/exploitation.md](docs/exploitation.md)

## Versions

| Version | Contenu | État |
|---|---|---|
| 0.1.0 | Squelette : API, worker, base, page État | livrée |
| 0.2.0 | Collecte Gmail, journal des recherches, dédoublonnage | livrée (analyseurs jobup et Indeed) ; Job-Room : pas d'analyseur dédié, présent en pause dans les sites (docs/11) |
| 0.3.0 | Documents, blocs de profil, prérequis et réglages, filtre | livrée |
| 0.3.1 | Lien de candidature et texte complet des offres jobup | livrée |
| 0.4.0 | Page Offres avec filtres, note et résumé IA, notifications | livrée |
| 0.4.1 | Propositions de blocs de profil par l'IA depuis un document | livrée |
| 0.5.0 | Suivi des candidatures (a), lettre (b) et CV adapté (c) | livrée |
| 0.6.0 | Export ORP (a) et rappels (b) | livrée |
| 0.6.1 | Offres expirées (a), prise en main (b), filtres au choix (c) | livrée |
| 0.7.0 | Expiration signalée (a), mots-clés (b), sites ajoutés : jobs.ch, LinkedIn (c) | livrée |
| 0.7.1 | Détail allégé et adresse de l'annonce (a), registre IDE (b) | livrée |
| 0.7.2 | Adresse cherchée sur Internet par l'IA | livrée |
| 0.7.3 | Postuler depuis la préparation, lien de candidature pour l'ORP | livrée |
| 0.7.4 | Page Offres (transition, tri), logos des entreprises | livrée |
| 0.8.0 | Cloche des alertes (a), Actualités (b) | livrée |
| 0.9.0 | Actualités ciblées (a), sources suggérées et veilles (b), formations (c) | livrée |
| 0.10.0 | Profils d'essai : Actualités (a), Formations (b) | livrée |
| 0.11.0 | Connexion (a), Candidatures et ORP réunies (b) | livrée |
| 0.12.0 | Navigation par catégories : menu et rubrique Candidatures (a), Aujourd'hui et Réglages (b) | livrée |
| 0.13.0 | Mes alertes (a), Voir l'offre chez l'employeur (b) | livrée |
| 0.14.0 | Simplifier : textes et « Comment ça marche » (a), Alertes (b), offre, ORP, Réglages, Profil (c) | livrée |
| 0.15.0 | Suivi et preuves ORP en un onglet, en calendrier | livrée |
| 0.16.0 | Retour d'entretien : formulaire (a), enseignements et préparation (b) | livrée |
| 0.17.0 | Assistant : discussion et lecture des données (a), contexte de la page et raccourcis (b) | livrée |
| 0.18.0 | Remplir le formulaire de l'employeur : PDF et fiche à copier (a), extension du navigateur (b) | livrée |
| 0.19.0 | Télétravail : repérage, règle et filtre (a), sites d'offres à distance (b) | livrée |
| 0.20.0 | Filtres des offres en cartes, courbe des notes | livrée |
| 0.21.0 | Accessibilité : contraste, couleur seule, zones de clic | livrée |
| 0.22.0 | Une action principale par page (a), aides visibles (b) | livrée |
| 0.23.0 | Repérer les offres douteuses : doublons, annonces permanentes, employeur caché, arnaques | livrée |
| 0.24.0 | Contacts dans l'entreprise : recherches LinkedIn déjà remplies, premier message rédigé par l'IA, suivi des prises de contact et relance | livrée |
| 0.25.0 | Alléger la plateforme : bulle temporaire, lignes dépliables, panneau latéral, pages compactes, aides derrière « ? », Actualités en page journal | livrée |
| 0.26.0 | La plateforme sur téléphone : menu burger, rien ne déborde, action principale en bas, écrans plein écran, écran d'accueil | livrée |
| 0.27.0 | Téléphone : pages longues raccourcies (Formations en liste, Réglages en lignes dépliables, Aujourd'hui l'essentiel d'abord) | livrée |
| 0.28.0 | Actualités en modules à la manière de RTS : en tête, second rang, lignes à vignette ; format téléphone | livrée |
| 0.29.0 | Téléphone : Candidatures et Profil (en-tête compact, offres en lignes, « Filtrer » en carte, Suivi sur une ligne, onglets courts) | livrée |
| 0.30.0 | Formations : une formation terminée entre dans ton profil (a), demande de financement à l'ORP (b) | livrée |
| 0.31.0 | Relancer une candidature : message rédigé (ou modèle), messagerie, date de relance, « Sans réponse » après 14 jours | livrée |
| 0.32.0 | Candidatures spontanées : sans annonce, préparées comme une offre (lettre adaptée, CV, adresse au registre), ligne ORP habituelle | livrée |
| 0.33.0 | Tes dates dans ton agenda : fichier par entretien, abonnement (entretiens, suites, remise ORP, relances) | livrée |
| 0.33.1 | Revue 0.24 à 0.33 : corrections (spontanée expirée, Échap, cloche, relances, agenda, IA indisponible…) | livrée |
| 0.34.0 | Bilan : ce qui donne des réponses (source, note, contact, relance), parcours, résumé pour le rendez-vous ORP | livrée |
| 0.35.0 | Revue page par page : Aujourd'hui par urgence, Actualités emploi / économie, un en-tête et une largeur, vrais pluriels, alignements | livrée |

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
docs/       cadrage, documents de version, contrat d'exploitation
data/       fichiers personnels, ignoré par git
```

L'infrastructure (conteneurs, CI, Kubernetes, Terraform, Ansible, supervision) n'est pas dans ce dépôt pour l'instant : elle se construit à partir de [docs/exploitation.md](docs/exploitation.md).

## Données personnelles

Le dépôt est public. CV, profil, offres, lettres et exports ORP restent dans `data/` et dans la base, jamais dans git ; un test le vérifie (`backend/tests/test_no_personal_data.py`).

## Licence

GPL-3.0, voir [LICENSE](LICENSE).
