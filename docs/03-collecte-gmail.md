# 03 — Collecte des alertes Gmail (version 0.2.0)

> Statut : **validé le 2026-10-02**. Partie a livrée. Partie b : analyseur Indeed livré ; jobup et Job-Room à suivre.
> S'appuie sur [01-cadrage.md](01-cadrage.md) §2 et §9, et sur le squelette livré en 0.1.0.

## 1. Objectif

Chaque alerte e-mail de jobup, Indeed ou Job-Room devient :

- une ligne du **journal des recherches** (`searches`) : quand, quel site, quelle alerte, combien d'offres ;
- des **offres** (`offers`), sans doublon même si la même annonce arrive par plusieurs sites ou plusieurs alertes.

Hors périmètre de la 0.2 :
- le filtre des prérequis (0.3) : toutes les offres restent au statut `new` ;
- la note IA (0.4) ;
- l'ouverture des liens vers les annonces (niveau B du cadrage §2) : en 0.2, seul le contenu de l'e-mail est utilisé (niveau A).

## 2. Ce que tu dois préparer

À faire une fois, avant que je puisse tester sur de vraies alertes :

1. **Créer une adresse Gmail dédiée**, qui ne sert qu'aux alertes. Évite d'y mettre ton nom complet : l'adresse apparaîtra dans les e-mails analysés.
2. **Activer la validation en deux étapes** sur cette adresse : Google l'exige pour les mots de passe d'application.
3. **Créer un mot de passe d'application** (Compte Google → Sécurité → Mots de passe des applications), nommé par exemple `job-bot`.
4. Le mettre dans `.env`, avec l'adresse (§6). **Ne me le donne pas dans la conversation.**
5. **Créer tes alertes** sur jobup, Indeed et Job-Room, envoyées vers cette adresse, avec des critères larges. Le tri fin se fera dans la plateforme (0.3).
6. Attendre d'avoir reçu **au moins 2 ou 3 alertes par site** : les analyseurs se construisent à partir de vrais e-mails (§5).

Point à vérifier de ton côté : Job-Room propose bien des alertes par e-mail pour une recherche enregistrée. Si ce n'est pas le cas pour ton compte, dis-le-moi : il faudra une autre source pour Job-Room, à cadrer à part.

## 3. Fonctionnement

```
 tâche `collect` (worker, toutes les 2 h de 7 h à 21 h + bouton « Collecter maintenant »)
   │
   ├─ 1. IMAP en LECTURE SEULE : liste les e-mails reçus depuis la dernière collecte
   │       (premier passage : les 30 derniers jours)
   │
   ├─ 2. pour chaque e-mail pas encore vu (clé : Message-ID)
   │       ├─ copie brute → stockage `emails/AAAA/MM/<id>.eml`
   │       ├─ choix de l'analyseur selon l'expéditeur : jobup | indeed | jobroom | inconnu
   │       ├─ analyse → nom de l'alerte + liste d'offres brutes
   │       └─ 1 ligne `searches` (même si l'e-mail n'est pas reconnu : rien ne se perd)
   │
   └─ 3. pour chaque offre brute
           ├─ normalisation : titre, entreprise, lieu, taux d'activité tiré du titre
           ├─ déjà connue ? (§4)  oui → on ajoute seulement « vue dans cette alerte »
           │                       non → nouvelle offre, statut `new`
           └─ compteurs de la ligne `searches` mis à jour
```

### Lecture seule stricte

Le cadrage (§9) prévoyait de marquer chaque e-mail comme traité. Je propose de **ne rien modifier du tout dans la boîte** : ni lu/non lu, ni libellé, ni déplacement. Le dossier est ouvert en mode lecture seule (`EXAMINE` en IMAP), et la plateforme retient elle-même les e-mails déjà traités grâce à leur `Message-ID`. Avantages : impossible d'abîmer la boîte, et tu continues à voir les alertes comme non lues dans Gmail si tu les consultes.

### Copie brute des e-mails

