# 72 — La démo publique (version 0.59.0)

> Statut : **validé** le 2026-10-18.
> Origine : discussion du 2026-10-18 sur la demande de soutien à l'activité indépendante (SAI). jobA1 peut servir de **vitrine** : montrer ce que tu sais construire, sans compte, sans rien de personnel.

## 1. Le but

- Une adresse publique (par exemple `demo.joba1.ch`) où n'importe qui **visite jobA1 en entier**, en un clic, sans créer de compte.
- On y voit une recherche d'emploi **crédible et vivante** : des offres notées, des lettres et des CV préparés, un suivi sur trois mois, des preuves ORP, un bilan, des entretiens.
- Tout est **fictif**, et rien de ce qu'un visiteur fait n'est gardé.

## 2. Le principe : une installation à part, en « mode démo »

- **Une installation séparée**, avec sa propre base. Elle ne touche jamais ta plateforme ni tes données.
- Un réglage **`JOBBOT_DEMO=true`** la met en mode démo :
  - **pas de connexion** : le visiteur arrive directement sur Aujourd'hui, avec le compte fictif « Camille Exemple » ;
  - **lecture seule** : l'API refuse toute modification. Un clic sur « Enregistrer », « Marquer comme envoyée » ou « Générer » affiche « Dans la démo, rien n'est enregistré », au lieu d'une erreur ;
  - **rien ne tourne en arrière-plan** : pas de collecte d'e-mails, pas d'IA, pas de notifications, pas de tâches planifiées.
