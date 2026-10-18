# 78 — Constat de sécurité, étanchéité des comptes et règles écrites (versions 0.64.0 à 0.64.2)

> Statut : **validé** le 2026-10-18.
> Origine : ta question du 2026-10-18 : « est-ce que ma plateforme est sécurisée ? » Tu veux une étanchéité **parfaite** entre les comptes, et des règles (policies) définies. Deux relectures complètes en lisant le code : la séparation dans la base (tables, règles, fonctions, tâches de fond), puis la connexion, les droits route par route, les fichiers, les adresses que le serveur va chercher et les bibliothèques. J'ai fait les contrôles sur la base de test (`jobbot_test`, migration 0053) et j'ai revérifié moi-même chaque constat moyen ou grave dans le code. Je n'ai rien lu de ta base, je ne me suis connecté à rien.

## 1. En clair : le verdict

**Oui, ta plateforme est sérieusement protégée, et aucune donnée d'un compte n'est lisible par un autre aujourd'hui.** Je n'ai trouvé aucune faille critique. Ce qui est en place :

- chaque ligne de chaque table personnelle est rangée par compte, et PostgreSQL lui-même refuse de la montrer à un autre ;
- les mots de passe sont bien hachés ;
- les jetons ne sont gardés qu'en empreinte ;
- les requêtes venues d'un autre site sont refusées ;
- les fichiers sont vérifiés ;
- le serveur ne va jamais chercher une adresse interne ;
- aucune bibliothèque n'a de faille connue (`pip-audit` et `npm audit` : 0).

**Mais l'étanchéité n'est pas encore parfaite.** Elle repose sur **une seule barrière**, et j'ai trouvé quatre endroits où un compte peut agir sur un autre, ou apprendre quelque chose de lui :