Chaque e-mail est conservé tel quel dans le stockage (`JOBBOT_STORAGE_PATH`, donc `data/` en local, jamais dans git). Si un analyseur se trompe ou si un site change le format de ses e-mails, la commande `jobbot reparse` réanalyse les copies sans retourner dans Gmail, et sans créer de doublon.

### Collecte idempotente

Relancer `collect` (bouton, CronJob lancé deux fois, deux workers) ne crée aucun doublon : `Message-ID` est unique dans `searches`, et l'association offre ↔ alerte est unique. Le bouton « Collecter maintenant » utilise un verrou de file (`queueing_lock`) : si une collecte attend déjà, il n'en ajoute pas une deuxième.

## 4. Doublons

Une même annonce peut arriver plusieurs fois : dans deux alertes du même site, ou sur jobup **et** Indeed. Deux niveaux de reconnaissance, dans cet ordre :

1. **Identifiant du site** : quand le lien contient l'identifiant de l'annonce (par exemple le paramètre `jk` des liens Indeed), même site + même identifiant = même offre.
2. **Empreinte** : titre, entreprise et lieu normalisés, puis hachés. La normalisation, testée à fond dans `core/` :
   - minuscules, accents retirés, ponctuation et espaces multiples supprimés ;
   - titre : suppression des mentions de genre (`(h/f)`, `(m/w/d)`, `H/F`, `/ -in`) et du taux (`80-100 %`), qui est gardé à part ;
   - entreprise : suppression des formes juridiques (`SA`, `AG`, `Sàrl`, `GmbH`, `Ltd`) ;
   - lieu : ville seule (pas de NPA ni de canton).

Conséquence assumée : deux postes identiques dans la même entreprise et la même ville (deux ouvertures du même poste) sont fusionnés en une seule offre. L'offre garde la liste de toutes ses apparitions (sites, alertes, dates) et affiche « vue N fois ».

## 5. Analyseurs par site

Je ne connais pas avec certitude le format exact des alertes de chaque site, qui change d'ailleurs de temps en temps. Les analyseurs sont donc **construits à partir de tes vrais e-mails**, en trois temps :

