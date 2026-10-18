# jobA1

> **Less searching. More living.** (anciennement job-bot : le dépôt, le paquet `jobbot`, la commande `jobbot` et les variables `JOBBOT_*` gardent leur nom technique.)

Assistant de recherche d'emploi : il collecte les offres reçues par alerte e-mail (jobup et Indeed, les autres sites lus par l'IA), écarte celles qui ne respectent pas tes prérequis, note les autres par rapport à ton profil, prépare lettre et CV, et tient le journal des candidatures exportable pour l'ORP. Tu valides chaque envoi.

- Cadrage : [docs/01-cadrage.md](docs/01-cadrage.md)
- Version en cours : [docs/71-extension-publiee.md](docs/71-extension-publiee.md) (0.58.1)
- Règles de l'interface (illustrations, mouvement, clic) : [docs/interface.md](docs/interface.md)
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
| 0.36.0 | Formations : cartes calmes (3 lignes, « Suivre » ou état + « Gérer »), suivi dans le panneau latéral en trois sections | livrée |
| 0.37.0 | Fiche d'une offre : deux boutons et « ⋯ », sections Pour toi, À savoir (✓ ! ✗), Entreprise, Annonce repliée | livrée |
| 0.38.0 | Suivi : cartes calmes (statut, une seule prochaine étape), panneau d'une candidature en cinq sections, ouvert aussi depuis la liste | livrée |
| 0.39.0 | Préparer une candidature : onglets ① Lettre ② CV ③ Postuler, l'offre à côté de la lettre, PDF / Word sur une ligne | livrée |
| 0.40.0 | Réglages : une rubrique à la fois (six), sites et sources en lignes calmes avec panneau, seuils dits en clair | livrée |
| 0.41.0 | Mon parcours : un encart de dépôt, documents en lignes calmes, cartes de bloc calmes, le bloc dans le panneau latéral | livrée |
| 0.41.1 | Revue : menu « ⋯ » commun (Échap ne ferme que le menu), une classe de section, 61 règles CSS inutiles retirées | livrée |
| 0.41.2 | Téléphone, revue de 0.36 à 0.41 : contexte de la préparation, objet de la lettre, texte aligné, étapes de Postuler, filtres du parcours | livrée |
| 0.42.0 | L'assistant propose, tu confirmes : trier une offre, la signaler expirée, changer le statut d'une candidature ; « Annuler » ensuite | livrée |
| 0.43.0 | Plus de « ? » : l'assistant explique (« Comment ça marche ici ? »), 14 descriptions au survol de 3 s pour le moins évident | livrée |
| 0.44.0 | Aujourd'hui en tableau de bord : quatre tuiles à pictogramme, la semaine en barres, les offres en tableau, la jauge de l'objectif ORP | livrée |
| 0.45.0 | Le Bilan dans le style du tableau de bord : quatre tuiles, le parcours en barres, candidatures et réponses par mois, comparaisons en barres, résumé ORP visible | livrée |
| 0.45.1 | Revue : guide de l'assistant à jour (Aujourd'hui, Bilan), suggestions du Bilan, ménage de la feuille de style | livrée |
| 0.45.2 | Clic direct : l'élément entier ouvre son contenu avec un survol, plus de « › » ni de « Continuer › » | livrée |
| 0.46.0 | Illustrations animées : prise en main, chargements, rédaction par l'IA, fichiers en préparation | livrée |
| 0.47.0 | Micro-interactions : appui, survol, sélecteurs, coches, copier, fichiers sur le bouton, étapes de l'IA ; illustrations réduites aux pages vides | livrée |
| 0.47.1 | Illustrations en grand sur ordinateur (réussites, prise en main, formulaires, pages vides), retours d'actions, entrée des chiffres et des barres | livrée |
| 0.47.2 | Illustrations à côté des cartes et plus grandes ; Engagement en grand par-dessus la page | livrée |
| 0.48.0 | Carte de réussite qui vient devant, transition des pages qui chargent, images à côté des blocs trop larges | livrée |
| 0.48.1 | Illustrations à leur place : retirées des Réglages, de Profil, de Préparer et d'Aujourd'hui ; une seule famille aux couleurs de l'interface | livrée |
| 0.48.2 | Des blocs à leur taille : frise des étapes, ce que donnent tes critères, dépense de l'IA, Réglages à la largeur de lecture ; transition plus lente | livrée |
| 0.48.3 | Revue : l'assistant connaît tes critères et la dépense de l'IA, ménage de la feuille de style, téléphone vérifié (sélecteurs, barres des critères, guides, page introuvable) | livrée |
| 0.50.0 | Chaque donnée appartient à un compte, séparé par la base ; tâches compte par compte ; test des deux comptes sur toutes les routes | livrée |
| 0.51.0 | Comptes invités : invitation et nouveau mot de passe par lien, suspension, suppression ; rubrique Plateforme ; plafond de l'IA par compte et total ; notifications à soi | livrée |
| 0.52.0 | Une adresse de réception par compte, collecte rangée par destinataire, e-mails « confirmez votre alerte » dans Alertes, pause des sites par compte | livrée |
| 0.53.0 | Tes données : page publique (ce qui est gardé, ce qui part à l'IA, tes mentions), export complet du compte, suppression de son compte | livrée |
| 0.53.1 | Page de connexion en deux moitiés : illustration à gauche, connexion à droite ; Google, Apple, Microsoft présentés (pas encore branchés) | livrée |
| 0.54.0 | L'accueil après la première connexion, façon Duolingo : sept questions en cartes, chaque réponse règle la plateforme, puis la création des alertes | livrée |
| 0.55.0 | Les illustrations de jobA1 : des images générées, plus grandes, remplacent les dessins unDraw (gardés en réserve) ; sans connexion, la présentation de la plateforme à la place des Actualités | livrée |
| 0.55.1 | Les pages qui chargent gardent leurs dessins animés d'avant (Aujourd'hui, Offres, Suivi, Bilan, Alertes, Actualités, Formations) | livrée |
| 0.55.2 | La connexion illustrée par la ville et le bureau, l'image entière remplissant la moitié gauche | livrée |
| 0.55.3 | En sombre, la connexion joue la vidéo du soir qui tombe, puis l'image du soir | livrée |
| 0.55.4 | La connexion sans voile : la phrase en haut à gauche, la lune visible, les couleurs qui suivent le ciel | livrée |
| 0.55.5 | La connexion plus nette, la phrase qui blanchit plus tard | livrée |
| 0.56.0 | Le titre animé : une fois connecté, un personnage à la place du « 1 », qui change chaque heure | livrée |
| 0.56.1 | Revue des comptes : les Actualités fermées sans connexion, liens d'invitation verrouillés, identifiant unique, journal des tâches réservé, export complet | livrée |
| 0.56.2 | Revue, suite : l'assistant à jour (`assistant-v6`), le ménage des illustrations, le focus de l'accueil, le test instable stabilisé | livrée |
| 0.57.0 | L'extension remplit la saisie Job-Room d'une candidature (tu vérifies et sauvegardes) ; « déclarée dans Job-Room » suivi pour chaque candidature | livrée |
| 0.57.1 | Job-Room dans Firefox : le remplissage tourne dans la page, les valeurs tapées sont prises ; chaque valeur relue après la saisie | livrée |
| 0.58.0 | L'extension prête pour la boutique de Mozilla : relier en un clic (« Relier ce navigateur »), onglet d'accueil à l'installation, paquet, fiche et politique de confidentialité | livrée |
| 0.58.1 | Premier essai réel : le panneau tient dans sa largeur, les champs facultatifs de Job-Room ne sont plus signalés, essai par le paquet (zip) | livrée |

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
docs/       cadrage, documents de version, règles de l'interface, contrat d'exploitation
data/       fichiers personnels, ignoré par git
```

L'infrastructure (conteneurs, CI, Kubernetes, Terraform, Ansible, supervision) n'est pas dans ce dépôt pour l'instant : elle se construit à partir de [docs/exploitation.md](docs/exploitation.md).

## Données personnelles

Le dépôt est public. CV, profil, offres, lettres et exports ORP restent dans `data/` et dans la base, jamais dans git ; un test le vérifie (`backend/tests/test_no_personal_data.py`).

## Licence

GPL-3.0, voir [LICENSE](LICENSE).

Les illustrations de `frontend/src/assets/illustrations/` viennent d'[unDraw](https://undraw.co) (Katerina Limpitsouni), sous la licence unDraw ; elles sont animées et préparées par `frontend/scripts/illustrations.mjs` (docs/58), sans changer leurs formes.
