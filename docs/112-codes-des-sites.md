# 112 — Les codes et les messages des sites (version 0.82.0)

> Statut : **validé** le 2026-10-21 (« oui pour tout le 112 ») : le code dans la notification, l'extension qui remplit et clique « Continuer », les liens de confirmation ouverts par jobA1, les messages gardés 30 jours.
> Origine : ta session du 2026-10-21 avec le compte « eliot » : jobup demande un code à 6 chiffres envoyé à `eliot-1k93cq4e@joba1.ch`, et le code arrive dans ta boîte Gmail. « Comment un utilisateur va recevoir ses alertes chez lui ? », puis « n'y a-t-il pas moyen de le faire automatiquement, sans que l'utilisateur ait besoin de faire quelque chose ? ».
> Se construit sur docs/65 §3 (les liens « Confirmez votre alerte »), docs/104 (l'adresse à jobA1, les premières offres) et docs/25 (l'extension).

## Le constat

Quand un invité crée son alerte sur un site, ce site lui écrit **à son adresse jobA1**, pas seulement pour les alertes :

| Ce que le site envoie | Aujourd'hui |
|---|---|
| **un code de vérification** (« Entrez votre code », 6 chiffres, valable ~10 minutes) | arrive dans ta boîte de collecte ; **l'invité ne le voit nulle part** |
| **un lien « Confirmez votre alerte »** | repéré, affiché sur la page Alertes : l'invité l'ouvre lui-même |
| **un message du site** (bienvenue, alerte modifiée, mot de passe oublié) | rangé comme « alerte non reconnue » ; l'invité ne peut pas le lire |

Le relevé de la boîte se fait **toutes les 2 heures** : un code de 10 minutes est déjà mort quand jobA1 le lit.

## Ce qui ne peut pas être automatique

- **Créer le compte sur le site** à la place de la personne : un robot qui ouvre un compte en son nom, contre les conditions des sites et leurs protections. jobA1 ne le fait pas.
- **Taper le code dans une application du téléphone** : une application web ne peut pas remplir une page ouverte dans le navigateur ou dans une autre application. Sur téléphone, il reste à recopier le code.

## La proposition

### 1. Le code arrive en quelques secondes

- **La page qui demande le code se reconnaît** : l'extension jobA1 (si elle est installée) voit `auth.jobup.ch/…/challenge` (et l'équivalent des sites suivis connus) et prévient jobA1 qu'un code est attendu.
- **Sans extension**, la page Alertes propose **« J'attends un code »** au moment où l'assistant dit de créer l'alerte.
- Dans les deux cas, jobA1 **relève la boîte toutes les 15 secondes pendant 5 minutes**, pour ce compte seulement, puis revient au rythme habituel.

### 2. Le code reconnu et montré

- Un e-mail à l'adresse du compte qui n'est pas une alerte et qui contient **un code de 4 à 8 chiffres à côté des mots « code », « vérification », « Bestätigungscode », « verification code »** devient un **code du site** : le site, le code, l'heure.
- Il s'affiche **en haut de la page Alertes et dans la cloche** : « Code jobup : 482 913 », avec **« Copier »**.
- **Une notification sur le téléphone** l'annonce (voir le point à valider 1 sur ce qu'elle contient).
- Le code **s'efface au bout de 30 minutes**. Il ne part jamais à l'IA et n'est visible que par ce compte.

### 3. Sur ordinateur, le code rempli tout seul

