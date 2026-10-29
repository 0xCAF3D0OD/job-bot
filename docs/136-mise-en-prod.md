# 136 — La vraie plateforme en ligne (version 1.6.x)

> Statut : **préparé** le 2026-10-29, essayé sur le Mac (images construites, plateforme et démo derrière un seul Caddy, mise à jour plateforme en marche, sauvegarde et essai de restauration). Pas encore lancé sur le serveur.
> Origine : ta demande du 29 octobre : faire pour jobA1 ce que BlablaBot a (`make deploy` depuis le Mac met à jour le serveur), mettre en ligne la vraie plateforme à côté de la démo sur la VM Infomaniak, construire les images avec GitHub Actions.

## 1. En clair

Aujourd'hui, la vraie plateforme tourne sur ton Mac, en mode développement (`launsh.sh` lance `make dev`), et seule la démo est en ligne (docs/77). Après ce changement :

- la vraie plateforme tourne sur le **même serveur que la démo**, à `https://app.joba1.ch` (l'adresse se choisit à l'installation) ;
- **GitHub construit les images** à chaque envoi sur `main`, en même temps que les tests ;
- **`make deploy`**, depuis ton Mac, met le serveur à jour avec le dernier commit de `main` dont les tests **et** les images ont réussi. Rien n'est compilé sur le serveur.

## 2. Pourquoi ainsi

**Le serveur** (VPS Infomaniak, `179.237.122.64`) a 1 processeur, 2 Go de mémoire, pas de swap. Mesuré le 29.10 : la démo prend ~280 Mo, 1,1 Go restent libres. La plateforme (API ~180 Mo, worker, PostgreSQL, Caddy) tient dans ce qui reste une fois lancée. Ce qui ne tenait pas, c'était **de construire sur le serveur** (`npm ci`, compilation de l'interface, `uv sync`) : le risque était de manquer de mémoire et de faire tomber la démo, et 9 Go de cache s'étaient accumulés. L'installation ajoute 2 Go de swap et vide ce cache.

**Pourquoi pas la méthode BlablaBot telle quelle** (envoyer le code, compiler et relancer un service sur le serveur) : jobA1 a déjà ses images Docker (`deploy/demo`) et une doc d'exploitation écrite pour des conteneurs. Seule la construction change de place.

**Pourquoi pas un déploiement automatique à chaque fusion** : il y en a plusieurs par jour et c'est ta plateforme, avec tes données. Tu choisis le moment, et aucune clé SSH du serveur n'est confiée à GitHub.

**Pourquoi le même serveur que la démo** plutôt que celui de BlablaBot : même projet, déjà sous Docker, déjà sous `joba1.ch`. BlablaBot reste seul sur sa machine. Si le serveur manque de place un jour, passer la VM à 4 Go chez Infomaniak suffit.

## 3. Ce qui tourne sur le serveur

| Projet Docker | Services | Rôle |
|---|---|---|
| `joba1` (`deploy/prod/docker-compose.yml`) | `db`, `migrate`, `api`, `worker`, `web` | la vraie plateforme ; `migrate` met le schéma à jour avant l'API et le worker, à chaque lancement ; `web` est le seul Caddy du serveur, qui sert les deux sites (ports 80 et 443) |
| `joba1-demo` (`deploy/demo/docker-compose.yml` + `deploy/prod/demo.yml`) | `db`, `api`, `nightly` | la démo (docs/77), avec l'image de la plateforme ; son Caddy à elle ne tourne pas ici (profil `autonome`) ; le Caddy de la plateforme joint son API sur le réseau partagé `joba1` |