1. `jobbot imap-sample --limit 30` copie des e-mails de la boîte dans `data/samples/` (local, ignoré par git, lecture seule comme la collecte).
2. Je lis ces copies pour écrire un analyseur par site (expéditeur, structure HTML, liens, identifiant d'annonce).
3. `jobbot anonymize-sample` en fait des **jeux de test anonymisés** : ton adresse, ton nom et les jetons de suivi des liens sont remplacés. **Tu les relis avant qu'ils soient commités**, puisque le dépôt est public.

Chaque analyseur :
- reconnaît ses e-mails par le **domaine de l'expéditeur** (et le sujet si nécessaire) ;
- extrait le nom de l'alerte et, pour chaque offre : titre, entreprise, lieu, extrait, lien, identifiant du site si présent ;
- a un numéro de version, enregistré dans `searches` : après une correction, `jobbot reparse` sait quels e-mails réanalyser.

E-mail non reconnu (confirmation d'inscription, publicité, nouveau format) : il est enregistré avec le statut `unrecognized` et visible dans le Journal. Rien n'est jeté en silence.

**Sécurité.** Le contenu des e-mails est traité comme de la donnée non fiable : HTML analysé sans rien exécuter, liens jamais ouverts automatiquement, affichés avec `rel="noopener noreferrer"`. À partir de la 0.4, ce texte sera envoyé à l'IA : il lui sera présenté comme une donnée à évaluer, jamais comme des instructions.

## 6. Configuration ajoutée

| Variable | Type | Défaut | Rôle |
|---|---|---|---|
| `JOBBOT_IMAP_HOST` | config | `imap.gmail.com` | |
| `JOBBOT_IMAP_PORT` | config | `993` | TLS obligatoire |
| `JOBBOT_IMAP_USER` | config | vide | adresse Gmail dédiée |
| `JOBBOT_IMAP_PASSWORD` | secret | vide | mot de passe d'application ; accepte `_FILE` |
| `JOBBOT_IMAP_FOLDER` | config | `INBOX` | |
| `JOBBOT_IMAP_BACKFILL_DAYS` | config | `30` | profondeur du premier passage |

Sans `JOBBOT_IMAP_USER` ni `JOBBOT_IMAP_PASSWORD`, la plateforme démarre normalement. La tâche `collect` se termine sans erreur avec 0 e-mail, et la page État affiche « Collecte : non configurée ». Une erreur d'authentification fait échouer la tâche avec un message clair, qui ne contient jamais le mot de passe.

Ces variables sont ajoutées à `.env.example` et à `docs/exploitation.md`.

## 7. Base de données (migration 0003)

```
searches        id, source (jobup|indeed|jobroom|unknown), message_id UNIQUE, imap_uid,
                received_at, subject, alert_label?, raw_key (chemin de la copie brute),
                parse_status (parsed|empty|unrecognized|failed), parser_version, error?,
                results_count, new_offers_count, collected_at, job_run_id → job_runs
offers          id, fingerprint UNIQUE, title, company?, location?, rate_min?, rate_max?,
                snippet?, status (new en 0.2), first_seen_at, last_seen_at, seen_count
offer_links     id, offer_id → offers, source, external_id?, url,
                UNIQUE (source, external_id) quand external_id est connu
offer_sightings offer_id → offers, search_id → searches, position, PRIMARY KEY (offer_id, search_id)
```

**Écart avec le cadrage (§5) :** la table `offer_sources` est remplacée par deux tables. `offer_links` répond à « où trouver cette offre » (un lien par site). `offer_sightings` répond à « dans quelles alertes elle est apparue ». Une seule table ne pouvait pas porter les deux : une même annonce Indeed vue dans deux alertes violait l'unicité de l'identifiant.

Les colonnes des offres prévues pour plus tard (contrat, langues, salaire, description, contact) arriveront avec les versions qui les remplissent.

## 8. API et interface

Routes ajoutées :

| Route | Rôle |
|---|---|
| `GET /api/searches?source=&status=&limit=&offset=` | journal des recherches, plus récentes d'abord |
| `GET /api/searches/{id}` | une alerte et ses offres (nouvelles ou déjà connues) |
| `GET /api/offers?limit=&offset=` | offres collectées, plus récentes d'abord |
| `POST /api/collect` | met une collecte en file ; répond `202` avec `queued` ou `already_queued` |
| `GET /api/status` | ajoute un bloc `collect` : configurée oui/non, dernier succès, dernière erreur |

Interface :
- **Journal** (page remplie) : tableau des alertes reçues (date, site, alerte, nombre d'offres, nouvelles, statut d'analyse), filtres par site et par statut, bouton « Collecter maintenant ». Un clic sur une ligne affiche les offres de cette alerte.
- **Offres** : liste simple (titre, entreprise, lieu, taux, sites, « vue N fois », lien). Le tableau de bord complet, avec la note et les actions, reste en 0.4.
- **État** : quatrième voyant « Collecte ».

## 9. Tâches, commandes et métriques

| Élément | Détail |
|---|---|
| Tâche `collect` | planifiée toutes les 2 h de 7 h à 21 h, heure suisse ; lancée aussi par le bouton ou `jobbot run-job collect` |
| `jobbot imap-sample --limit N` | copie N e-mails dans `data/samples/` (§5) |
| `jobbot anonymize-sample` | produit les jeux de test anonymisés à relire (§5) |
| `jobbot reparse [--source S]` | réanalyse les copies brutes stockées |
| `jobbot_collect_emails_total{source, parse_status}` | e-mails traités |
| `jobbot_collect_offers_total{source, result}` | `result` : `new` ou `duplicate` |
| `jobbot_imap_errors_total{kind}` | `auth`, `connection`, `other` |

Logs : identifiant interne de l'e-mail, site, compteurs. **Jamais** l'adresse, le sujet ni le contenu.

## 10. Tests

- **Normalisation et empreinte** (`core/`) : mentions de genre, taux, formes juridiques, accents, ville. Une série de paires « doivent fusionner » et « ne doivent pas fusionner ».
- **Analyseurs** : sur les jeux anonymisés, nombre d'offres et champs attendus pour chaque e-mail ; e-mail inconnu → `unrecognized`.
- **Collecte** avec une fausse boîte IMAP en mémoire :
  - deux passages successifs → aucun doublon ;
  - la même offre sur deux sites → une offre, deux liens ;
  - boîte non configurée → succès avec 0 e-mail ;
  - mauvais mot de passe → échec, sans mot de passe dans l'erreur ni dans les logs ;
  - la boîte n'est jamais ouverte autrement qu'en lecture seule (le test échoue sur toute commande d'écriture IMAP).
- **`reparse`** : une version d'analyseur corrigée met à jour les offres sans créer de doublon.
- **Frontend** : Journal (liste, filtres, détail, bouton), voyant Collecte.

## 11. Livraison en deux PR

| PR | Contenu | Prérequis de ton côté |
|---|---|---|
| **0.2.0-a** | IMAP en lecture seule, copie brute, journal `searches` (tous les e-mails en `unrecognized`), normalisation et doublons, tables, API, pages Journal et Offres, `imap-sample` | aucun pour le code ; adresse Gmail configurée pour l'essayer |
| **0.2.0-b** | Analyseurs jobup, Indeed et Job-Room, jeux de test anonymisés, `reparse` | 2 ou 3 alertes reçues par site, et ton feu vert pour que je lise `data/samples/` |

La PR **a** peut avancer pendant que les premières alertes arrivent.

## Points à valider

1. **Lecture seule stricte** (§3) : rien n'est modifié dans Gmail, même pas l'état lu/non lu. C'est un écart avec le cadrage §9.
2. **Copie brute** des e-mails dans `data/emails/`, pour pouvoir réanalyser sans retourner dans Gmail (§3).
3. **Échantillons** : tu acceptes que je lise les e-mails copiés dans `data/samples/` pour écrire les analyseurs, et tu relis les jeux anonymisés avant qu'ils soient commités (§5).
4. **Aucun lien ouvert en 0.2** : seul le contenu de l'e-mail est utilisé (§1).
5. **Fréquence** : toutes les 2 h de 7 h à 21 h, plus le bouton ; premier passage sur 30 jours (§6, §9).
6. **Fusion des doublons** par identifiant du site puis par empreinte titre + entreprise + lieu, en acceptant que deux ouvertures identiques soient fusionnées (§4).
7. **Deux tables `offer_links` et `offer_sightings`** à la place de `offer_sources` (§7).
8. **Livraison en deux PR** (§11).

## Écarts à la livraison

- **Fenêtre de collecte** : chaque collecte relit les `JOBBOT_IMAP_BACKFILL_DAYS` derniers jours, au lieu de repartir de la veille du dernier e-mail reçu. Sinon, des alertes étiquetées après coup (filtre Gmail ajouté plus tard) étaient ignorées. Les e-mails déjà connus ne sont pas retéléchargés : seul leur en-tête est lu.
- **Boîte lue** : une adresse Gmail existante, en ne lisant qu'un libellé (`JOBBOT_IMAP_FOLDER`, par exemple `Professionnel/job-bot`), plutôt qu'une adresse dédiée.
- **Indeed** : l'analyseur lit la partie texte de l'e-mail, plus stable que le HTML. Les liens sont reconstruits à partir de l'identifiant d'offre (`jk`), sans les jetons de suivi du compte. Les annonces sponsorisées n'ont pas d'identifiant : elles sont dédoublonnées par l'empreinte.
- **Jeux de test** : seule la partie texte est gardée, avec des en-têtes réduits au minimum.
- **Stockage en local** : `JOBBOT_STORAGE_PATH=../data`, car les commandes tournent depuis `backend/`.
- **Expéditeurs confirmés** : `donotreply@jobalert.indeed.com` et `candidat@my.jobup.ch`.