1. **Une seule barrière.** Le serveur se connecte à la base avec le compte administrateur, puis se met lui-même en mode restreint. Une seule erreur de programmation, une injection SQL par exemple (je n'en ai trouvé aucune), suffirait à sortir de ce mode et à tout voir.
2. **Les boutons « pour tout le monde ».** Un invité qui clique « Renoter » ou « Collecter maintenant » lance la tâche pour **tous** les comptes, y compris sur ton budget d'IA. Il ne voit rien de tes données, mais il dépense pour toi.
3. **Un message d'erreur commun.** La page de notation montre à chaque compte la dernière erreur de notation, qui peut venir d'un autre compte et contenir un bout de ses données.
4. **Un numéro d'offre d'un autre compte accepté.** Le message à un contact peut enregistrer une ligne qui pointe vers l'offre d'un autre compte, sans la lire. C'est un moyen de deviner quels numéros existent.

À côté, quelques défauts de la connexion :
- un compte suspendu garde ses jetons d'extension et d'agenda ;
- la limitation des essais de connexion se trompe d'adresse derrière un serveur intermédiaire ;
- le mode « sans connexion » n'a pas de garde-fou.

Et il n'existe **aucune règle écrite** : la sécurité est dans le code et dans `docs/exploitation.md`, mais rien ne dit qui a le droit de voir quoi, ni que faire en cas d'incident.

## 2. Les constats

Rangés par gravité ; chacun a été lu dans le code.

| Gravité | Constat | Correction | Version |
|---|---|---|---|
| **Haute** (une seule barrière) | L'API et le worker se connectent avec l'utilisateur des migrations, superutilisateur et propriétaire des tables (`dkey` chez toi, `jobbot` dans la démo, `deploy/demo/docker-compose.yml:16`). Seul `set role jobbot_app` (`db/base.py:48`) active la séparation ; un `reset role` dans la même transaction redonne tous les droits (essayé sur `jobbot_test`). Aucune table n'a `FORCE ROW LEVEL SECURITY`. | Trois rôles distincts (§3.1) : le serveur ne se connecte **jamais** en administrateur. | 0.64.0 |
| **Moyenne** | Une tâche lancée par un bouton est mise en file **sans le compte** (`worker/queue.py:11-28`) ; le worker la fait alors pour chaque compte (`worker/jobs.py:149-151`). Concerne « Renoter » et « Lire le télétravail » (`api/routes/scoring.py:143,159`), « Collecter maintenant » (`collect.py:740`), le filtre (`preferences.py:136,142`) et les actualités (`news.py:206`). Les tests ne le voient pas : la file y est remplacée (`tests/test_accounts.py:358,444`). | Le compte voyage avec la tâche, et chaque compte a sa propre place dans la file. | 0.64.1 |
| **Moyenne** | `GET /api/scoring` renvoie à tout compte l'erreur du dernier passage de notation, commun à tous (`api/routes/scoring.py:113`), avec le texte de l'exception (`worker/jobs.py:105`). `/api/status` masque pourtant ce même message aux invités (`status.py:110`). | Erreur par compte ; le détail technique à l'exploitant seul. | 0.64.1 |
| **Moyenne** | La base vérifie qu'un numéro existe, pas qu'il est **du même compte** : aucune des 21 clés étrangères entre tables personnelles ne contient le compte. Exemple : `contacts/message.py:64,102` enregistre l'appel d'IA d'un invité avec le numéro d'une offre d'un autre. | Clés étrangères qui comprennent le compte (§3.3) : la base refuse tout lien entre deux comptes. | 0.64.1 |
| Moyenne | **Un compte suspendu garde ses jetons** d'extension et d'agenda : les fonctions qui les reconnaissent ne regardent pas la suspension (migrations `0046:139`, `0053:26`), et la suspension ne ferme que les sessions (`platform.py:216-218`). | Les fonctions ignorent un compte suspendu ; la suspension révoque aussi les jetons. | 0.64.2 |
| Moyenne | **Limitation des essais de connexion** : elle compte par adresse du client (`routes/auth.py:129`). Derrière un serveur intermédiaire qui n'est pas sur la même machine (Caddy dans Docker, par exemple), tout le monde a la même adresse : 5 échecs de quelqu'un bloquent tout le monde. Le compteur par identifiant permet aussi à un inconnu de bloquer ta connexion jusqu'à 5 minutes (`auth/service.py:90-105`), et il n'est jamais vidé. Chez toi, derrière le tunnel sur ton Mac, l'adresse vue est probablement la bonne. | L'adresse réelle n'est lue que depuis les intermédiaires déclarés ; compter par adresse, et par adresse + identifiant ; vider les vieux essais. | 0.64.2 |
| Moyenne (réglage) | **`JOBBOT_AUTH_ENABLED=false` donne ton compte d'exploitant à n'importe qui** qui joint la plateforme, gestion des comptes comprise (`auth/middleware.py:151-160`). Rien ne l'empêche sur une plateforme ouverte. | Refusé dès que l'API n'écoute pas seulement sur l'ordinateur lui-même, ou en production. | 0.64.2 |
| Basse | `users`, `sessions` et `account_links` n'ont pas de séparation dans la base : seules les routes protègent les empreintes de mot de passe et de jeton. | Séparation dans la base, et fonctions « jeton → numéro de compte » comme pour l'extension (§3.2). | 0.64.0 |
| Basse | Le serveur a **tous** les droits sur toutes les tables (`0046_comptes.py:84`), y compris vider une table d'un coup (`TRUNCATE`, que la séparation n'arrête pas). | Lire, ajouter, modifier, supprimer, et seulement là où il le faut (§3.2). | 0.64.0 |
| Basse | Les tables communes (entreprises, logos) sont écrites par les invités : la recherche chez l'employeur (`employer/service.py:326-341`), l'adresse cherchée (`registry/service.py:93,172`), le logo tiré du site saisi dans une candidature spontanée (`spontaneous.py:42-48`). Un invité peut ainsi imposer un logo ou une page carrière aux autres. Le catalogue des formations accepte aussi, dans la base, l'écriture de n'importe quel compte (`0046_comptes.py:127-132`). | Ce qu'un invité trouve reste dans **son** offre ; seuls le worker et toi écrivez les tables communes (§3.2). | 0.64.0 et 0.64.2 |
| Basse | `GET /api/offers/{id}/address-candidates` appelle le registre et l'IA (coût) et écrit dans la base : une lecture avec effets, qu'un autre site peut déclencher par un simple lien. | La passer en écriture (POST), donc protégée comme les autres. | 0.64.2 |
| Basse | Pas d'en-têtes de sécurité posés par l'API elle-même (seul le Caddy de la démo les met). Un document déposé est renvoyé « à afficher » sans `nosniff` (`profile.py:183-189`). `/metrics`, `/readyz`, `/version` répondent à qui joint l'API ; la documentation de l'API est publique hors production. | En-têtes posés par l'API ; documents texte en téléchargement ; ces adresses réservées à l'ordinateur lui-même. | 0.64.2 |
| Basse | Taille des envois : tout le fichier est lu avant d'être refusé (`profile.py:126`), et un `.docx` est une archive qui peut gonfler. | Refus dès l'en-tête de taille ; taille dépliée plafonnée. | 0.64.2 |
| Basse | Les deux fonctions spéciales n'ont pas `pg_temp` en fin de chemin de recherche (habitude de prudence, sans risque aujourd'hui). | `set search_path = public, pg_temp`. | 0.64.0 |
| Info | Une session se prolonge sans fin tant qu'elle sert (30 jours glissants). Deux fonctions disent à un compte si une source d'actualités est suivie ailleurs, ou si un Message-ID existe déjà. Le cache commun des entreprises peut trahir qu'un autre compte a eu la même entreprise. | Session limitée à **90 jours** au total. Le reste est accepté et écrit dans les règles (§4) : ce sont des informations publiques ou impossibles à deviner. | 0.64.2 |

