# 77 — La démo en ligne (version 0.63.0)

> Statut : **validé** le 2026-10-18.
> Origine : docs/72 a fait la démo (données fictives, lecture seule), `make demo` la lance sur ton ordinateur, et la revue 0.62.1 l'a rendue sûre (remplissage protégé, base en lecture seule). Il reste à la mettre **en ligne**, à une adresse que tu peux donner (dossier SAI, conseiller ORP, entretiens), sans que ton ordinateur soit allumé.

## 1. En clair : ce qu'il faut

Trois pièces, pas plus :

| Pièce | Ce que c'est | Qui |
|---|---|---|
| **Un petit serveur** | un ordinateur loué, toujours allumé, quelque part sur Internet | toi (location, paiement) |
| **Une adresse** | par exemple `demo.joba1.ch`, qui pointe vers ce serveur | toi (nom de domaine) |
| **Le paquet de démo** | tout ce qu'il faut pour que le serveur fasse tourner la démo avec une seule commande, et la remette à neuf chaque nuit | moi (dans le dépôt) |

La démo n'a **aucun secret** : ni clé d'IA, ni boîte e-mail, ni mot de passe, et rien de ta vraie plateforme. Si le serveur était compromis, il n'y aurait que des données fictives.

## 2. Où l'héberger

