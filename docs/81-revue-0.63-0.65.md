# 81 — Revue après 0.63 à 0.65.1 (version 0.65.2)

> Statut : **validé** le 2026-10-19.
> Origine : huit versions depuis la dernière revue (docs/76) : la démo en ligne (0.63), l'étanchéité des comptes (0.64.0 à 0.64.2), la page de maintenance (0.65.0, 0.65.1). Relecture du serveur, de l'interface, de la documentation et des tests, en lisant le code. Chaque constat a été vérifié dans le code, avec son fichier et sa ligne.

## 1. En clair

Rien de grave : pas de faille, pas de perte de données. Deux défauts que tu pourrais voir, des oublis dans la documentation, un peu de ménage.

## 2. Ce qui se voit (à corriger d'abord)

| Gravité | Constat | Correction |
|---|---|---|
| **Moyenne** | **Ouvrir Actualités pendant une maintenance en lecture seule affiche « tu ne peux pas encore enregistrer ».** La page note toute seule la visite (`POST /api/news/seen`, `NewsView.vue:137`), et cette écriture est refusée pendant la maintenance. C'est le même défaut que celui de la démo corrigé en 0.63.2. | Une écriture que la page fait d'elle-même, sans clic, ne déclenche jamais le message : elle est simplement abandonnée pendant la maintenance. Test. |
| **Moyenne** | **Après la page d'attente, le curseur est perdu.** Quand la page d'attente s'en va, le focus ne revient pas là où il était (`MaintenanceOverlay.vue:20-27`) : au clavier, ou avec un lecteur d'écran, il faut revenir à la main dans la lettre qu'on écrivait. | Retenir l'élément actif à l'ouverture et y revenir à la fermeture. Test. |
| Basse | **Base pas à jour : la connexion passe avant la maintenance.** Le contrôle « base pas encore à jour » se fait après la reconnaissance de la session (`api/app.py`, ordre des intermédiaires). Une future migration qui toucherait aux sessions répondrait donc par une erreur au lieu de la page d'attente. | Le contrôle « base pas à jour » passe en premier, avant la connexion. La maintenance annoncée reste après, puisqu'elle doit savoir si c'est toi. |
| Basse | **Le worker ne s'arrête pas quand la base n'est pas à jour.** Il s'arrête pendant une maintenance annoncée, mais pas entre `git pull` et `jobbot migrate` (`maintenance.py`, `worker_paused`). Avec `make update`, ce moment n'existe pas. À la main, il produirait des tâches en échec. | Les tâches attendent aussi tant que la base n'est pas à jour, comme l'API. |

## 3. La documentation

| Constat | Correction |
|---|---|
| Le README marque encore la 0.65.1 « en cours ». | « livrée ». |
| `docs/exploitation.md:233` liste comme ouvertes sans connexion les Actualités (fermées depuis 0.56.1) et `/readyz`, `/metrics`, `/version` (réservées depuis 0.64.2). Il oublie `GET /api/privacy` et `GET /api/maintenance`. | La liste exacte, reprise du code (`auth/middleware.py`, `PUBLIC_READ`). |
| `jobbot maintenance` manque dans le tableau des commandes de `docs/exploitation.md` ; `make update` manque dans celui du README. | Les ajouter. |
| `docs/exploitation.md:244` : « toute écriture refusée . », espace en trop. | Corriger. |
| `accounts.py:80` dit que les fonctions des jetons viennent de la migration 0046. Elles ont été refaites en 0053 et 0056. | « migrations 0046, 0053 et 0056 ». |

## 4. Vérifié sans problème

- **Les trois accès à la base** : l'API en `jobbot_app` et le worker en `jobbot_worker` sur ta plateforme. La démo refuse de démarrer en administrateur ; cela a joué pendant les essais de la 0.65.1.
- **La séparation des comptes** : le test de toutes les routes avec un second compte, les règles par famille de tables, les liens entre comptes refusés par la base, la vraie file des tâches.
- **La maintenance** : les trois cas, toi qui passes, la lecture seule, les tâches en pause, le dessin immobile si « réduire les animations ».
- **La démo** : le paquet Docker, la remise à neuf de nuit, les adresses techniques fermées, la réponse « en maintenance » de Caddy.
- **Les textes** : tutoiement, ton, aucun jargon nouveau dans l'interface.
- **Les bibliothèques** : `pip-audit` et `npm audit` sans faille connue (audit du lundi sur GitHub).

## 5. Livraison

Une PR, **0.65.2**, sans migration :
- les quatre corrections du §2, avec leurs tests ;
- la documentation du §3.

Vérifié : tous les tests, la lecture seule sur une démo de brouillon (Actualités sans message), et la page d'attente au clavier.

## Points à valider

1. **Les quatre corrections** du §2.
2. **La documentation** remise à jour (§3).
3. **Une PR 0.65.2**, sans migration (§5).

## Écarts avec le cadrage (0.65.2)

- **Une écriture que la page fait d'elle-même** porte une marque (`X-Jobbot-Background`). Pendant une maintenance en lecture seule, son refus est abandonné sans message. Aujourd'hui, c'est seulement la visite des Actualités. Une écriture faite par un clic garde son message.
- **Le contrôle « base pas à jour »** passe avant la connexion. Celui de la maintenance annoncée reste après, puisqu'il doit savoir si c'est toi. Les deux lisent le même état, relu au plus toutes les 5 secondes.
- **Vérifié** :
  - 500 tests serveur, dont 1 nouveau : base pas à jour, même quand lire la session échouerait ; et le worker en pause. 296 tests de l'interface, dont 1 nouveau (l'écriture de la page elle-même), plus le curseur retrouvé dans le test de la page d'attente.
  - Sur une instance de brouillon, un invité connecté ouvre les Actualités pendant une maintenance en lecture seule : la visite est refusée (503) sans aucun message, et le bandeau reste.