Déjà juste, vérifié :
- l'appel de **toutes les routes** (188) avec un second compte, dans `tests/test_accounts.py` ;
- les identifiants envoyés par l'interface toujours relus à travers la séparation ;
- les fichiers rangés par compte ;
- l'export qui ne sort ni empreinte ni mot de passe ;
- la démo en lecture seule ;
- aucun `v-html`, aucun SQL construit avec une saisie ;
- les secrets jamais journalisés ;
- les adresses internes refusées partout où le serveur va chercher une page.

## 3. L'étanchéité parfaite : ce qui change

### 3.1 Trois rôles, et le serveur n'est jamais administrateur

| Rôle | Qui l'utilise | Ce qu'il peut |
|---|---|---|
| `jobbot_owner` | `jobbot migrate` seulement | créer et modifier les tables ; ne sert jamais pendant le fonctionnement |
| `jobbot_app` | l'API | les lignes du compte en cours, et lire les tables communes ; ni superutilisateur, ni contournement de la séparation, ni droit de changer de rôle |
| `jobbot_worker` | le worker | comme l'API, plus l'écriture des tables communes (entreprises, logos, articles, journal des tâches) |

- Chaque rôle se connecte **directement** : il n'y a plus de `set role`, donc rien à « défaire ».
- `FORCE ROW LEVEL SECURITY` est mis sur toutes les tables personnelles : même le propriétaire y est soumis.
- Au démarrage, l'API et le worker vérifient leur propre rôle. S'ils tournent en administrateur, ils le disent dans le journal et sur « La plateforme » (en rouge). La démo, elle, refuse de démarrer.
- **Sur ta plateforme, ensuite** : deux lignes à changer dans ton `.env` (l'adresse de la base pour l'API et le worker, une autre pour `migrate`). Je te les donne dans la PR. Sur ton Mac, PostgreSQL n'exige pas de mot de passe en local : il n'y en a aucun à créer ni à me donner. Dans la démo, le paquet `deploy/demo/` fait tout.

### 3.2 Une règle pour chaque table

