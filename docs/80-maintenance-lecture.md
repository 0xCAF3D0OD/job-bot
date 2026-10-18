# 80 — La maintenance en lecture seule, et son dessin animé (version 0.65.1)

> Statut : **validé** le 2026-10-18.
> Origine : ta question du 2026-10-18 après la 0.65.0 : les personnes peuvent-elles continuer d'utiliser la plateforme pendant une maintenance ? Aujourd'hui, non : la page d'attente bloque tout. Et tu veux sur cette page le dessin unDraw animé de la maintenance (`undraw_maintenance_4unj.svg`, version animée de ton dossier `illustration1/animees`).

## 1. En clair

Deux sortes de maintenance annoncée, au lieu d'une :

| Commande | Les invités | Toi |
|---|---|---|
| `jobbot maintenance on --lecture "message"` | **continuent de consulter** : offres, candidatures, documents, actualités… Un bandeau dit « Maintenance : tu peux consulter, pas encore enregistrer ». Une action qui enregistre (bouton, formulaire) est refusée, avec ton message, sans rien perdre de ce qui était écrit. | tout fonctionne, avec le rappel en haut de l'écran |
| `jobbot maintenance on "message"` (complète, comme aujourd'hui) | la page d'attente | tout fonctionne, avec le rappel |

**Quand choisir laquelle** :
- **en lecture seule** pour une opération qui ne touche pas la structure de la base : vérifier ou corriger des données à la main, changer un réglage, faire une sauvegarde tranquille ;
- **complète** pour une mise à jour du schéma de la base (`make update` la garde) ou tout ce qui pourrait montrer des données à moitié changées.

Les deux cas automatiques ne changent pas : l'API qui redémarre et la base pas encore à jour montrent toujours la page d'attente, puisqu'il n'y a alors rien de fiable à lire.

## 2. La page d'attente avec le dessin animé

Le dessin d'aujourd'hui (la personne qui lit, de la famille des images de jobA1) est remplacé par le **dessin unDraw de la maintenance** : une personne qui travaille sur des serveurs, avec une barre qui se remplit et des voyants qui clignotent.

- Préparé comme les dessins des pages qui chargent (`scripts/illustrations-undraw.mjs`), donc **aux couleurs de jobA1**, en clair comme en sombre.
- Il **bouge tant que l'attente dure**. C'est une exception aux règles de l'interface, à écrire dans `docs/interface.md`, comme celle de l'IA qui rédige : une vraie attente, où le mouvement dit que quelque chose se passe. Les autres dessins unDraw ne jouent qu'une fois.
- **Immobile** si « réduire les animations » est demandé.
- 300 px sur ordinateur, 200 sur téléphone, à côté du texte, comme aujourd'hui.

## 3. Comment

**Côté serveur** :
- La maintenance annoncée retient son mode : `lecture` ou `complete`. `jobbot maintenance status` l'affiche.
- En lecture seule, pour un invité :
  - les lectures (GET) passent ;
  - toute écriture (POST, PUT, PATCH, DELETE) reçoit 503 « maintenance, lecture seule » avec ton message ;
  - la connexion reste ouverte.
- **Les tâches de fond s'arrêtent** pendant une maintenance annoncée, quel que soit le mode : sinon la collecte ou la notation écriraient quand même. Les tâches planifiées sont sautées, et le journal le dit. Une tâche que tu lances toi-même passe. Ce point corrige aussi la 0.65.0, où le worker continuait pendant une maintenance complète.
- `GET /api/maintenance` dit aussi le mode.

**Côté interface** :
- **En lecture seule** :
  - pas de page d'attente : un bandeau en haut de l'écran pour les invités ;
  - une action refusée affiche un message (comme dans la démo) ;
  - le bandeau disparaît tout seul quand la maintenance est levée : vérifié toutes les 30 secondes tant qu'il est affiché.
- **Complète** : la page d'attente, avec le nouveau dessin.

## 4. Ce qu'on ne fait pas

- **Pas de lecture seule pendant une mise à jour du schéma** : `make update` garde la maintenance complète.
- **Les lectures qui notent quelque chose en passant** passent comme les autres : la date d'un export, le catalogue des formations. Elles sont rares et sans danger pour une maintenance en lecture seule. Pour tout bloquer, la maintenance complète existe.
- **Pas de lecture seule automatique** quand l'API redémarre : il n'y a alors rien à lire.

## 5. Livraison

Une PR, **0.65.1**, sans migration : le mode va dans le réglage `maintenance` qui existe déjà.

Ce qui sera vérifié :
- **Tests serveur** :
  - en lecture seule, un invité lit mais n'écrit pas, et toi tu écris ;
  - les tâches planifiées sont sautées, la tienne passe ;
  - le mode complet est inchangé.
- **Tests de l'interface** : le bandeau, le message d'une action refusée, la page d'attente avec le dessin, immobile si « réduire les animations ».
- **Captures** sur ordinateur et téléphone, en clair et en sombre : le bandeau en lecture seule, et la page d'attente avec le dessin.

## Points à valider

1. **Deux modes** : `--lecture` (les invités consultent) et complet (la page d'attente), au choix à chaque maintenance (§1).
2. **Le dessin unDraw animé de la maintenance** sur la page d'attente, à la place de l'image actuelle. Il bouge tant que l'attente dure ; c'est une exception écrite aux règles de l'interface (§2).
3. **Les tâches de fond en pause** pendant toute maintenance annoncée, sauf celles que tu lances (§3).
4. **Les lectures qui notent quelque chose en passant** restent permises en lecture seule (§4).
5. **Une PR 0.65.1**, sans migration (§5).

## Écarts avec le cadrage

- **Le signe de vie du worker continue** pendant une maintenance. S'il s'arrêtait, l'état de la plateforme dirait que le worker est tombé. Il n'écrit que dans le journal des tâches.
- **`jobbot run-job` passe toujours** : c'est une commande que tu lances toi-même.
- **Dans la démo**, une écriture est déjà refusée par la démo, avant la maintenance : son message reste celui de la démo. Le bandeau de la lecture seule s'affiche quand même.
- **Le bandeau** reprend ton message s'il y en a un. Une écriture refusée l'ajoute aussi à son message, qui s'affiche quelques secondes en bas de l'écran.
- **Le dessin** prend les couleurs de jobA1 comme les dessins des pages qui chargent : le personnage et les serveurs suivent le thème, en sombre aussi.
- **Vérifié** :
  - 499 tests serveur, dont 2 nouveaux : la lecture seule, et la vraie file des tâches où seule la tâche de l'exploitant passe. 295 tests de l'interface, dont 2 nouveaux : le bandeau et l'écriture refusée, puis le dessin sur la page d'attente.
  - Sur une démo de brouillon :
    - en lecture seule, le bandeau s'affiche et pas la page d'attente ;
    - en maintenance complète, la page d'attente s'affiche avec le dessin animé ;
    - l'animation est arrêtée si « réduire les animations » est demandé ;
    - quand la maintenance est levée, la page d'attente s'en va ;
    - captures sur ordinateur et sur téléphone, en clair et en sombre.
  - En passant, le garde-fou de la 0.64.0 a bien joué : la démo, lancée par erreur avec l'adresse d'un administrateur, a refusé de démarrer.