- Sur la page qui demande le code, **l'extension le remplit** dès qu'il arrive chez jobA1 (elle demande le code de ce site, reçu il y a moins de 10 minutes, pour ce compte).
- Pour agir sans clic, l'extension demande **une fois** la permission sur les pages de connexion des sites connus (`auth.jobup.ch`, …). Sans cette permission, elle le fait au clic sur son icône, comme aujourd'hui.
- Elle **ne valide pas** à ta place (règle de l'extension, docs/25) : il reste « Continuer » (voir le point à valider 2).

### 4. Les liens de confirmation ouverts par jobA1

- Un lien « Confirmez votre alerte » d'un **site connu** (jobup, jobs.ch, Indeed, Job-Room, LinkedIn) est **ouvert par jobA1** dès qu'il arrive : une requête, `https` et adresse publique seulement, 4 redirections au plus.
- Si la page répond normalement, l'alerte est notée **confirmée** et la ligne « À confirmer » n'apparaît pas. Si le site demande une connexion ou une action (page de connexion, bouton à cliquer), rien n'est forcé : la ligne reste, à ouvrir soi-même.
- **Jamais** un lien de désinscription, de suppression ou de changement de mot de passe (la liste de refus de docs/65 §3 reste).

### 5. Les messages des sites lisibles

- Les autres e-mails des sites à l'adresse du compte (bienvenue, alerte modifiée, mot de passe oublié) vont dans **« Messages des sites »**, sur la page Alertes : le site, le sujet, la date, et le texte à l'ouverture (sans images ni pièces jointes).
- Un lien « réinitialiser le mot de passe » s'y affiche mais **n'est jamais ouvert par jobA1**.
- Gardés **30 jours**, puis effacés.

## Garde-fous

- **Le code d'un compte n'est visible que par ce compte** : il est rangé par l'adresse de destination, comme les alertes (docs/65 §3). Une adresse inconnue : rien n'est montré.
- **Pas dans la démo.**
- **Le relevé rapide** est limité : 5 minutes, 15 secondes, un compte à la fois, et au plus 6 fois par heure par compte.

## Écarts

- **Ce qui est un « message du site »** : un e-mail qu'aucun analyseur ne reconnaît (hors site lu par l'IA en attente : plafond, pas de clé), ou dans lequel l'IA ne trouve aucune offre. Une alerte reconnue mais vide ce jour-là reste une alerte. Un message relu plus tard avec des offres redevient une alerte.
- **Ni les codes ni les messages ne sont des alertes reçues** : ils ne comptent pas dans les preuves de recherche ORP, ni dans le nombre d'alertes d'un site, ni pour dire qu'une alerte marche.
- **« J'attends un code »** est un lien sous les codes, en haut de la page Alertes, toujours visible (pas seulement dans l'assistant). La page se met à jour toutes les 10 secondes pendant l'attente, et s'arrête dès qu'un code arrive.
- **Le relevé rapide** s'arrête au premier code reçu ; une alerte arrivée pendant ce temps suit son chemin habituel (filtre, page, note).
- **L'effacement** passe toutes les 15 minutes : le code disparaît du journal et la cloche affiche « Code expiré » ; la page Alertes, elle, ne montre plus un code de plus de 30 minutes. Codes et messages sont supprimés (avec leur e-mail) après 30 jours.
- **L'extension** reconnaît pour l'instant les pages de code de **jobup et jobs.ch** (`auth.jobup.ch`, `auth.jobs.ch`, même groupe). Elle ne remplit que si l'onglet est toujours sur la page du code au moment où il arrive. Nouvelle version **0.59.0**, à envoyer à Mozilla.
- **Le lien de confirmation** n'est noté confirmé que si la page répond sans demander de connexion (ni page de connexion, ni champ de mot de passe) ; sinon il reste « À confirmer ».
- **Le texte d'un message** est montré sans images ni liens actifs.

## Vérifié

- Tests backend : la reconnaissance des codes (français, allemand, anglais ; un téléphone, un code postal, une date, un prix ne sont pas des codes) ; un code reçu → rangé, dans la cloche et sur le téléphone avec le code, en haut des Alertes, absent des preuves ORP ; effacé après 30 minutes (« Code expiré »), supprimé après 30 jours ; l'extension ne lit qu'un code de moins de 10 minutes, du bon site ; les messages et leur texte ; les liens de confirmation (site connu accepté, page de connexion, site inconnu jamais ouvert, désinscription et mot de passe jamais) ; « J'attends un code » limité à 6 par heure ; le relevé rapide qui s'arrête au premier code ; la route de l'extension. 569 tests, ruff, mypy.
- Tests de l'interface et de l'extension : le code en grand et « Copier le code », l'attente et son arrêt, la limite ; les messages et leur texte à l'ouverture ; la page du code reconnue (et seulement elle), le champ rempli comme au clavier et « Continuer » cliqué, la plateforme prévenue puis le code attendu, rien si l'onglet a changé de page. 391 tests, lint, vue-tsc.
- Captures Playwright à 414 et 1280 px : le code en haut des Alertes, la recherche jobup, les messages des sites (une carte, des filets). Rien ne dépasse.

## Décisions (2026-10-21)

Ta réponse : « oui pour tout le 112, vas-y ». Retenu, pour chaque question, la première proposition : le code lui-même dans la notification, l'extension qui remplit **et** clique « Continuer », les liens de confirmation ouverts par jobA1 pour les sites connus, les messages gardés 30 jours.

### Les questions posées

1. **La notification sur le téléphone** : elle passe par le serveur de notifications (ntfy). Y mettre **le code lui-même** (« jobup : 482 913 », lisible sans ouvrir jobA1, mais le code transite par ce serveur), ou seulement **« Code jobup reçu »** (il faut ouvrir jobA1 pour le voir) ?
2. **L'extension** : remplir le code **et cliquer « Continuer »**, ou **seulement remplir** (comme pour les candidatures, rien n'est envoyé à ta place) ?
3. **Les liens de confirmation** : d'accord pour que jobA1 les ouvre lui-même pour les sites connus ?
4. **Les messages des sites** : les garder 30 jours, ou plus ?