Toutes les tables sont rangées dans **quatre familles**, écrites dans un seul fichier du code (`db/policies.py`). Un test compare ce fichier à la base. Une nouvelle table qui n'y est pas rangée, ou qui n'a pas la règle de sa famille, fait échouer les tests : **on ne peut plus oublier une table**.

| Famille | Tables | Règle dans la base |
|---|---|---|
| **Personnelles** (29) | offres, candidatures, contacts, entretiens, entraînements, documents, profils, blocs, lettres, discussions, alertes, notifications… | chaque compte ne lit et n'écrit que ses lignes ; impossible d'en créer une pour un autre compte, ni de la relier à une ligne d'un autre compte (§3.3) |
| **Connexion** (3) | `users`, `sessions`, `account_links` | un compte ne voit que sa propre ligne ; toi, tu vois la liste des comptes (jamais leurs empreintes) ; un jeton ou un identifiant n'est reconnu que par une fonction qui ne rend que le numéro du compte, comme déjà pour l'extension et l'agenda |
| **Communes** (8) | entreprises, logos, sites, sources et articles d'actualités, catalogue des formations, réglages de l'installation, journal des tâches | tout compte lit (le journal : toi seul) ; seuls le worker et ton compte écrivent ; les invités, jamais |
| **Techniques** | file des tâches (`procrastinate_*`), version des migrations | aucun accès direct de l'API, seulement « mettre une tâche en file » |

### 3.3 Aucun lien possible entre deux comptes

Les 21 clés étrangères entre tables personnelles comprennent désormais le compte. Par exemple, une candidature ne peut pointer vers une offre que si **les deux** sont du même compte, et la base refuse sinon. C'est la règle la plus forte possible : même un code faux ne pourrait pas créer de lien.

Le test le prouve en essayant directement dans la base les 21 liens d'un compte vers un autre : chacun doit être refusé.

### 3.4 Les tâches gardent leur compte

- Un bouton met en file la tâche **avec le compte** qui a cliqué. Le worker ne la fait que pour lui.
- Deux comptes peuvent lancer la même tâche en même temps ; un même compte, pas deux fois.
- Les tâches planifiées passent toujours compte par compte, comme aujourd'hui.
- L'erreur d'un passage est rangée par compte.
- Le test passe par la vraie file, sans la remplacer.

## 4. Les règles écrites (policies)

Deux nouveaux textes, en français simple :

**`docs/securite.md` : les règles de la plateforme.**

| Sujet | Ce qui est écrit |
|---|---|
| **Qui voit quoi** | Un invité : ses données, rien d'autre. L'exploitant : la liste des comptes, leur consommation d'IA, l'état de la plateforme, **jamais** les données d'un invité dans l'interface. Honnêtement : l'exploitant a l'accès administrateur à la base et aux fichiers, donc il pourrait techniquement les lire ; il s'engage à ne pas le faire, sauf demande de l'invité ou obligation légale. C'est aussi écrit dans la page « Confidentialité ». |
| **Les données** | Où elles sont (ton serveur, en Suisse ; les fichiers sous `accounts/<compte>/`). Ce qui part à l'IA, et ce qui n'y part jamais (noms des contacts, tes coordonnées). La durée de conservation. L'export et la suppression par l'invité. |
| **Les secrets** | Uniquement dans `.env` ou des fichiers `_FILE`, jamais dans git ni dans un journal. Quand en changer : départ d'un invité qui y avait accès, doute, et au moins une fois par an. |
| **Les accès** | Inscription sur invitation seulement ; mot de passe de 12 caractères au moins ; session de 90 jours au plus ; suspension immédiate (sessions et jetons) ; la connexion ne se désactive que sur l'ordinateur lui-même. |
| **En cas d'incident** | Les étapes dans l'ordre : suspendre le compte touché ; se déconnecter partout ; révoquer les jetons ; changer les secrets ; garder les journaux ; prévenir les personnes concernées. Si leurs données sont probablement en danger, annoncer l'incident au PFPDT dès que possible (nLPD, art. 24). |
| **Contrôles réguliers** | À chaque version : tests de séparation et vérification des familles de tables. Chaque semaine (GitHub) : `pip-audit` et `npm audit`. Une revue de sécurité comme celle-ci tous les six mois, ou avant d'ouvrir à de nouveaux invités. |
| **Ce qui est accepté** | Les petites informations du §2 « Info », avec la raison. |

