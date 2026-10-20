# 102 — S'inscrire, sur demande (version 0.73.0)

> Statut : **validé** le 2026-10-20.
> Origine : ta remarque du 2026-10-20, « on ne peut pas faire de nouveaux comptes, il faudrait pouvoir s'inscrire », puis ton choix : **l'inscription sur demande**.
> Change la règle de docs/65 §2 (« sur invitation seulement »). Les invitations restent.

## Le principe

- **N'importe qui peut demander un compte** depuis la page de connexion. Il choisit son identifiant et son mot de passe.
- **Le compte attend ta validation.** Tant que tu ne l'as pas acceptée, la personne ne peut pas se connecter, et rien ne tourne pour elle : ni collecte, ni IA, ni tâches.
- **Tu acceptes ou refuses** dans Réglages › Plateforme. Refuser efface la demande.
- **La plateforme n'envoie toujours pas d'e-mail.** La personne revient se connecter ; si tu veux la prévenir, tu le fais toi-même.

## Le parcours de la personne

1. **Page de connexion** : sous le formulaire, « Pas encore de compte ? **Créer un compte** » (au lieu de « L'accès se fait sur invitation »).
2. **Page « Créer un compte »** (`/inscription`), sur le modèle de la page d'invitation (`/acces/…`) :
   - l'identifiant (40 caractères au plus, unique) ;
   - le mot de passe (12 caractères au moins), deux fois ;
   - **« Un mot pour l'exploitant »**, facultatif (300 caractères au plus) : qui tu es, comment tu as connu jobA1. Il t'aide à décider.
   - une case à cocher : « J'ai lu ce que deviennent mes données », avec le lien vers « Tes données » ;
   - le bouton « Envoyer ma demande ».
3. **Après l'envoi** : « Ta demande est envoyée. Tu pourras te connecter dès que l'exploitant l'aura acceptée. » Avec un lien vers la page de connexion.
4. **Une connexion avant l'acceptation** répond : « Ton compte attend encore la validation de l'exploitant. » La réponse ne dit rien de plus, et seulement si le mot de passe est juste. Sinon c'est le message habituel, pour ne pas révéler qu'un identifiant existe.
5. **Une fois acceptée**, la personne se connecte normalement et arrive sur l'accueil (docs/66), comme un compte invité.

## Ce que tu vois (Réglages › Plateforme)

- **Une rubrique « Demandes de compte »**, en tête quand il y en a. Chaque demande montre :
  - l'identifiant ;
  - la date ;
  - le mot laissé.
- **Deux actions** par demande :
  - **« Accepter »** : le compte devient actif, avec le plafond d'IA par défaut d'un compte invité (5 CHF) ;
  - **« Refuser »** : la demande et le compte sont effacés.
- **Un interrupteur « Accepter des demandes de compte »**, activé par défaut. Éteint, la page « Créer un compte » dit « Les demandes de compte sont fermées pour le moment », et le lien de la page de connexion disparaît.
- **La cloche** : une nouvelle demande t'arrive comme une alerte (« Nouvelle demande de compte : *identifiant* »). Elle arrive aussi par ntfy, si tu l'as réglé.
- **Les invitations** (lien à usage unique) restent. Un compte invité est accepté d'office.

## Les garde-fous

- **Pas plus de 20 demandes en attente.** Au-delà, la page dit que les demandes sont fermées pour le moment.
- **3 demandes par heure** depuis une même adresse IP (le même mécanisme que la connexion).
- **Un champ piège invisible** : rempli, la demande est ignorée en silence. Les robots le remplissent, les personnes ne le voient pas. Pas de CAPTCHA.
- **Une demande sans réponse est effacée après 30 jours**, par la tâche de maintenance.
- **Un compte en attente n'a rien** : pas de profil, pas d'adresse de réception, pas de tâche. Il ne compte pas dans le plafond d'IA.
- **La démo** n'a pas d'inscription.
- **Les journaux** gardent l'identifiant et l'adresse IP de la demande, jamais le mot de passe ni le mot laissé.

## Comment

- **Base** : deux colonnes sur `users`, par une migration :
  - `approved_at`, la date d'acceptation (les comptes existants prennent leur date de création) ;
  - `signup_note`, le mot laissé, effacé à l'acceptation.

  Un compte en attente a `approved_at` vide.
- **API** :
  - `POST /api/auth/signup` crée le compte en attente ;
  - `GET /api/auth/signup` dit si les demandes sont ouvertes ;
  - `POST /api/platform/accounts/{id}/approve` et `DELETE` sur le même compte (exploitant seul).
- **La connexion, les sessions et le worker** ignorent les comptes en attente.
- **Docs** : `docs/65` (§2 annoté), `docs/securite.md`, `docs/78-securite.md` et `docs/exploitation.md` suivent la nouvelle règle.

## Vérifié avant la PR

- **Tests serveur** :
  - la demande (identifiant pris, mot de passe trop court, case non cochée, champ piège, limite par IP, 20 en attente, demandes fermées, démo) ;
  - la connexion refusée tant que le compte attend, sans révéler l'identifiant ;
  - accepter et refuser (exploitant seul, 403 sinon) ;
  - l'effacement après 30 jours ;
  - aucune tâche pour un compte en attente.
- **Tests interface** :
  - le lien « Créer un compte » ;
  - la page et son message final ;
  - les demandes dans la Plateforme ;
  - l'interrupteur.
- **L'audit des rangées** est vide.
- **Captures**, en clair et en sombre, sur ordinateur et sur téléphone :
  - la page de connexion ;
  - « Créer un compte » ;
  - la demande envoyée ;
  - les demandes dans la Plateforme.

## Écarts

- **La limite de 3 demandes par heure et par adresse compte tous les essais**, même refusés : sinon « identifiant déjà pris » permettrait de tester des identifiants en masse. La page vérifie donc, avant d'envoyer, l'identifiant, le mot de passe (12 caractères, deux fois le même), la case et la longueur du mot laissé.
- **Les demandes sont aussi fermées** quand la connexion est désactivée, et tant que l'exploitant n'a pas lancé `jobbot set-password` : sinon une installation neuve pourrait être prise par le premier venu. Pendant une maintenance, l'inscription répond 503 ; la connexion reste ouverte.
- **Une demande réussie répond 204**, comme les autres routes de connexion.
- **`approved_at` vaut la date du jour par défaut** : les invitations, `set-password` et la démo restent acceptés sans rien changer. L'inscription le force à vide.
- **L'effacement après 30 jours** passe par la tâche quotidienne `reminders`, au tour de l'exploitant : il n'y avait pas de tâche de maintenance à part.
- **La base** : pas de nouvelle règle d'accès. L'inscription crée le compte au nom de l'exploitant, comme une invitation. La migration `0060` met à jour `active_accounts()` et `account_of_session()` pour ignorer les comptes en attente.
- **Une réinitialisation ou une suspension** d'un compte en attente répond 409 : il faut d'abord accepter ou refuser.
- **Refuser** demande une confirmation, comme suspendre un compte.
- **L'interrupteur** est dans la carte « Comptes », au-dessus de « Inviter quelqu'un ».
- **La page de connexion** : « Pas encore de compte ? Créer un compte » et « Données personnelles » sont sur deux lignes.
- **Vérifié** :
  - 540 tests serveur (10 nouveaux : tous les cas de la demande, la connexion en attente, accepter et refuser, l'effacement, aucune tâche) ;
  - 343 tests de l'interface (nouveaux : la page « Créer un compte », le lien, la connexion en attente, les demandes dans la Plateforme, l'interrupteur) ;
  - lint et typecheck ;
  - la migration descendue puis remontée, sur la base de test ;
  - audit des rangées vide ;
  - le parcours entier sur une instance de test : deux demandes, l'alerte dans la cloche, la connexion refusée tant que la demande attend, les demandes dans la Plateforme ; captures en clair, en sombre et sur téléphone.
  - Un test du Suivi (`ApplicationsView`) échoue depuis le 20 octobre, sur main aussi : sa donnée de test tombe sur la date du jour. À corriger à part.
