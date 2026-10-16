# 65 — De vrais comptes : plusieurs chercheurs d'emploi sur la même plateforme (versions 0.50 à 0.53)

> Statut : **validé** le 2026-10-16, livré (0.50.0 à 0.53.0).
> Suite de docs/17 (option B, « plus tard ») : aujourd'hui, la plateforme a **un seul compte** (le tien, créé par `jobbot set-password`), et tout est commun : offres, candidatures, preuves ORP, profil, réglages, IA. Les profils d'essai ne changent que les Actualités et les Formations. Le but : que d'autres chercheurs d'emploi utilisent la plateforme, chacun avec **ses** données, sans jamais voir celles des autres.

## 1. Ce que chacun a à soi, ce qui reste commun

| À soi (séparé par compte) | Commun à tous |
|---|---|
| Offres reçues, leur note et leur tri ; critères (Ce que je cherche) | Le catalogue des entreprises, sites d'emploi et logos |
| Candidatures, contacts, relances, entretiens, retours | Les sources d'actualités et leurs articles |
| Preuves ORP, objectif, date limite | Le catalogue des formations |
| Profil : coordonnées, CV et documents, blocs de profil | Les tâches techniques (collecte, notation en lot) |
| Alertes suivies, « Mon domaine », formations marquées | |
| Discussions avec l'assistant, notifications | |
| Dépense de l'IA, plafond du mois | |
| Lien d'agenda, jetons de l'extension | |

- Une offre reçue par deux personnes existe **deux fois**, une par compte : chacune a sa note (calculée sur son profil), son statut, ses candidatures. Plus simple et sans fuite possible.
- Concrètement : **27 tables** sur 36 reçoivent le compte auquel chaque ligne appartient ; les fichiers déposés vont dans un dossier par compte.
- **Tes données actuelles deviennent celles de ton compte** : rien ne change pour toi.

## 2. Qui peut créer un compte : sur invitation

- Pas d'inscription ouverte. **Toi seul** crées une invitation (Réglages › Comptes) : un lien à usage unique, valable 7 jours, que tu transmets toi-même (e-mail, message).
- La personne choisit son identifiant et son mot de passe sur la page d'invitation. Mots de passe comme aujourd'hui (scrypt, essais limités).
- **Mot de passe oublié** : sans envoi d'e-mail par la plateforme, c'est toi qui génères un lien de réinitialisation (valable 24 h) et le transmets. L'envoi automatique d'e-mails pourra venir avec le déploiement public.
- Tu peux **suspendre** un compte (plus de connexion, plus de collecte, données gardées) ou le **supprimer**.

## 3. Le point délicat : les alertes e-mail de chacun

Aujourd'hui, la plateforme lit **ta** boîte Gmail (en lecture seule). Les autres ne vont pas donner le mot de passe de leur boîte. Trois façons :

| | **A. Une adresse de réception par compte** (proposé) | B. Chacun relie sa propre boîte | C. Pas d'alertes e-mail |
|---|---|---|---|
| Principe | la boîte de la plateforme reçoit pour tous ; chaque compte a son adresse, par exemple `jobbot+k7f3q9@gmail.com` (Gmail livre tout dans la même boîte, la partie après « + » dit à qui c'est) | mot de passe d'application de chaque personne, gardé chiffré | seulement l'extension et l'ajout à la main |
| Pour la personne | elle crée ses alertes sur jobup, jobs.ch… avec **cette adresse** au lieu de la sienne | elle crée un mot de passe d'application, le colle dans la plateforme | rien à configurer, mais plus de veille automatique |
| Ce qu'on garde | aucun mot de passe d'autrui | les mots de passe de boîtes des autres : une responsabilité lourde | — |

Je propose **A** : l'assistant de création des alertes affiche l'adresse du compte à la place de la tienne. La collecte range chaque e-mail selon l'adresse de destination ; un e-mail adressé à une adresse inconnue n'est rangé nulle part. Les e-mails de confirmation des sites (« confirmez votre alerte ») apparaissent dans la page Alertes du compte, avec leur lien. **Ta** collecte actuelle continue telle quelle pour ton compte.

Côté infrastructure (à toi) : une boîte dédiée à la plateforme plutôt que ta boîte personnelle, dès que d'autres comptes existent. La lecture reste en lecture seule.

## 4. L'IA, les notifications, les réglages

- **IA** : ta clé, pour tous. Chaque compte a **son plafond mensuel** (5 CHF par défaut, que tu fixes par compte), en plus d'un **plafond total** de la plateforme. L'assistant, la notation et les lettres d'un compte ne lisent que les données de ce compte ; les coordonnées et noms de contacts ne partent toujours jamais à l'IA.
- **Notifications** : chaque compte a son sujet ntfy, tiré au hasard, affiché dans ses Réglages.
- **Réglages** : ce qui touche la recherche (objectif ORP, sites suivis, seuils, Mon domaine, notifications, agenda, extension) est **par compte**. Ce qui touche l'installation (clé d'IA, boîte de réception, plafond total, comptes) n'est visible que **pour toi**, dans une rubrique « Plateforme ».
- **Profils d'essai** : ils restent un outil à toi (juger les Actualités pour un autre métier) ; les autres comptes n'en ont pas besoin, leur « Mon domaine » est le leur.