Les images : `ghcr.io/0xcaf3d0od/joba1-api` (API, worker, commandes, avec `pg_dump` 17 pour les sauvegardes) et `ghcr.io/0xcaf3d0od/joba1-web` (Caddy et l'interface), étiquetées du commit.

Les réglages, sur le serveur seulement, jamais dans git :

| Fichier | Contenu |
|---|---|
| `~/joba1/deploy/prod/.env` | la version en place, les deux adresses, les trois mots de passe de la base (tirés au hasard à l'installation, jamais affichés) |
| `~/joba1/deploy/prod/jobbot.env` | clé d'IA, boîtes e-mail, ntfy, phrase des sauvegardes… (modèle : `jobbot.env.example`) |
| `~/joba1/deploy/demo/.env` | les réglages de la démo, repris de l'installation du 18.10 (`/root/job-bot`) |

Chaque service n'a que l'accès à la base dont il a besoin (docs/78) : l'API `jobbot_app`, le worker `jobbot_worker` (et le propriétaire pour les sauvegardes), `migrate` le propriétaire.

Les sauvegardes (docs/82) vont dans `~/joba1/sauvegardes`, **sur le même disque** : `make prod-sauvegardes` les copie sur ton Mac.

## 4. Ce que tu fais, une fois

1. **Le DNS** : chez Infomaniak, dans la zone DNS de `joba1.ch`, un enregistrement **A** `app` vers `179.237.122.64`. Vérifier : `dig +short app.joba1.ch`.
2. **Fusionner la PR.** Le workflow « Images » se lance sur `main` (~5 minutes la première fois).
3. **Rendre les images publiques** : sur GitHub, ton profil › Packages › `joba1-api` › Package settings › Change visibility › Public ; pareil pour `joba1-web`. Le code est déjà public et les images ne contiennent aucun secret (`.dockerignore`). Sans cela, le serveur ne peut pas les télécharger.
4. **Installer** depuis le Mac :

   ```bash
   make deploy-install DOMAIN=app.joba1.ch
   ```

   Docker est déjà là ; le script ajoute le swap, vide le cache, reprend les réglages de la démo, crée ceux de la plateforme, arrête l'ancien Caddy de la démo et lance tout. La démo est coupée quelques secondes.
5. **Les réglages** : `make prod-reglages` ouvre `jobbot.env` sur le serveur (Ctrl-O, Entrée, Ctrl-X), puis relance l'API et le worker. Mets la **même** `JOBBOT_BACKUP_PASSPHRASE` que sur ton Mac, sinon tes sauvegardes du Mac ne s'ouvriront pas sur le serveur.
6. **Tes données** : arrête la plateforme du Mac (Ctrl-C sur `make dev`), fais une dernière sauvegarde, puis envoie-la :

   ```bash
   cd backend && uv run jobbot backup && cd ..
   make prod-restaurer FICHIER=sauvegardes/jobA1-AAAA-MM-JJ-HHMM.jobA1backup
   ```

   Il faut écrire « restaurer » pour confirmer. Sans données à reprendre : `make prod-mot-de-passe` crée le compte de l'exploitant.
7. **Ne relance plus `make dev` avec la vraie boîte e-mail** : deux plateformes qui lisent la même boîte se disputeraient les alertes, et la boîte des invités est vidée à chaque relevé. Pour développer, garde un `.env` local sans `JOBBOT_IMAP_*` ni `JOBBOT_GUEST_IMAP_*`.
8. **L'extension** : dans sa fenêtre, remplace l'adresse par `https://app.joba1.ch`.

## 5. Ensuite, au quotidien

| Commande (sur le Mac) | Ce qu'elle fait |
|---|---|
| `make deploy` | met à jour : maintenance annoncée, images du commit, schéma, API, worker, site, maintenance levée, démo, ménage, contrôle de la version (~35 s, le site ne répond pas pendant ~2 s) |
| `make deploy REF=abc1234` | une version précise (revenir en arrière : seulement si le schéma de la base n'a pas changé entre les deux) |
| `make prod-etat` | services, mémoire, swap, disque |
| `make prod-logs` | journal en direct (`SERVICES=worker` pour un seul) |
| `make prod-reglages` | modifier `jobbot.env`, puis relance |
| `make prod-sauvegardes` | copie les sauvegardes du serveur dans `~/Documents/joba1-sauvegardes-serveur` |
| `make prod-restaurer FICHIER=…` | remet la plateforme à une sauvegarde |
| `make prod-mot-de-passe` | compte de l'exploitant |
| `make prod-ssh` | un terminal sur le serveur |

`make deploy` dit ce qui part et ce qui tourne : « Envoi : 1a2b3c4 … — 3 commits de plus ». Le commit que le robot du changelog ajoute après chaque fusion n'a ni tests ni images (GitHub ne relance rien pour un envoi de son propre jeton) : `make deploy` prend la fusion juste avant, au contenu identique.

Pendant une mise à jour, Caddy répond « jobA1 se met à jour » quand l'API redémarre, et l'interface montre sa page d'attente (docs/79).

## 6. Ce qu'on ne fait pas (encore)

- **Pas de surveillance** comme la veille ntfy de BlablaBot : si la plateforme tombe, `make prod-etat` le dit. Le worker prévient déjà par ntfy quand une sauvegarde échoue.
- **Pas de copie automatique des sauvegardes hors du serveur** : `make prod-sauvegardes` à la main, ou un stockage externe plus tard (kDrive, Swiss Backup).
- **`/root/job-bot`**, l'ancienne installation de la démo, reste sur le serveur sans servir : à effacer une fois la nouvelle vérifiée.

## 7. Vérifié sur le Mac (29.10)

- les deux images se construisent (`joba1-api` 844 Mo, `joba1-web` 103 Mo) ; `pg_dump` 17.11 dans l'image ;
- plateforme : migrations, API, worker et site démarrent en ~26 s ; `/healthz` 200, `/version`, `/metrics` et `/api/docs` en 404 depuis l'extérieur ; un ancien fichier `/assets/…` en 404 ;
- démo derrière le même Caddy : pages en 200, écriture en 403, `X-Robots-Tag: noindex` et `robots.txt` ; tant que son API n'est pas lancée, réponse « se met à jour » (503) ;
- `serveur.sh mettre-a-jour`, avec un registre d'images local à la place de GitHub : première mise en ligne, puis une seconde version plateforme en marche (maintenance annoncée puis levée) ;
- `jobbot backup` avec l'accès propriétaire, puis `jobbot restore --essai` : 49 tables, rien de touché.

Pas vérifiable avant la fusion : le workflow « Images » sur GitHub et l'installation sur le vrai serveur.

**Remarqué en passant** : sur une base **sans aucun compte**, l'API ne voit pas une maintenance annoncée (la recherche de l'exploitant échoue avec le rôle `jobbot_app`, et l'API considère alors la plateforme comme ouverte). Sans effet ici : à la première installation, rien ne tourne encore, et ensuite le compte existe.