**`SECURITY.md` à la racine du dépôt** : comment signaler une faille. On passe par le **signalement privé de GitHub** (aucune adresse e-mail dans le dépôt public). Le texte dit ce qui est couvert (le code), ce qui ne l'est pas (ta plateforme, la démo), et dans quel délai tu réponds.

## 5. Livraison en trois PR

| Version | Contenu | Migration |
|---|---|---|
| **0.64.0** | Trois rôles, `FORCE`, droits précis, séparation des tables de connexion, tables communes en écriture pour le worker et toi, catalogue des formations, `pg_temp`. `db/policies.py` et son test. `docs/securite.md` et `SECURITY.md`. Le paquet de la démo mis à jour. | 0054 |
| **0.64.1** | Les tâches avec leur compte ; l'erreur de notation par compte ; les clés étrangères avec le compte ; le message à un contact qui ne garde que son propre numéro d'offre. | 0055 |
| **0.64.2** | Jetons coupés à la suspension, limitation de connexion juste, mode sans connexion verrouillé, lecture avec effets passée en écriture, en-têtes et documents, taille des envois, session de 90 jours, découvertes des invités gardées dans leur offre, `pip-audit` et `npm audit` chaque semaine. | 0056 |

Chaque PR met à jour `docs/securite.md` et `docs/exploitation.md` (qui parle encore de 27 tables, c'est 29).

Vérifications, à chaque fois sur une base à part :
- tous les tests et les nouveaux tests de séparation ;
- un essai qui tente un `reset role` et une écriture vers un autre compte, et qui doit échouer ;
- la démo complète dans Docker (`make demo-image`) avec ses trois services et ses deux rôles ;
- le parcours de toutes les pages sans erreur.

**Après 0.64.0**, sur ta plateforme : les deux lignes du `.env`, puis `jobbot migrate` (je te donne les commandes dans la PR). Sur le VPS : `git pull` et `docker compose up -d --build --wait`, comme d'habitude.

## Points à valider

1. **Trois rôles**, et le serveur jamais administrateur ; sur ta plateforme, un avertissement plutôt qu'un refus de démarrer (§3.1).
2. **Quatre familles de tables** dans `db/policies.py`, vérifiées par un test (§3.2).
3. **Clés étrangères avec le compte** : aucun lien possible entre deux comptes (§3.3).
4. **Tâches avec leur compte** (§3.4).
5. **Tables communes écrites par le worker et toi seulement** : ce qu'un invité trouve (adresse, page carrière, logo) reste dans son offre (§2, §3.2).
6. **Session de 90 jours au plus** (§2).
7. **Les règles écrites** : `docs/securite.md`, et `SECURITY.md` avec le signalement privé de GitHub, sans adresse e-mail (§4).
8. **Trois PR, 0.64.0 à 0.64.2**, avec trois migrations (§5).

## Écarts avec le cadrage (0.64.0)

- **Une limite à dire franchement.** La séparation repose sur le compte que le serveur donne à la base au début de chaque transaction. Une injection SQL pourrait encore changer ce compte dans sa propre transaction. Je n'en ai trouvé aucune : aucune requête n'est construite avec une saisie. Ce que 0.64.0 enlève, c'est tout le reste. Une injection ne pourrait plus :
  - lire les fichiers du serveur ;
  - lancer une commande ;
  - modifier ou vider une table ;
  - reprendre les droits d'administrateur.

  Le §1 disait « sortir de ce mode et tout voir » : il ne reste plus que changer de compte, ce qui suppose une injection.
- **Pas de rôle `jobbot_owner` créé** : le propriétaire des tables reste l'utilisateur des migrations (`dkey` chez toi, `jobbot` dans la démo), donné par `JOBBOT_MIGRATE_DATABASE_URL`.
- **Pas de `FORCE ROW LEVEL SECURITY`.** Le propriétaire est superutilisateur partout, et un superutilisateur passe outre de toute façon : `FORCE` n'aurait rien changé. Il aurait en revanche bloqué les fonctions spéciales si le propriétaire ne l'était pas. La protection vient de ce que le serveur ne se connecte plus en propriétaire, et de `tests/test_policies.py`.
- **Ancienne configuration acceptée, signalée** : sans les nouvelles adresses, l'API et le worker se restreignent eux-mêmes comme avant. L'API l'écrit dans son journal et l'affiche en rouge sur « La plateforme ». La démo, elle, refuse de démarrer.
- **Le journal des tâches est lisible par tous les comptes dans la base** (les dates de la dernière collecte servent à l'état de chaque compte) ; sa page reste réservée à l'exploitant. L'erreur détaillée passe par compte en 0.64.1.
- **La file des tâches** : l'API garde le droit d'écrire dans les tables de procrastinate, parce que ses fonctions de mise en file s'exécutent avec les droits de l'appelant. Elle n'y lit aucun contenu des comptes.
- **Le worker lit tous les comptes** (pas les mots de passe à l'écran, mais la ligne) : il en a besoin pour ranger chaque alerte e-mail par l'adresse du compte.
- **Une session expirée est encore reconnue par sa fonction**, pour être effacée ensuite au nom de son compte ; elle n'ouvre rien.
- **Les découvertes d'un invité, déjà en 0.64.0** pour l'adresse (registre, Internet) et la page carrière : la base refusant désormais ces écritures, elles ne valent que pour ses offres. Choisir une proposition du registre la redemande au registre si le cache commun ne l'a pas. Le logo tiré du site saisi dans une candidature spontanée reste pour 0.64.2.
- **Une source d'actualités** que plus personne ne suit est effacée par une fonction de la base (`drop_unfollowed_news_source`), qui remplace `news_source_followers` : un compte n'apprend plus si d'autres la suivent.
- **Le catalogue des formations** s'écrit au nom de l'exploitant, à la première lecture.
- **La page « Confidentialité »** dit aussi que l'exploitant s'engage à ne pas lire les données (§4).
- **Les tests qui vident les tables** le font avec le propriétaire (`admin_engine()`), le serveur n'ayant plus `TRUNCATE`.
- **Vérifié** :
  - 479 tests serveur, dont 13 nouveaux (`test_policies.py`, connexion directe en `jobbot_app`, trois accès, recherche d'adresse d'un invité), et 290 tests de l'interface ;
  - dans Docker, la démo 0.63.2 mise à jour en 0.64.0 sur sa base existante, puis une installation neuve :
    - l'API connectée en `jobbot_app`, avec le mot de passe donné par `jobbot migrate` ;
    - le parcours de toutes les pages : 174 appels, aucune erreur ;
    - la remise à neuf de nuit fonctionne ;
    - `reset role` puis `truncate` sont refusés au rôle ;
  - sur une base de brouillon, avec ton ancienne configuration : l'avertissement s'affiche ;
  - avec les trois adresses : une tâche mise en file par l'API est faite par le worker en `jobbot_worker`.
- **À activer sur GitHub** (toi) : Settings › Security › « Private vulnerability reporting », pour que le signalement de `SECURITY.md` soit possible.

## Écarts avec le cadrage (0.64.1)

- **Quatre unicités valaient pour toute la plateforme** : une candidature, une évaluation, un lien par site et une version de lettre par offre. Un refus pouvait dire à un compte qu'une ligne existait chez un autre. Le test des liens l'a montré : la base répondait « déjà pris » avant de vérifier le compte. Elles valent maintenant par compte. Un test vérifie qu'aucune unicité d'une table personnelle ne vaut pour toute la plateforme. Seules exceptions : les empreintes de jetons et le numéro de lot de l'IA, tirés au hasard.
- **Les 21 liens** sont vérifiés dans la définition de la base (chacun comprend le compte), et quatre sont essayés pour de vrai : l'appel d'IA, la candidature, le contact, le message de l'assistant. PostgreSQL applique la même règle à tous.
- **Un lien qui traversait déjà deux comptes** : la migration le défait s'il est facultatif, et s'arrête sans rien effacer s'il est obligatoire. Vérifié en lecture seule sur ta base : aucun.
- **Une tâche à la fois, tous comptes confondus.** Chaque compte a sa place dans la file, mais deux exécutions de la même tâche ne tournent toujours pas en même temps. Un clic ne chevauche donc jamais le passage planifié du même compte.
- **« Collecter maintenant »** lit la boîte de l'installation, qui est commune ; chaque e-mail va dans son compte. Le clic d'un invité ne fait qu'avancer cette lecture : c'est accepté.
- **L'erreur de notation** :
  - l'exploitant voit le détail ;
  - le compte pour qui la notation a échoué voit « voir avec l'exploitant » ;
  - un autre compte ne voit rien.
- **Vérifié** :
  - 485 tests serveur, dont 6 nouveaux (`test_links.py`, unicités par compte). La file est la vraie, sans bouchon : la tâche de B tourne pour B, celle de l'exploitant pour l'exploitant.
  - Dans Docker, la démo 0.64.0 mise à jour en 0.64.1 sur sa base : migration 0055, parcours de toutes les pages en 174 appels, aucune erreur.

## Écarts avec le cadrage (0.64.2)

- **Plus de compteur par identifiant seul** : les essais ratés comptent par adresse, et par adresse plus identifiant. Un essai depuis une autre adresse ne bloque donc plus ta connexion. Contre des essais venus de nombreuses adresses, deux choses suffisent :
  - un mot de passe de 12 caractères au moins ;
  - scrypt, qui rend chaque essai coûteux.
- **Un jeton révoqué à la suspension le reste** si le compte est réactivé : la personne en crée un nouveau dans ses Réglages. La base ignore aussi les jetons d'un compte suspendu, même révoqués à la main.
- **Les adresses d'exploitation** (`/readyz`, `/version`, `/metrics`, documentation de l'API) restent permises depuis le réseau privé, pour les sondes et Prometheus. Jamais au travers d'un intermédiaire : une requête qui porte `X-Forwarded-For` reçoit 404. Sur ta plateforme, la documentation de l'API n'est donc plus visible par le tunnel, même en `JOBBOT_ENV=dev`.
- **Les en-têtes de l'API** : `nosniff`, `SAMEORIGIN`, `same-origin`. Pas de CSP générale sur les réponses JSON ; les logos et images ont déjà la leur. Dans la démo, Caddy pose des valeurs plus strictes (`DENY`, `no-referrer`).
- **Taille des envois** : refusée dès l'en-tête au-delà de 11 Mo. Un envoi sans taille annoncée est coupé dès qu'il dépasse.
- **Le logo, pour un compte invité** : seul le logo relevé dans une page ou une alerte compte, ou le site connu du cache commun. Jamais un site saisi par l'invité, ni l'adresse trouvée pour lui.
- **L'audit des bibliothèques** tourne chaque lundi sur GitHub, et à la main par « Run workflow » (`.github/workflows/audit.yml`). Les deux passent aujourd'hui : aucune faille connue.
- **Vérifié** :
  - 494 tests serveur, dont 9 nouveaux (`test_connexion.py`), et 290 tests de l'interface.
  - Dans Docker, la démo 0.64.1 mise à jour en 0.64.2 sur sa base, avec la migration 0056 :
    - le parcours de toutes les pages fait 174 appels, aucune erreur ;
    - les adresses d'exploitation répondent 404 depuis l'extérieur ;
    - `/readyz` répond toujours depuis l'intérieur du conteneur ;
    - la recherche d'adresse est refusée par la démo, comme toute écriture.
