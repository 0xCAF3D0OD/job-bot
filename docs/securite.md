# Les règles de sécurité de jobA1

> Ce texte dit **qui voit quoi**, comment les données et les secrets sont gardés, et que faire en cas d'incident. Il vaut pour toute installation de jobA1, et il est mis à jour à chaque version qui touche à la sécurité.
> Origine : le constat de sécurité du 2026-10-18 (docs/78). Le détail technique est dans `docs/exploitation.md`, « Sécurité » et « Accès à la base ».

## 1. Qui voit quoi

| Qui | Ce qu'il voit et fait | Ce qu'il ne voit jamais |
|---|---|---|
| **Un invité** | ses offres, candidatures, contacts, entretiens, documents, profils, réglages ; les tables communes (entreprises, sites, actualités, catalogue des formations) | les données d'un autre compte, même leur existence ; la liste des comptes |
| **L'exploitant** (le premier compte) | ses propres données ; la liste des comptes, leur dernière connexion, leur dépense d'IA et leur nombre d'offres du mois ; l'état et le journal de la plateforme ; les invitations ; les demandes de compte (identifiant, date, mot laissé) | dans l'interface, **jamais** les données d'un invité |
| **Le worker** (tâches de fond) | chaque compte à son tour, au nom de ce compte ; il écrit seul (avec l'exploitant) les tables communes | — |
| **Une page d'un autre site** | rien : les requêtes qui modifient sont refusées si elles ne viennent pas de la plateforme | — |

**Honnêtement** : l'exploitant administre le serveur. Il a donc un accès technique à la base et aux fichiers, et pourrait les lire. Il s'engage à ne pas le faire, sauf à la demande de l'invité ou par obligation légale. La page « Confidentialité » de la plateforme le dit aussi.

La séparation est faite **par la base elle-même** (PostgreSQL, sécurité au niveau des lignes), pas seulement par le code : chaque table est rangée dans une famille, avec sa règle, et un test vérifie qu'aucune table n'est oubliée (`backend/src/jobbot/db/policies.py`, docs/78 §3.2).

## 2. Les données

- **Où** : sur le serveur de l'exploitant (pour la démo en ligne : un serveur loué en Suisse). Base PostgreSQL ; les fichiers (CV, lettres, e-mails d'alerte) sous `accounts/<compte>/`.
- **Ce qui part à l'IA** (Anthropic, aux États-Unis) : le texte des offres, le profil (blocs du CV), les réponses d'entraînement ; **jamais** les noms des contacts ni les coordonnées de la personne. Chaque appel est journalisé et compté dans un plafond mensuel.
- **Ce qui part ailleurs** : seulement les adresses listées dans `docs/exploitation.md`, « Accès sortants ». Le serveur ne va jamais chercher une adresse interne (localhost, réseau privé).
- **Combien de temps** : tant que le compte existe, sauf les discussions avec l'assistant (30 jours) et les notifications (90 jours). Un invité **exporte** toutes ses données (Réglages › Compte, archive ZIP) et **supprime** son compte avec son mot de passe : ses lignes et son dossier sont effacés.
- **Les sauvegardes** (depuis 0.66, docs/82) : chaque nuit, la base et les fichiers, chiffrés, dans le dossier choisi par l'exploitant ; gardées 6 mois au plus, puis effacées. Un compte supprimé y reste jusqu'à 6 mois : la page « Confidentialité » le dit.
- **La démo** n'a que des données fictives, remises à neuf chaque nuit, en lecture seule.

## 3. Les secrets

