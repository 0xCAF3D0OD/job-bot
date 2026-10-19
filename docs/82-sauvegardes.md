# 82 — Les sauvegardes automatiques (version 0.66.0)

> Statut : **validé** le 2026-10-19.
> Origine : la suite proposée après la revue 0.65.2. `docs/exploitation.md` dit quoi sauvegarder (« Données à sauvegarder »), mais rien ne le fait : si le disque de ton Mac lâche, ou s'il est volé, tes candidatures, tes preuves ORP et les données de tes invités sont perdues. Aujourd'hui, la base pèse 16 Mo et les fichiers 26 Mo : une sauvegarde complète est petite et rapide.

## 1. En clair

- **Chaque nuit**, la plateforme fait une sauvegarde complète : la base et les fichiers déposés (CV, lettres, e-mails d'alerte), dans **un seul fichier chiffré**.
- **Elle garde** les 7 derniers jours, puis une par semaine pendant 4 semaines, puis une par mois pendant 6 mois. Le reste est effacé tout seul.
- **Chaque semaine**, elle vérifie que la dernière sauvegarde se restaure vraiment : elle la remet dans une base à part, compte ce qu'elle contient, puis l'efface. Une sauvegarde jamais essayée ne vaut rien.
- **Si une sauvegarde échoue**, ou si la dernière date de plus de 36 heures, tu reçois une notification sur ton téléphone (ntfy), et « La plateforme » l'affiche en rouge.
- **Restaurer** se fait avec une commande, qui met la plateforme en maintenance le temps de l'opération.

## 2. Où vont les sauvegardes

Une sauvegarde sur le même disque que la plateforme ne protège ni d'une panne du disque ni d'un vol. Le dossier est donc à choisir (`JOBBOT_BACKUP_PATH`), par exemple :

| Où | Pour | Contre |
|---|---|---|
| **Un dossier iCloud Drive** (ou Google Drive, Proton Drive…) | copié tout seul hors de ton Mac, sans rien faire | les fichiers sont chez ce service : d'où le chiffrement (§3) |
| **Un disque externe** | rien ne sort de chez toi | il faut qu'il soit branché la nuit |
| **Le dossier du dépôt** (par défaut : `sauvegardes/`, ignoré par git) | rien à régler | ne protège que d'une erreur, pas d'une panne |

Je conseille **iCloud Drive** (ou le service que tu utilises déjà), grâce au chiffrement : le service ne voit qu'un fichier illisible.

## 3. Le chiffrement

- Chaque sauvegarde est chiffrée (AES-256-GCM) avec une **phrase secrète** que tu choisis et que tu écris toi-même dans `.env` (`JOBBOT_BACKUP_PASSPHRASE`). Je ne la vois jamais.
- **Sans cette phrase, les sauvegardes sont illisibles, y compris pour toi.** Garde-la aussi ailleurs que sur le Mac : un gestionnaire de mots de passe, ou sur papier. C'est la seule chose à ne pas perdre.
- Sans phrase réglée, la plateforme ne sauvegarde pas, et « La plateforme » te le dit. Une sauvegarde non chiffrée des données de tes invités ne doit pas partir dans un service en ligne.
- Il faut une bibliothèque de plus : `cryptography`, la référence en Python pour le chiffrement.

## 4. Comment

- **La sauvegarde** : `pg_dump` de la base complète (avec l'accès propriétaire, `JOBBOT_MIGRATE_DATABASE_URL`, le seul qui voit tous les comptes), plus les fichiers sous `JOBBOT_STORAGE_PATH`. Les logos et les miniatures des actualités sont exclus : ils se retéléchargent tout seuls. Le tout est mis dans une archive, chiffrée, puis écrite sous `jobA1-AAAA-MM-JJ-HHMM.jobA1backup`.
- **Quand** : une tâche du worker à **3 h** (heure suisse). Si ton Mac dormait à cette heure-là, elle se fait **au prochain démarrage** du worker, dès que la dernière date de plus de 24 heures.
- **L'essai de restauration** : chaque dimanche, après la sauvegarde. Il restaure dans une base temporaire, vérifie que les tables et les fichiers sont là, puis efface la base. Le résultat est noté dans le journal des tâches.
- **Les commandes** :

  | Commande | Effet |
  |---|---|
  | `jobbot backup` | une sauvegarde tout de suite (avant une opération délicate, par exemple) |
  | `jobbot backup --list` | les sauvegardes présentes, leur date et leur taille |
  | `jobbot restore <fichier> --essai` | l'essai de restauration, dans une base à part, sans rien toucher |
  | `jobbot restore <fichier>` | la vraie restauration. Elle demande d'écrire « restaurer » au clavier, puis : maintenance complète, sauvegarde de l'état actuel (au cas où), base et fichiers remis, migrations, fin de maintenance. |

- **« La plateforme »** : la date de la dernière sauvegarde, et celle du dernier essai de restauration réussi.

## 5. Ce que ça change pour tes invités

- La page « Confidentialité » dit que la plateforme est sauvegardée chaque nuit, chiffrée, et que les sauvegardes sont gardées **6 mois au plus**.
- **Un compte supprimé reste dans les sauvegardes jusqu'à 6 mois**, puis disparaît avec elles. Il ne revient que si toute la plateforme est restaurée à une date antérieure. La loi sur la protection des données l'admet, à condition de le dire : c'est écrit sur cette page.
- `docs/securite.md` : les sauvegardes et la phrase secrète rejoignent les règles (§2 et §3), et la restauration rejoint ce qu'on fait en cas d'incident (§5).

## 6. Ce qu'on ne fait pas

- **Pas de sauvegarde de la démo** : elle n'a que des données fictives, refaites chaque nuit.
- **Pas d'envoi vers un serveur à moi ou à un service choisi par jobA1** : le dossier est le tien, et la copie hors du Mac passe par le service que tu choisis (§2).
- **Pas de restauration d'un seul compte** : on restaure toute la plateforme. Rendre ses données à un invité se fait déjà par son export (Réglages › Compte).

## 7. Livraison

Une PR, **0.66.0**, sans migration : l'état des sauvegardes va dans le journal des tâches et dans `platform_settings`.

Ce qui sera vérifié :
- **Tests** :
  - une sauvegarde puis sa restauration sur une base de test, avec le même contenu à l'arrivée ;
  - une mauvaise phrase secrète refusée ;
  - le tri des sauvegardes gardées ;
  - le rattrapage au démarrage ;
  - l'alerte après 36 heures ;
  - la restauration qui refuse sans le mot « restaurer ».
- **Sur une copie de ta plateforme** (une base de brouillon) : une sauvegarde, puis une restauration complète.
- **Captures** de « La plateforme » avec l'état des sauvegardes.

Après la fusion, de ton côté :
1. choisir le dossier ;
2. écrire la phrase secrète dans `.env` ;
3. lancer `jobbot backup`, puis `jobbot restore <fichier> --essai`.

Je te donnerai les commandes exactes.

## Points à valider

1. **Chaque nuit, chiffrée, gardée 7 jours, 4 semaines, 6 mois** (§1).
2. **Le dossier**, à choisir par toi : iCloud Drive conseillé, grâce au chiffrement (§2).
3. **La phrase secrète** dans `.env`, écrite par toi, et la bibliothèque `cryptography` en plus (§3).
4. **L'essai de restauration chaque dimanche**, et l'alerte sur ton téléphone si ça échoue (§1, §4).
5. **La page « Confidentialité »** qui parle des sauvegardes et des 6 mois (§5).
6. **Une PR 0.66.0**, sans migration (§7).

## Écarts avec le cadrage

- **L'état des sauvegardes est dans Réglages › Plateforme**, et non dans « La plateforme », la page de présentation. L'alerte du téléphone mène là.
- **La tâche passe toutes les heures** (à la 17e minute) et décide elle-même : une sauvegarde à 3 h, heure suisse, ou dès que la dernière date de plus de 24 heures. Le rattrapage se fait donc dans l'heure qui suit le réveil du Mac, et pas seulement au démarrage du worker.
- **Une sauvegarde avec le rôle de l'API est refusée** : il ne voit pas tous les comptes, la sauvegarde serait incomplète sans le dire. Il faut l'accès propriétaire (`JOBBOT_MIGRATE_DATABASE_URL`), déjà dans ton `.env` depuis la 0.64.
- **Le mot de passe de la base** passe à `pg_dump` par l'environnement, jamais par sa ligne de commande : il n'apparaît pas dans la liste des processus.
- **La vraie restauration commence par un essai** dans une base à part. Elle ne vide la base que si l'essai réussit. Les fichiers de la sauvegarde sont remis par-dessus ceux du stockage ; un fichier plus récent que la sauvegarde reste là.
- **Changer de phrase secrète** ne rechiffre pas les anciennes sauvegardes : elles restent lisibles avec l'ancienne. C'est écrit dans `docs/securite.md`.
- **Vérifié sur une base de brouillon** remplie avec les données fictives de la démo, plutôt qu'une copie de ta plateforme : je ne copie pas tes données ni celles de tes invités. Résultats :
  - `jobbot backup` : 46 Ko, chiffrée ;
  - `jobbot restore --essai` : 45 tables, 466 lignes ;
  - les 36 candidatures effacées puis la vraie restauration : les 36 sont revenues, l'état d'avant a été sauvegardé, et la maintenance a été levée ;
  - la base d'essai est bien effacée à chaque fois ;
  - captures de Réglages › Plateforme.
- **Tests** : 508 côté serveur, dont 8 nouveaux (`test_backup.py`, et `~` dans le dossier développé en dossier personnel), et 297 côté interface, dont 1 nouveau.

## Complément 0.66.1 : restaurer par le seul nom

À la première utilisation, `jobbot restore jobA1-….jobA1backup --essai` répondait « Fichier introuvable ». La commande cherchait le fichier dans le dossier courant, alors que `jobbot backup --list` n'affiche que les noms. Désormais :
- un nom seul est cherché dans le dossier des sauvegardes ;
- `--list` affiche aussi le dossier ;
- le message d'un fichier introuvable dit où il a cherché.

Test ajouté.
