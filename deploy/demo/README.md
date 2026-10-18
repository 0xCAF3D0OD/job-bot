# La démo en ligne de jobA1

Ce dossier fait tourner la **démo publique** de jobA1 sur un serveur : des données fictives (« Camille Exemple »), en lecture seule, remises à neuf chaque nuit à 4 h. Pourquoi et comment : [docs/77](../../docs/77-demo-en-ligne.md).

La démo n'a **aucun secret** : ni clé d'IA, ni boîte e-mail, ni mot de passe, et rien de ta vraie plateforme.

## Ce qu'il te faut

- Un petit serveur Linux (Debian 12 ou Ubuntu 24.04), la plus petite offre suffit : 1 processeur, 1 à 2 Go de mémoire, 10 Go de disque.
- Une adresse, par exemple `demo.joba1.ch`.

## Mise en ligne (une fois)

1. **Loue le serveur** et note son adresse IP (le fournisseur l'affiche).
2. **Fais pointer l'adresse vers le serveur** : chez ton fournisseur de nom de domaine, dans la **zone DNS** de ton domaine (par exemple `joba1.ch`), ajoute un enregistrement **A** : source `demo`, cible l'adresse IP du serveur. `demo.joba1.ch` est un **sous-domaine** : il n'y a rien à acheter de plus que `joba1.ch`. Il faut parfois quelques minutes pour que ce soit pris en compte ; depuis ton ordinateur, `dig +short demo.joba1.ch` doit afficher l'IP du serveur.

   Sans nom de domaine, pour un premier essai : l'adresse `IP-AVEC-DES-TIRETS.sslip.io` (par exemple `83-166-1-2.sslip.io`) pointe d'elle-même vers ton serveur, HTTPS compris.
3. **Ouvre les ports 80 et 443** du serveur, s'il a un pare-feu (souvent dans le panneau du fournisseur). Rien d'autre n'a besoin d'être ouvert.
4. **Connecte-toi au serveur**, comme le fournisseur l'explique (si ton utilisateur n'est pas `root`, mets `sudo` devant les commandes `apt-get` et `docker` qui suivent), par exemple :

   ```bash
   ssh root@ADRESSE_IP
   ```

5. **Installe Docker et git** (script officiel de Docker) :

   ```bash
   apt-get update && apt-get install -y git curl && curl -fsSL https://get.docker.com | sh
   ```

6. **Récupère jobA1** :

   ```bash
   git clone https://github.com/0xCAF3D0OD/job-bot.git && cd job-bot/deploy/demo
   ```

7. **Écris l'adresse de la démo** :

   ```bash
   cp .env.example .env && nano .env
   ```

   Remplace `demo.joba1.ch` par ton adresse, aux deux endroits ; enregistre avec Ctrl-O, Entrée, puis quitte avec Ctrl-X.

8. **Lance la démo** (5 à 10 minutes la première fois, le temps de tout construire) :

   ```bash
   docker compose up -d --build --wait
   ```

   À la fin, `docker compose ps` montre les quatre services : `db` et `api` « Up … (healthy) », `nightly` et `web` simplement « Up » (ils n'ont pas de contrôle de santé, c'est normal). Seul `web` publie des ports (80 et 443).

9. **Ouvre l'adresse** dans ton navigateur, en `https://` : la démo apparaît, avec le bandeau « Démo » en haut. Le certificat HTTPS est obtenu tout seul à la première visite (quelques secondes). Si tu vois une page « en construction » de ton fournisseur, l'adresse ouverte n'est pas celle qui pointe vers le serveur (étape 2).

10. **Sur ta vraie plateforme**, ajoute le réglage `JOBBOT_DEMO_URL=https://demo.joba1.ch` (ton adresse) et redémarre-la : « La plateforme » propose alors « Voir la démo ».

## Après chaque nouvelle version de jobA1

```bash
cd ~/job-bot && git pull && cd deploy/demo && docker compose up -d --build --wait
```

La démo est remplie à nouveau au redémarrage.

**Depuis 0.64** (docs/78), l'API se connecte à la base avec un rôle restreint, `jobbot_app`, qui ne peut pas passer outre la séparation des comptes ; seules la mise à jour du schéma et la remise à neuf utilisent le propriétaire des tables. Rien à faire : le mot de passe de ce rôle a une valeur par défaut. Pour le choisir toi-même, ajoute `DEMO_APP_DB_PASSWORD=…` dans `.env` avant la commande ci-dessus.

## Si quelque chose ne va pas

- **Voir ce qui se passe** : `docker compose ps` (l'état des services), `docker compose logs --tail 50 api web`.
- **Relancer** : `docker compose restart`.
- **Le certificat ne vient pas** : l'adresse ne pointe pas encore vers le serveur (étape 2), ou le port 80 est fermé (étape 3). Caddy réessaie tout seul.
- **Arrêter la démo** : `docker compose down`. Avec `docker compose down -v`, tout est effacé (base fictive comprise) ; elle se recrée au prochain lancement.

## L'entretien du serveur

Une fois par mois : `apt-get update && apt-get upgrade -y`, puis `docker compose pull db web && docker compose up -d --wait` pour les dernières versions de PostgreSQL et de Caddy.

## Ce que contient ce dossier

| Fichier | Rôle |
|---|---|
| `Dockerfile` | l'image du serveur jobA1 (`api`) et celle du site (`web` : Caddy et l'interface déjà construite) |
| `docker-compose.yml` | la base (jamais joignable depuis Internet), l'API en mode démo, la remise à neuf de nuit, le site |
| `Caddyfile` | HTTPS automatique, `/api` vers l'API, en-têtes de sécurité, pas d'indexation, métriques et documentation de l'API fermées, journal d'accès gardé 7 jours |
| `nightly.py` | remet la démo à neuf chaque nuit à 4 h (heure suisse) |
| `.env.example` | les réglages à copier en `.env` |

Pour l'essayer sur ton ordinateur d'abord : `make demo-image` à la racine du dépôt (http://localhost:8280), puis `make demo-image-stop`.