| Option | Prix | Pour | Contre |
|---|---|---|---|
| **Ton Mac + un tunnel** (comme ta plateforme aujourd'hui) | gratuit | rien à louer | éteinte quand ton Mac dort ; adresse du tunnel, pas la tienne |
| **Un petit serveur en Suisse** (VPS, par exemple chez Infomaniak ou Exoscale) | quelques francs par mois (à vérifier sur leur site) | toujours en ligne, ton adresse, hébergé en Suisse, tout est à toi | une location à gérer, une mise à jour à lancer après chaque version |
| **Une plateforme clé en main** (Render, Fly.io…) | gratuit limité ou quelques dollars | rien à administrer | conditions qui changent, souvent hors de Suisse, moins de contrôle |

**Je conseille le petit serveur en Suisse** : c'est le plus simple à long terme, et cohérent avec ce que jobA1 dit de lui-même (des données qui restent en Suisse). La plus petite offre suffit : 1 processeur, 1 à 2 Go de mémoire, 10 Go de disque, Linux (Debian ou Ubuntu).

## 3. Ce que je prépare : le paquet `deploy/demo/`

- **Une image** pour le serveur de jobA1 (l'API), et l'interface déjà construite.
- **Un fichier `docker-compose.yml`** qui lance tout ensemble :
  - la base PostgreSQL, invisible depuis Internet ;
  - l'API en mode démo (`JOBBOT_DEMO=true`, `JOBBOT_ENV=prod`) ;
  - **Caddy**, qui sert l'interface, relaie `/api` vers l'API, et obtient tout seul le certificat HTTPS de ton adresse ;
  - une petite tâche qui **remplit la démo au démarrage, puis chaque nuit à 4 h**, pour repartir propre et recaler les dates sur le jour.
- **Des réglages prudents** :
  - `/metrics` et la documentation de l'API ne sont pas exposés ;
  - en-têtes de sécurité (HTTPS obligatoire, pas d'intégration dans un autre site) ;
  - taille des requêtes limitée ;
  - journaux d'accès gardés 7 jours au plus, sans rien d'autre.
- **Un mode d'emploi pas à pas** (`deploy/demo/README.md`), en français simple : chaque commande à copier, et ce que tu dois voir à l'écran.

## 4. Ce que tu fais, une fois

1. Louer le serveur, et noter son adresse IP.
2. Chez ton fournisseur de domaine, faire pointer `demo.joba1.ch` (ou l'adresse choisie) vers cette IP (un enregistrement « A »).
3. Te connecter au serveur (le fournisseur explique comment), installer Docker (une commande, donnée dans le mode d'emploi).
4. Copier le dépôt sur le serveur, écrire l'adresse choisie dans un petit fichier de réglages, puis `docker compose up -d`.
5. Ouvrir l'adresse : la démo apparaît, avec le bandeau « Démo ».
6. Sur **ta vraie plateforme**, ajouter `JOBBOT_DEMO_URL=https://demo.joba1.ch` : « La plateforme » propose alors « Voir la démo ».

Je ne me connecte jamais à ton serveur, et tu n'as aucun mot de passe à me donner.

**Après chaque nouvelle version** : une commande sur le serveur (`git pull` puis `docker compose up -d --build`), écrite dans le mode d'emploi.

## 5. Ce qu'on ne fait pas

- **Pas d'IA dans la démo**, comme prévu au docs/72 : une adresse publique attirerait les abus, et chaque appel coûte.
- **Pas de statistiques de visite** : la démo ne trace personne.
- **Pas de référencement par les moteurs de recherche** : la démo dit aux moteurs de ne pas l'indexer (`noindex`), pour que des offres d'emploi fictives n'apparaissent pas dans Google. Tu donnes le lien à qui tu veux.
- **Pas de surveillance automatique** : si la démo tombe, tu le verras en l'ouvrant ; le mode d'emploi dit comment la relancer.

## 6. Ce qui change dans le code

| Où | Quoi |
|---|---|
| `deploy/demo/` | `Dockerfile`, `docker-compose.yml`, `Caddyfile`, réglages d'exemple, `README.md` |
| `frontend/index.html` | `noindex` quand l'interface est construite pour la démo |
| `docs/exploitation.md` | la démo en ligne, ses réglages et sa mise à jour |
| `Makefile` | `make demo-image` : construit l'image et lance la démo dans Docker sur ton ordinateur, comme sur le serveur, pour l'essayer avant |

Pas de migration, rien ne change sur ta vraie plateforme.

## 7. Livraison et vérification

Une PR, **0.63.0**.

Vérifié sur mon ordinateur avec Docker, exactement comme sur le serveur :
- tout démarre avec une commande ;
- la démo répond et se remplit ;
- le remplissage de nuit tourne (je l'avance pour l'essai) ;
- `/metrics` et la documentation de l'API répondent 404 depuis l'extérieur ;
- une écriture est refusée ;
- le parcours de toutes les pages ne fait aucune erreur.

Le certificat HTTPS ne s'essaie qu'avec la vraie adresse : c'est la seule partie que tu verras en premier.

## Points à valider

1. **Un petit serveur en Suisse**, loué par toi (§2).
2. **L'adresse** : `demo.joba1.ch`, ou une autre (as-tu déjà un nom de domaine ?) (§1, §4).
3. **Le paquet `deploy/demo/`** : Docker, Caddy pour le HTTPS, remise à neuf chaque nuit à 4 h (§3).
4. **Pas d'IA, pas de statistiques, pas de référencement** (§5).
5. **Une PR 0.63.0**, sans migration (§7).

## Écarts avec le cadrage

- **`noindex` par le site, pas par l'interface** : Caddy envoie `X-Robots-Tag: noindex, nofollow` sur toutes les pages et sert un `robots.txt` qui interdit tout. Même effet, sans construire une interface à part pour la démo ; `frontend/index.html` ne change pas.
- **La remise à neuf de nuit** tourne dans son propre conteneur (`nightly`), plutôt que dans une tâche planifiée du serveur : rien à régler hors de Docker. La démo est aussi remplie à chaque démarrage.
- **Un `.dockerignore` à la racine du dépôt** : la construction n'emporte ni `data/`, ni `.env`, ni `node_modules`, même lancée depuis ton dossier de travail.
- **Le serveur de jobA1 tourne sans droits** (utilisateur dédié, qui n'écrit que dans `/data`) ; seul le site publie des ports (80 et 443).
- **Le nom de domaine** n'était pas encore choisi : `demo.joba1.ch` sert d'exemple dans `.env.example`, à remplacer à l'étape 7 du mode d'emploi.
- **Vérifié dans Docker sur mon ordinateur**, comme sur le serveur (`make demo-image`) :
  - les quatre services démarrent et sont en bonne santé ;
  - la démo répond et se remplit ;
  - une écriture est refusée (403) ;
  - `/metrics`, `/readyz`, `/version` et la documentation de l'API répondent 404 ;
  - les en-têtes et `robots.txt` sont en place ;
  - le parcours de toutes les pages fait 175 appels, sans aucune erreur ;
  - la remise à neuf tourne à la main, et le calcul de la prochaine (4 h) est juste ;
  - l'image ne contient ni `.env` ni données ;
  - la base n'a aucun port publié.

  Seul le certificat HTTPS ne s'essaie qu'avec la vraie adresse.