## 5. Ce que tu vois des autres

- Rubrique **Plateforme › Comptes** : identifiant, date de création, dernière connexion, dépense d'IA du mois, offres reçues ce mois. Inviter, suspendre, supprimer, lien de réinitialisation.
- **Jamais leurs données** : ni offres, ni candidatures, ni documents, ni discussions. Aucune page ne permet de « voir en tant que ».

## 6. Données personnelles (loi sur la protection des données)

En accueillant d'autres personnes, tu deviens responsable de leurs données (CV, coordonnées, candidatures, ORP). Ce que la plateforme fournit :

- une page **« Tes données »** : ce qui est gardé, où, combien de temps, qui y a accès (toi en tant qu'exploitant, pour l'infrastructure seulement), et ce qui part à l'IA ;
- **exporter** tout son compte (une archive : données en JSON, documents, lettres, preuves ORP) ;
- **supprimer** son compte : tout est effacé, fichiers compris, après confirmation ;
- les durées actuelles restent (discussions de l'assistant effacées après 30 jours, e-mails jamais gardés bruts).

Le texte juridique lui-même (mentions, hébergeur, contact) est à toi ; la page prévoit sa place.

## 7. La sécurité de la séparation

C'est le cœur du chantier : **une seule fuite entre comptes serait grave.**

- Toute lecture et écriture passe par le compte de la session ; aucune route ne prend un compte en paramètre.
- Un **test automatique** crée deux comptes, remplit le premier, puis appelle **toutes les routes de l'API** avec le second : il ne doit rien voir, rien modifier, rien télécharger du premier. Une nouvelle route non couverte fait échouer le test.
- Les tâches de fond (collecte, notation, relances, actualités) travaillent compte par compte.
- **En option, une seconde barrière dans la base** (« sécurité au niveau des lignes » de PostgreSQL) : même une requête mal écrite ne verrait que les lignes du compte en cours. Plus sûr, un peu plus de travail ; je le recommande.

## 8. Livraison en quatre PR

| Version | Contenu | Visible pour toi |
|---|---|---|
| **0.50.0** | Chaque ligne rattachée à un compte, tout rangé dans le tien ; lectures et tâches par compte ; le test des deux comptes ; la barrière dans la base si retenue | rien ne change |
| **0.51.0** | Invitations, comptes, suspension, réinitialisation ; réglages par compte et rubrique Plateforme ; plafond d'IA par compte | Plateforme › Comptes |
| **0.52.0** | Adresse de réception par compte, collecte rangée par destinataire, e-mails de confirmation dans Alertes | l'assistant des alertes montre ton adresse actuelle |
| **0.53.0** | « Tes données », export, suppression du compte | Réglages › Compte |

Chaque PR est vérifiée avec deux comptes sur l'instance de test (jamais sur ta base).

## Points à valider

1. **Ce qui est à soi et ce qui est commun** ; une offre par compte ; tes données dans ton compte (§1).
2. **Sur invitation seulement**, réinitialisation par un lien que tu génères (§2).
3. **Les alertes** : option A, une adresse de réception par compte, et une boîte dédiée à la plateforme (§3).
4. **IA** : ta clé, un plafond par compte (5 CHF par défaut) et un plafond total ; réglages par compte, rubrique Plateforme pour toi (§4).
5. **Tu ne vois jamais les données des autres**, seulement l'usage (§5).
6. **Tes données** : page d'information, export, suppression (§6).
7. **La séparation** : test des deux comptes sur toutes les routes, et la barrière dans la base (§7).
8. **Quatre PR**, de 0.50.0 à 0.53.0 (§8).

## Écarts avec la livraison de 0.50.0

- **La séparation est faite par la base** (sécurité au niveau des lignes), pas requête par requête : la colonne `user_id` est remplie d'office avec le compte en cours, et la base ne montre que ses lignes. Les 150 routes et les tâches n'ont presque pas changé ; une requête oubliée ne peut pas fuir. L'application endosse pour cela un rôle PostgreSQL sans privilège (`jobbot_app`), créé par la migration.
- **27 tables** et non 26 : les lots de notation de l'IA (`llm_batches`) sont aussi rangés par compte.
- **Ton compte** : tes données vont au premier compte créé, `kevin`. Le second compte de ta base, `infirmiere`, devient un compte **vide**, séparé du tien (il partageait tout jusqu'ici). Vérifié sur une copie de ta base, effacée ensuite : 362 offres, 13 candidatures et 12 blocs de profil dans ton compte, rien dans l'autre.
- **Ce qui reste à l'exploitant** jusqu'aux versions suivantes : la collecte e-mail (ta boîte), les notifications ntfy (ton sujet) et leur bouton d'essai, et les modifications des données communes (sites d'emploi, catalogue des sources d'actualités ; **403** pour un autre compte). S'abonner ou se désabonner d'une source reste à chaque compte ; une source n'est effacée que si plus aucun compte ne la suit.
- **Plafond de l'IA** : il se calcule désormais sur la dépense du compte ; le plafond total de la plateforme vient en 0.51.
- **Tâches** : planifiées, elles passent compte par compte (l'échec de l'un n'arrête pas les autres) ; lancées depuis un bouton, pour le compte qui a cliqué seulement.
- **Fichiers** : les nouveaux documents et e-mails vont sous `accounts/<compte>/` ; les anciens restent où ils sont.
- **Le test des deux comptes** appelle les 153 routes de l'API (lues dans le schéma : une route ajoutée plus tard est testée d'office) avec un corps valide et les numéros des lignes de A, plus l'extension avec son propre jeton et le lien d'agenda : B ne voit, ne modifie ni ne supprime rien de A, ni des données communes. Un second test vérifie la base elle-même (lecture et écriture au nom d'un autre compte refusées, rien sans compte), un troisième les tâches compte par compte.
- **À faire de ton côté** : `make migrate` avant de relancer `make dev` (les migrations ne se lancent jamais au démarrage).

## Écarts avec la livraison de 0.51.0

- **Invitations** : Réglages, rubrique **Plateforme** (visible par toi seul) : « Inviter quelqu'un » montre une fois le lien `/acces/…`, valable 7 jours, à transmettre toi-même ; les invitations en attente se retirent. La page du lien demande l'identifiant (40 caractères au plus, pas déjà pris) et le mot de passe deux fois (12 caractères au moins), puis ouvre la session.
- **Nouveau mot de passe** : « Lien de nouveau mot de passe » sur la ligne du compte, valable 24 h ; un nouveau lien remplace le précédent ; ses autres sessions sont fermées.
- **Suspendre** : plus de connexion (« compte suspendu »), sessions fermées, plus de tâches ; ses données restent. **Supprimer** : il faut écrire son identifiant pour confirmer ; le compte, toutes ses lignes et son dossier de fichiers sont effacés. Ton compte ne se suspend ni ne se supprime.
- **Ce que tu vois** : identifiant, création, dernière connexion, dépense de l'IA du mois sur son plafond, offres reçues ce mois. Les totaux viennent de deux fonctions de la base, qui ne rendent que ces chiffres.
- **IA** : chaque compte invité a 5 CHF par mois par défaut, que tu changes sur sa ligne ; il voit son plafond sans pouvoir le changer. Ton plafond reste celui de tes Réglages (rubrique IA). Plafond total de la plateforme : 50 CHF par mois par défaut, réglable ; atteint, l'IA s'arrête pour tous, et la carte de la dépense le dit.
- **Notifications** : un compte invité choisit « Recevoir sur mon téléphone » ; la plateforme lui tire un sujet ntfy au hasard, qu'il suit dans l'application ; « Arrêter » l'efface. Rien ne part vers ntfy sans ce choix. Toi, tu gardes le sujet de l'installation.
- **Compte neuf** : son profil principal est créé à sa première connexion (ou à l'invitation) et suit d'office les articles « marché de l'emploi », comme un profil d'essai. Le compte `infirmiere` de ta base en aura un à sa prochaine connexion.
- **Profils d'essai** : créer, dupliquer ou supprimer un profil d'essai est réservé à l'exploitant (**403** sinon), et la section n'apparaît pas pour les autres.
- **Pas encore** : les sites d'emploi suivis restent communs et réservés à l'exploitant ; ils passeront par compte avec les adresses de réception (0.52).
- **Vérifié** : sur l'instance de test, une invitation créée dans la rubrique Plateforme, le compte « camille » créé par son lien, qui arrive sur un Aujourd'hui vide (aucune des offres de l'exploitant) et voit son plafond fixé et l'activation des notifications ; la rubrique Plateforme ne lui apparaît pas.

## Écarts avec la livraison de 0.52.0

- **L'adresse** : la plateforme lit toujours une seule boîte, la tienne (`JOBBOT_IMAP_USER`, ou `JOBBOT_MAIL_ADDRESS` si les alertes arrivent à une autre adresse de la même boîte). Toi, tu gardes cette adresse : rien ne change pour tes alertes. Un compte invité reçoit à `boite+code@domaine` (code de 8 caractères, créé à la première visite de ses Alertes), que l'assistant des alertes et « Gérer mes alertes » lui montrent.
- **La collecte** lit la boîte une fois, puis range chaque e-mail selon son adresse de destination (`Delivered-To`, `To`, `Cc`…) : un code connu, ce compte ; aucune adresse « plus » de la boîte, toi, comme avant ; un code inconnu (compte supprimé) ou un compte suspendu, nulle part. Les e-mails déjà rangés, dans n'importe quel compte, ne sont pas relus. Le filtre tourne pour chaque compte qui a reçu des offres ; la lecture jobup et la notation, pour tous, comme après chaque collecte.
- **E-mails de confirmation** : un e-mail non reconnu qui demande de confirmer (français, allemand, anglais, italien) garde son lien `https://` (jamais celui de désabonnement). La page Alertes du compte montre « À confirmer » avec un bouton « Confirmer ↗ » qui ouvre le lien dans un nouvel onglet ; la ligne s'en va ensuite. La plateforme n'ouvre jamais ce lien elle-même.
- **Sites suivis** : la pause d'un site vaut pour le compte (ta pause actuelle est reprise dans ton compte). Ajouter, retirer ou proposer un site reste à toi : la liste des sites et de leurs expéditeurs est commune, elle sert à reconnaître les e-mails de tous.
- **Pas fait** : envoyer les e-mails de confirmation au compte par e-mail (la plateforme n'envoie pas d'e-mail) ; une boîte dédiée à la plateforme reste conseillée dès qu'il y a d'autres comptes (§3), c'est ta configuration.
- **Vérifié** sur l'instance de test, connecté en « camille » : l'encadré « À confirmer » et son bouton, et l'étape 2 de l'assistant qui donne son adresse `…+code@…`.

## Écarts avec la livraison de 0.53.0

- **La page « Tes données »** (`/tes-donnees`) se lit sans connexion, avant même d'accepter une invitation (l'invitation y renvoie) : ce qui est gardé, où et combien de temps (discussions 30 jours, notifications 90 jours, le reste jusqu'à la suppression du compte), qui y a accès (la personne ; l'exploitant voit l'usage, jamais les données), ce qui part à l'IA (offres, blocs de profil, questions, texte du CV pour les propositions de blocs, alertes lues par l'IA ; jamais les coordonnées ni les noms des contacts), ntfy seulement si activé.
- **Tes mentions** : Réglages, rubrique Plateforme, « Mentions de la page Tes données » (responsable, contact, hébergeur), affichées en bas de la page ; sans elles, la page le dit.
- **Exporter** (Réglages › Compte, tous les comptes, toi compris) : une archive ZIP avec `data/<table>.json` pour chacune des 28 tables rangées par compte, les documents déposés et les e-mails d'alerte reçus, plus un LISEZ-MOI. Les empreintes des jetons ne sont pas reprises. Les PDF (lettres, CV, preuves ORP) ne sont pas régénérés : leur contenu est dans les données, et ils se téléchargent toujours depuis leurs pages.
- **Supprimer mon compte** : pour un compte invité, avec son mot de passe ; tout est effacé (lignes et dossier de fichiers), la session se ferme. Ton compte ne se supprime pas depuis la plateforme.
- **Vérifié** : un test ouvre l'archive d'un compte et n'y trouve rien d'un autre ; sur l'instance de test, la page publique sans connexion, puis « camille » qui exporte son archive (`jobA1-camille-2026-10-16.zip`).