- **Garde-fou** : en mode démo, la plateforme refuse de démarrer si sa base contient un autre compte que le compte fictif. Le mode démo ne peut donc pas s'allumer par erreur sur ta vraie plateforme.
- Le visiteur n'est **pas l'exploitant** : la section « Plateforme » des Réglages (plafond de l'IA, comptes) n'apparaît pas.

## 3. Ce que le visiteur voit

- Une **bande en haut de chaque page** : « Démo : données fictives, rien n'est enregistré. » avec un lien vers « La plateforme » (la présentation) et vers le code source.
- **Toutes les pages** remplies :

| Page | Contenu fictif |
|---|---|
| Aujourd'hui | la semaine en cours, l'objectif ORP à 6 sur 10, deux relances, un entretien jeudi |
| Offres | une quarantaine d'offres notées (DevOps, Platform, SRE en Suisse romande), quelques-unes écartées par les prérequis |
| Préparation | des lettres et des CV déjà préparés pour plusieurs offres, en PDF |
| Suivi | trois mois de candidatures, avec leurs statuts, relances, entretiens et notes après entretien |
| Preuves ORP | les mois remis et le mois en cours, avec le PDF et la saisie Job-Room |
| Bilan | ce qui marche, par source, par note et selon les relances |
| Actualités et Formations | une sélection d'articles et de formations fictifs (sans images de sites réels) |
| Profil et Réglages | le profil de Camille, en lecture |

- **Les dates suivent le jour de la visite** : les données sont recalées sur la date du jour à chaque démarrage, pour que la démo ait toujours l'air d'être « cette semaine ».
- L'**assistant** est remplacé par un message : « Dans la démo, l'assistant est désactivé. » L'IA coûte, et une adresse publique attirerait les abus.
- L'**extension** : sa section dans Réglages renvoie à la fiche de la boutique de Mozilla, sans jeton à créer.

## 4. Les données fictives

- Une commande **`jobbot demo-seed`** remplit la base de démo à partir d'un jeu de données écrit dans le dépôt (`backend/src/jobbot/demo/`), **relu une fois par toi**.
- Entreprises, personnes et adresses **inventées** (« Exemple SA », « Démo Sàrl », rue du Test…), sans nom de vraie entreprise ni de vraie personne. Aucune donnée ne vient de ta base.
- Lettres et CV **écrits une fois pour la démo** et gardés dans le jeu de données : pas d'IA au moment de la visite.
- La commande efface la base de démo avant de la remplir. Elle refuse de tourner sur une base qui contient un vrai compte.

## 5. De ton côté : l'hébergement

C'est de l'infrastructure, donc à toi, comme le reste (docs/exploitation.md) :
- une petite installation de plus : l'API, le frontend et une base PostgreSQL à part ;
- l'adresse (`demo.joba1.ch` ou autre) ;
- les variables : `JOBBOT_DEMO=true`, et pas de clé d'IA, d'IMAP ni de ntfy ;
- `jobbot demo-seed` au déploiement, puis une fois par nuit pour repartir propre.

Je compléterai `docs/exploitation.md` avec ce contrat.

## 6. Ce qui change dans le code

| Où | Quoi |
|---|---|
| Serveur | réglage `JOBBOT_DEMO` ; entrée sans connexion sur le compte fictif ; refus des écritures (403, « démo ») ; garde-fou au démarrage ; tâches, IA, collecte et notifications coupées ; `jobbot demo-seed` et son jeu de données |
| Interface | bande « Démo » ; message à la place d'une erreur sur une action refusée ; assistant remplacé ; section Plateforme masquée ; « La plateforme » propose « Voir la démo » quand une adresse de démo est configurée |
| Dépôt | jeu de données fictif ; `docs/exploitation.md` ; lien vers la démo dans le README |

Pas de migration.

## 7. Livraison

| Étape | Qui |
|---|---|
| **0.59.0** : mode démo, jeu de données, `jobbot demo-seed`, bande et messages | moi (une PR) |
| Relecture du jeu de données fictif (aucun nom réel) | toi, dans la PR |
| Hébergement de l'installation de démo, seed nocturne | toi |
| Lien « Voir la démo » activé, une fois l'adresse en ligne | moi (petite PR) |

## Points à valider

1. **Une installation séparée en mode démo**, sans connexion, en **lecture seule**, avec un garde-fou contre l'allumage sur une vraie base (§2).
2. **Le contenu fictif** des pages, recalé sur la date du jour (§3, §4).
3. **Pas d'IA ni d'assistant** dans la démo (§3).
4. **`jobbot demo-seed`**, à relancer chaque nuit (§4, §5).
5. **L'hébergement est de ton côté** (§5).
6. **Une PR 0.59.0**, sans migration (§7).

## Écarts avec le cadrage

- **Deux comptes dans la base de démo** : l'exploitant inerte (sans mot de passe, comme sur une installation neuve) et le compte fictif « demo ». Le visiteur est donc un compte ordinaire, sans cas particulier dans le code : pas de rubrique Plateforme, pas de réglages réservés.
- **Lecture seule par le middleware** : en mode démo, toute requête qui n'est pas une lecture reçoit 403, avec `{"detail": "Dans la démo, rien n'est enregistré.", "demo": true}`. L'interface montre ce message dans une bulle ; la valeur modifiée revient d'elle-même (statut d'une candidature, par exemple).
- **Dates** : recalées au moment du remplissage (`jobbot demo-seed`, chaque nuit), plutôt qu'à chaque démarrage. Le mois en cours s'arrête à la veille ; l'entretien à venir est le jeudi suivant.
- **Assistant** : sans clé d'IA, il disparaît de lui-même, comme sur toute installation sans clé ; pas de message à la place.
- **Boutons sans objet masqués** : « Collecter » (barre du haut et menu) et « Relever » (Actualités). Les autres actions restent visibles et répondent par le message de la démo.
- **Le vrai filtre** trie les offres fictives : trois sont écartées, pour le lieu (Zürich), un stage et un taux de 40 %. Les lieux portent leur canton (« Lausanne, VD »), comme dans les alertes.
- **Jeu de données** : 36 offres, 36 candidatures sur quatre mois (dont 11 saisies à la main pour l'historique ORP), un entretien passé avec son retour, un refus après entretien, un entretien jeudi, deux contacts, deux formations suivies (catalogue du dépôt), six articles d'exemple qui renvoient au dépôt. Entreprises, personnes et adresses inventées, reconnaissables (« Exemple SA », « Démo Sàrl », « Alex Démo », « rue de l'Exemple ») ; un test le vérifie.
- **Extension** : la section des Réglages reste celle de la 0.58 (boutique pas encore en ligne) ; créer un jeton y est refusé comme toute écriture.
- **« Voir la démo »** sur « La plateforme » de toute installation, quand `JOBBOT_DEMO_URL` est réglé.
- **Tests** : sur une base à part (`jobbot_demo_test`, créée par les tests), pour que le remplissage ne touche pas la base des autres tests. Mutations vérifiées : sans le verrou d'écriture, ou sans le garde-fou au démarrage, un test échoue.
- **Essayé** : la démo complète en local (API en mode démo sur une base de démo, interface), toutes les pages parcourues, une action refusée avec son message.

## Complément 0.59.1 : `make demo`

- **Le besoin** (2026-10-18) : montrer la démo depuis son ordinateur, par exemple à un rendez-vous à l'ORP, avant de la mettre en ligne.
- **`make demo`** fait tout en une commande :
  - crée la base `jobbot_demo` si elle n'existe pas ;
  - applique les migrations, puis `jobbot demo-seed` (données fictives recalées sur le jour) ;
  - lance l'API en mode démo (port 8200) et l'interface (port 5200), puis ouvre http://localhost:5200 dans le navigateur.

  Ctrl-C arrête tout.
- **À côté de `make dev`** : base et ports à part, la vraie plateforme n'est pas touchée. Les clés d'IA, la boîte e-mail et ntfy du `.env` sont neutralisés pour la démo (variables vides), et aucun worker n'est lancé.
- **Essayé** : `make demo` sur une base neuve (créée, migrée, remplie : 36 candidatures), API en mode démo et interface qui répondent. La base d'essai est ensuite supprimée : elle se recrée au premier `make demo`.
