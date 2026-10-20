# 104 — Les premiers pas d'un nouveau compte (versions 0.75.0, 0.79.0 et 0.80.0)

> Statut : **0.75.0 validée** le 2026-10-20 ; **0.79.0 validée** le 2026-10-20 (le domaine `alertes.joba1.ch`, le nom dans l'adresse, un bouton « Copier » en attendant) ; **0.80.0 à valider** (décalée par docs/106, docs/108 et docs/110) (points en fin de page).
> Origine : ta session avec le nouveau compte « eliot » du 2026-10-20, cinq captures sur téléphone, puis tes choix : un domaine à jobA1 pour l'adresse, une lecture des recherches publiques pour les premières offres, deux boutons égaux.

## Ce que montre la session

| N° | Écran | Ce qui ne va pas |
|---|---|---|
| 1 | Accueil, « C'est prêt ! » | les « Modifier » en texte flottent à droite, sans structure |
| 2 | Offres | « 0 offres » le premier jour : il faut attendre les premières alertes |
| 3 | Alertes, étape 3 | l'adresse affichée est celle de l'exploitant (`kevin.dinocera+code@gmail.com`) |
| 4 | Alertes, étape 2 | « Passer ce site › » en lien, à côté d'un bouton plein |
| 5 | Alertes, étape 1 | l'exemple « Mots (DevOps) » n'a rien à voir avec pâtissier |

## 0.75.0 — L'interface (points 1, 4, 5)

1. **Le récapitulatif de l'accueil** : chaque ligne devient une carte entière cliquable (bordure, padding 0,75 × 1 rem, hauteur commune des contrôles). Un **crayon** à droite remplace « Modifier » : gris, bleu au survol avec la bordure. Le nom accessible reste « … — modifier ». Les lignes font toutes la même largeur (24 rem au plus).
4. **Les boutons d'un site** : « J'ai créé l'alerte » (plein) et « Plus tard » (contour), **côte à côte et de même taille**. L'avancée passe sur la ligne de l'étape : « Étape 2 sur 3 · site 2 sur 5 ». Plus de flèche, plus de lien.
5. **Les exemples des champs** suivent la recherche du compte : « Mots (pâtissier) », et le lieu de la recherche s'il y en a un (sinon « Lausanne »). Sans recherche : « Mots (ton métier) ».

Le changement vaut pour l'ordinateur aussi : ce sont des mots et des boutons, pas une mise en page propre au téléphone.

## 0.79.0 — Une adresse à jobA1 (point 3)

Aujourd'hui, jobA1 lit une seule boîte, la tienne, et donne à chaque compte `ta-boîte+code@gmail.com` (docs/65 §3). Avec l'adresse d'Eliot, il faudrait lire sa boîte, ce que jobA1 s'interdit.

**Le choix** : une adresse à jobA1, du type `eliot-pw99qlm7@alertes.<domaine>`.
- **Le domaine** redirige tout ce qui arrive sur `alertes.<domaine>` (« catch-all ») vers ta boîte de collecte. Le code serveur continue de lire une seule boîte.
- **Le routage** (`mail/addresses.py`) reconnaît le code dans la partie locale (`nom-code@alertes…`) en plus de `+code`. Les adresses déjà données aux sites continuent de marcher.
- **Un réglage** `JOBBOT_ALERT_DOMAIN` : vide, rien ne change ; rempli, les nouveaux comptes reçoivent l'adresse du domaine. L'exploitant garde sa propre adresse.
- **Le nom** dans l'adresse vient du nom du compte, en minuscules et sans accents. Le code empêche de deviner l'adresse d'un autre compte.

## 0.80.0 — Des offres dès le premier jour (point 2) — à valider

**Le choix** : juste après l'accueil, jobA1 lit **une fois** les pages publiques de recherche pour le métier et les lieux du compte, sans se connecter à aucun compte (docs/01 §1 reste vrai).
- **Les sources** : jobup (sa page de recherche publique, déjà lue offre par offre depuis docs/05) et Job-Room (la recherche publique de job-room.ch). À vérifier d'abord : leurs conditions d'utilisation et leur `robots.txt`. Une source qui l'interdit est laissée de côté.
- **Combien** : 20 offres au plus par source, une requête toutes les 2 s, comme `enrich`.
- **Ensuite** : les offres passent par le filtre et la note habituels, et la page Offres dit « Premières offres trouvées sur jobup et Job-Room ; tes alertes prennent le relais dès demain ». Les alertes restent la source de tous les jours.
- **Pas en démo**, pas sans métier, et une seule fois par compte (on peut la relancer depuis Alertes).

## Points à valider (0.79.0 et 0.80.0)

1. **Le domaine** : lequel ? Il faut un domaine (ou un sous-domaine) dont tu règles les e-mails, avec une redirection « catch-all » vers ta boîte de collecte (Cloudflare Email Routing, ImprovMX…).
2. **Le format de l'adresse** : `eliot-pw99qlm7@alertes.<domaine>` te va-t-il, ou préfères-tu le code seul (`pw99qlm7@…`) ?
3. **Les sources de la première lecture** : jobup et Job-Room seulement, ou aussi Indeed (plus strict sur la lecture automatique) ?
4. **20 offres par source** : assez pour le premier jour ?

## Vérifié (0.75.0)

- Tests : le crayon sur chaque ligne du récapitulatif, sans « Modifier » écrit ; l'exemple « Mots (DevOps) » qui suit la recherche ; « site 1 sur 2 » sur la ligne de l'étape ; « J'ai créé l'alerte » et « Plus tard » (contour).
- Capture à 414 px : le récapitulatif, l'étape 1 et l'étape 2 de l'assistant.

## Complément 0.79.0 : l'adresse à jobA1, faite

Ton retour du 2026-10-20 : « l'utilisateur eliot reçoit toujours cette information qui correspond à mes informations » (l'étape 3 de l'assistant des alertes montrait `kevin.dinocera+code@gmail.com`). Tes choix : **le domaine `alertes.joba1.ch`**, et **un bouton « Copier » en attendant** que le domaine soit en place.

- **Le domaine** (`JOBBOT_ALERT_DOMAIN=alertes.joba1.ch`) : un invité reçoit à `nom-code@alertes.joba1.ch` (le nom du compte en minuscules, sans accents ; le code de 8 caractères après le dernier tiret). Le domaine redirige tout vers ta boîte Gmail ; la collecte reconnaît le code dans l'adresse de destination et range l'e-mail dans le bon compte. Les adresses `+code` déjà données aux sites continuent de marcher.
- **Ce qu'il te reste à faire** (une fois) : sur le domaine `joba1.ch`, une redirection « catch-all » de `*@alertes.joba1.ch` vers ta boîte (Cloudflare Email Routing, par exemple), puis `JOBBOT_ALERT_DOMAIN=alertes.joba1.ch` dans le `.env`. Tant que ce n'est pas fait, rien ne change.
- **En attendant** : l'adresse d'un invité qui passe par ta boîte s'affiche abrégée (`k…+k9dyqou7@gmail.com`), avec **« Copier l'adresse »**, qui copie l'adresse entière à donner aux sites. Pour toi (l'exploitant), ton adresse reste entière.
- **Vérifié** : tests du routage (`nom-code@domaine`, majuscules, code inconnu, `+code` toujours valable), de la page Alertes d'un invité avec le domaine, du composant d'adresse (abrégée, entière, copie) ; pytest, ruff, mypy, vitest, eslint, vue-tsc.