- Les secrets (mot de passe de la base, clé de l'IA, boîte e-mail, boîte des invités, sujet ntfy) ne vivent que dans le fichier `.env` du serveur ou dans des fichiers `_FILE`. **Jamais** dans git, ni dans un journal, ni dans une capture d'écran partagée.
- **La phrase des sauvegardes** (`JOBBOT_BACKUP_PASSPHRASE`) : aussi gardée hors de l'ordinateur (gestionnaire de mots de passe, papier) ; sans elle, les sauvegardes sont illisibles. La changer ne rechiffre pas les anciennes sauvegardes : elles restent lisibles avec l'ancienne.
- La base ne garde des mots de passe et des jetons (sessions, invitations, extension, agenda) que leur **empreinte** : scrypt pour les mots de passe, SHA-256 pour les jetons.
- **Quand changer un secret** :
  - au départ d'une personne qui y avait accès ;
  - au moindre doute (clé vue, ordinateur perdu) ;
  - et au moins une fois par an pour la clé de l'IA et le mot de passe de la boîte.

## 4. Les accès

- **Inscription sur demande** (depuis 0.73.0, docs/102) : n'importe qui demande un compte depuis la page de connexion ; le compte **attend la validation de l'exploitant**. Tant qu'il attend : ni connexion, ni session, ni tâche, ni profil, ni adresse de réception. Une connexion avant l'acceptation le dit seulement si le mot de passe est juste. Refuser efface le compte ; une demande sans réponse est effacée après 30 jours.
- Garde-fous des demandes : 3 par heure depuis une même adresse IP, 20 en attente au plus, un champ piège invisible (rempli : ignorée en silence), pas de CAPTCHA. L'exploitant peut les fermer. La démo n'en a pas. Les journaux gardent l'identifiant et l'adresse IP, jamais le mot de passe ni le mot laissé.
- L'exploitant **invite** aussi par un lien à usage unique (7 jours) : le compte invité est accepté d'office.
- Mot de passe de **12 caractères au moins**. Après 5 essais ratés, une attente croissante.
- Une session dure 30 jours et se prolonge à l'usage, au plus 90 jours après la connexion. « Se déconnecter partout » ferme toutes les sessions du compte.
- **Suspendre** un compte ferme ses sessions, révoque ses jetons d'extension et d'agenda et arrête ses tâches ; ses données sont gardées.
- La connexion ne se désactive (`JOBBOT_AUTH_ENABLED=false`) que pour un essai sur son propre ordinateur, jamais sur une plateforme joignable par d'autres.
- Le serveur se connecte à la base avec des rôles **sans privilège** : `jobbot_app` pour l'API, `jobbot_worker` pour le worker. Seules les mises à jour du schéma utilisent le propriétaire des tables.

- La base **refuse tout lien entre deux comptes** : une candidature ne peut désigner qu'une offre du même compte, et ainsi de suite (depuis 0.64.1).
- Une tâche lancée par un bouton ne tourne **que pour le compte qui a cliqué** (depuis 0.64.1).

- Un compte suspendu perd aussi ses jetons d'extension et d'agenda ; une session dure au plus **90 jours** ; les essais de connexion sont comptés par adresse, pour qu'un inconnu ne bloque pas ta connexion ; le mode sans connexion est refusé hors de l'ordinateur lui-même (depuis 0.64.2).

## 5. En cas d'incident

Un compte qui agit de façon étrange, un secret qui a fuité, une faille signalée : dans l'ordre.

1. **Suspendre** le compte touché (Réglages › Plateforme, menu du compte, « Suspendre »).
2. **Se déconnecter partout** sur les comptes concernés ; la suspension révoque déjà leurs jetons d'extension et d'agenda.
3. **Changer les secrets** touchés : mot de passe de la base, clé de l'IA (sur la console d'Anthropic), mot de passe d'application de la boîte, sujet ntfy.
4. **Garder les journaux** du serveur tels quels (`docker compose logs`, journal de l'API), avant tout redémarrage qui les effacerait.
5. **Prévenir les personnes concernées** : ce qui s'est passé, quelles données, ce qui est fait.
6. Si leurs données sont **probablement en danger** (fuite, accès d'un tiers), **annoncer l'incident au PFPDT** (Préposé fédéral à la protection des données et à la transparence) dès que possible (nLPD, art. 24), par son formulaire en ligne.
7. Si des données ont été abîmées ou effacées : `jobbot restore <sauvegarde> --essai`, puis `jobbot restore <sauvegarde>` (docs/82).
8. Corriger, puis noter l'incident et sa correction dans une PR (sans données personnelles).

## 6. Les contrôles réguliers

- **À chaque version** : tous les tests, dont la séparation des comptes (chaque route de l'API appelée par un second compte) et les règles de chaque table (`tests/test_policies.py`).
- **Les bibliothèques** : `pip-audit` et `npm audit` chaque lundi sur GitHub (`.github/workflows/audit.yml`), et avant chaque revue.
- **Une revue de sécurité** comme celle de docs/78 tous les six mois, ou avant d'ouvrir la plateforme à de nouveaux invités.

## 7. Ce qui est accepté, et pourquoi

| Point | Pourquoi c'est accepté |
|---|---|
| Un compte apprend si un Message-ID d'e-mail existe déjà dans la plateforme | il faut déjà connaître ce Message-ID, impossible à deviner |
| Le cache commun des entreprises peut laisser deviner qu'un autre compte a eu la même entreprise | il ne contient que des informations publiques (registre IDE, site de l'entreprise), jamais une candidature |
| Les articles d'actualités et leurs images sont lisibles sans compte | ce sont des flux publics |
| L'exploitant a un accès technique à tout | c'est son serveur ; voir §1 |
| La base laisse l'exploitant lire l'empreinte du mot de passe des comptes | l'interface ne la montre jamais, et une empreinte scrypt ne redonne pas le mot de passe |

## 8. Signaler une faille

Voir [SECURITY.md](../SECURITY.md) : par le signalement privé de GitHub, jamais dans une issue publique.
