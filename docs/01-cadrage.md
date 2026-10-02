# 01 — Cadrage de job-bot

> Statut : **à valider**. Aucun code avant accord.
> Décisions déjà prises (2026-10-02) : journal au format ORP, collecte par alertes e-mail Gmail, mode semi-automatique (Kevin valide chaque envoi), projet local, architecture prête à migrer vers Kubernetes après la CKA.

## 1. Objectif

Arrêter de chercher à la main. La plateforme :

1. récupère les offres reçues par alerte e-mail (jobup, Indeed, Job-Room) ;
2. écarte celles qui ne respectent pas les prérequis non négociables ;
3. note les autres par rapport au profil de Kevin, et explique la note ;
4. prépare la lettre et le CV adapté pour les offres choisies ;
5. tient le journal des recherches et des candidatures, exportable pour les preuves de recherches d'emploi de l'ORP.

Hors périmètre, volontairement :

- se connecter aux comptes jobup, Indeed ou Job-Room (conditions d'utilisation, détection des bots, double authentification AGOV) ;
- envoyer une candidature sans clic de Kevin ;
- saisir les preuves dans Job-Room à sa place : l'export est prêt à recopier, la saisie reste manuelle.

## 2. Pipeline

```
 Gmail (adresse dédiée aux alertes)
   │  IMAP, lecture seule, toutes les 2 h
   ▼
 [collect]  analyse d'un e-mail par source → 1 ligne `searches` + N offres brutes
   ▼
 [normalize] champs communs + empreinte (titre + entreprise + lieu normalisés)
   ▼          → doublon ? on rattache la source à l'offre existante
 [filter]   règles fixes sur les prérequis, sans IA → `filtered_out` + raison
   ▼
 [evaluate] IA (modèle léger) + blocs de profil actifs → score 0-100, forces, manques
   ▼          score ≥ seuil → notification ntfy
 [review]   tableau de bord : préparer / ignorer / plus tard
   ▼
 [draft]    IA (modèle rédactionnel) → lettre + choix des blocs pour le CV
   ▼
 [apply]    Kevin envoie lui-même, puis clique « envoyée » → `applications`
   ▼
 [report]   export mensuel des preuves ORP (PDF + CSV)
```

Chaque étape est un **job indépendant et idempotent** : on peut le relancer sans créer de doublon. Ça sert deux fois : pour la fiabilité, et pour la migration (un job = une commande = plus tard un `CronJob` ou un worker Kubernetes).

### Détail des offres

Les e-mails d'alerte ne contiennent qu'un résumé : titre, entreprise, lieu, extrait, lien. Trois niveaux :

| Niveau | Contenu | Coût |
|---|---|---|
| A | Résumé de l'e-mail uniquement | Nul, toujours disponible |
| B | Ouverture de la page de l'offre, une requête à rythme humain, uniquement pour les offres qui passent le filtre | Faible, peut échouer (Indeed est derrière Cloudflare) |
| C | Kevin colle le texte de l'annonce dans la plateforme | Manuel, toujours fiable |

Proposition : A pour filtrer, B si elle réussit, sinon C avant la rédaction de la lettre. Une note obtenue sur le seul résumé est affichée comme « provisoire ».

## 3. Le profil en blocs (« chunks »)

Kevin dépose ses documents (CV, certificats de travail, diplômes). Ils sont stockés en local et **jamais commités**. Il découpe ensuite lui-même son profil en blocs modifiables :

| Type de bloc | Exemple | Utilisé par |
|---|---|---|
| `experience` | « 2022-2025, admin système chez X : … » | note, lettre, CV |
| `competence` | « Kubernetes (CKA en cours), Terraform, Linux » | note, lettre, CV |
| `formation` | diplôme, certification | note, CV |
| `preference` | « préfère une petite équipe, télétravail partiel » | note |
| `redhibitoire` | « pas de vente, pas de garde de nuit » | filtre (si traduisible en règle) puis note |
| `ton` | « lettres courtes, sans formule creuse » | lettre |

Règle stricte pour l'IA : elle ne peut rien affirmer sur Kevin qui ne figure pas dans un bloc actif. Chaque lettre liste les blocs utilisés, pour vérifier qu'elle n'invente rien.

## 4. Prérequis non négociables (filtre sans IA)

Évalués par règles, donc gratuits, reproductibles et expliqués :

- lieu : liste de communes ou rayon en km autour d'un point ;
- taux d'activité minimum ;
- type de contrat (CDI, CDD, temporaire, stage) ;
- langues exigées que Kevin ne parle pas → exclusion ;
- mots interdits dans le titre ;
- salaire minimum, appliqué seulement si l'offre l'indique (une offre sans salaire n'est pas exclue).

**Valeurs à fournir par Kevin** (cf. point 1 à valider).

## 5. Schéma de données

```
documents        id, filename, kind(cv|certificat|diplome|autre), storage_key, sha256, uploaded_at
profile_chunks   id, document_id?, kind, title, content, tags[], active, updated_at
criteria         id, field, operator, value, active            -- prérequis du §4
searches         id, source(jobup|indeed|jobroom|manual), message_id UNIQUE, alert_label,
                 received_at, executed_at, results_count, retained_count
offers           id, fingerprint UNIQUE, title, company, company_address?, contact_name?,
                 contact_phone?, contact_email?, location, rate_min?, rate_max?, contract?,
                 salary_min?, languages[], description?, detail_level(A|B|C),
                 status(new|filtered_out|to_review|later|ignored|preparing|applied),
                 first_seen_at, published_at?
offer_sources    offer_id, search_id, source, external_url        -- une offre, plusieurs sites
evaluations      id, offer_id, filter_passed, filter_reasons[], score?, strengths[], gaps[],
                 provisional, chunk_ids[], model, input_tokens, output_tokens, evaluated_at
drafts           id, offer_id, letter_md, cv_chunk_ids[], model, created_at, edited_md?
applications     id, offer_id, sent_at, method(ecrit|electronique|telephone|personnel),
                 assigned_by_orp, outcome(en_suspens|entretien|refus|engagement|sans_reponse),
                 outcome_reason?, outcome_at?, orp_month (AAAA-MM)
llm_calls        id, purpose, model, input_tokens, output_tokens, cost_chf, created_at
job_runs         id, job, started_at, finished_at, status, items_in, items_out, error?
```

`job_runs` et `llm_calls` alimentent aussi le monitoring (§7).

## 6. Export ORP

Une ligne par candidature du mois, avec les colonnes du formulaire « Preuves des recherches personnelles d'emploi » :

date · entreprise (nom, adresse) · personne de contact et téléphone · poste · taux (plein / partiel) · mode (écrit, électronique, téléphone, personnel) · assignation ORP oui/non · résultat (en suspens, engagement, refus + motif).

- Sorties : PDF lisible et CSV.
- Alerte ntfy si le nombre de candidatures du mois est sous l'objectif fixé par le conseiller.
- Rappel ntfy avant le 5 du mois suivant (date usuelle de remise, à confirmer avec le conseiller).
- Le journal des **recherches** (`searches`) est consultable à part. L'ORP demande des candidatures, mais ce journal prouve l'activité si on te pose la question.

## 7. Prévu pour changer d'infrastructure

Le but est que la version locale soit déjà une version « cloud native » qui tourne sur ton Mac. Passer à Kubernetes doit alors être un travail d'infrastructure, sans réécriture. Principes appliqués dès le départ :

| Principe | Version locale (v0.x) | Version infra (plus tard) |
|---|---|---|
| Conteneurs dès le départ | `docker compose up` | même image, déployée par Helm |
| Configuration par variables d'environnement uniquement | `.env` | ConfigMap + Secret (puis External Secrets ou Sealed Secrets) |
| API sans état | 1 conteneur `api` | `Deployment` avec plusieurs réplicas + `Ingress` |
| Jobs séparés de l'API | conteneur `worker` + planificateur interne | `CronJob` par job, ou worker qui lit la file |
| Base de données | **PostgreSQL** dans compose | `StatefulSet` + PVC, ou opérateur CloudNativePG |
| File de jobs | pg-boss (dans PostgreSQL, sans Redis) | inchangée |
| Fichiers (CV…) | interface `Storage` → disque local | même interface → MinIO / S3 |
| Santé | `/healthz` (vivant), `/readyz` (base joignable) | sondes liveness / readiness |
| Métriques | `/metrics` Prometheus (jobs, offres, coût IA, latence) | ServiceMonitor, Grafana, alertes |
| Logs | JSON structuré (pino, natif à Fastify) | Loki ou équivalent |
| Arrêt propre | gestion de SIGTERM | `terminationGracePeriodSeconds` |

**Écart par rapport à ta stack trading :** là-bas tu utilises `node:sqlite`. Ici je propose PostgreSQL dès le départ. SQLite tient sur un seul fichier, ce qui empêche plusieurs réplicas et transforme la migration en chantier. Avec PostgreSQL dans compose, rien ne change à l'usage en local.

Feuille de route infra, à démarrer après la CKA, chaque étape étant un exercice :

1. `deploy/k8s/` : manifestes bruts sur un cluster local (kind ou k3d) : Deployment, Service, CronJob, StatefulSet, PVC, Secret, NetworkPolicy, RBAC du worker.
2. `deploy/helm/` : chart avec values par environnement.
3. `deploy/monitoring/` : kube-prometheus-stack, tableau de bord Grafana, alertes (job en échec, coût IA du mois).
4. `deploy/terraform/` : cluster managé chez un hébergeur suisse (Infomaniak ou Exoscale) ou cluster local via le provider kind, DNS, stockage objet.
5. GitOps (Argo CD), CI GitHub Actions (build, scan d'image, push vers le registre).

Les dossiers `deploy/k8s`, `helm`, `monitoring` et `terraform` existent dès le départ, vides avec un README, pour que la structure ne bouge pas.

## 8. Arborescence

```
job-bot/
├── apps/
│   ├── api/            Fastify : routes REST, /healthz /readyz /metrics
│   ├── worker/         jobs collect, normalize, filter, evaluate, draft, report (pg-boss)
│   └── web/            interface (même choix que trading : Vite + Vue)
├── packages/
│   ├── core/           domaine pur : règles du filtre, empreinte, format ORP (testé à fond)
│   ├── db/             schéma, migrations, accès PostgreSQL
│   ├── sources/        un analyseur d'e-mail par site : jobup, indeed, jobroom
│   ├── llm/            appels Claude, prompts versionnés, comptage des tokens et du coût
│   └── storage/        interface Storage : local / S3
├── deploy/
│   ├── compose/        docker-compose.yml (postgres, api, worker, web)
│   ├── k8s/  helm/  monitoring/  terraform/    (vides au départ, voir §7)
├── docs/               01-cadrage.md, puis un document par module
├── data/               ← .gitignore : documents, exports ORP, rien de personnel commité
└── .env.example
```

**Dépôt public :** le dépôt `0xCAF3D0OD/job-bot` est public. CV, certificats, blocs de profil, offres, lettres et exports ORP restent dans `data/` et dans PostgreSQL, jamais dans git. On ajoute un test CI qui échoue si un fichier de `data/` est suivi.

## 9. Accès Gmail

- **Adresse dédiée aux alertes**, par exemple `kevin.jobs.alertes@gmail.com`. Les trois sites y envoient leurs alertes, et le bot n'a accès à rien d'autre de ta vie.
- Connexion IMAP avec un **mot de passe d'application** Google (double authentification requise sur cette adresse). Il est stocké dans `.env` en local, puis dans un Secret Kubernetes.
- Pourquoi pas l'API Gmail avec OAuth : une application OAuth non publiée en mode « test » voit son jeton expirer tous les 7 jours, donc il faudrait se reconnecter chaque semaine.
- Le bot ne fait que lire, et marque l'e-mail comme traité. Il ne supprime ni n'envoie rien.

## 10. IA et coûts

- Note : modèle léger (Claude Haiku), une requête par offre ayant passé le filtre, les blocs de profil étant mis en cache entre deux appels.
- Lettre : modèle rédactionnel (Claude Sonnet), uniquement sur ton clic « préparer ».
- Chaque appel est enregistré dans `llm_calls`, avec un plafond mensuel en CHF configurable au-delà duquel les notes sont mises en pause.
- L'abonnement claude.ai ne paie pas l'API : il faut une clé API Anthropic avec facturation à l'usage. Chiffrage précis dans le document du module IA.

## 11. Découpage en versions

| Version | Contenu |
|---|---|
| 0.1.0 | Squelette, compose (PostgreSQL, api, worker), santé, métriques, CI anti-données personnelles |
| 0.2.0 | Collecte Gmail + analyseurs des 3 sites + journal `searches` + dédoublonnage |
| 0.3.0 | Documents + blocs de profil + prérequis + filtre |
| 0.4.0 | Note IA + tableau de bord + ntfy |
| 0.5.0 | Rédaction lettre et CV + suivi des candidatures |
| 0.6.0 | Export ORP + rappels |
| 1.x | Infra : k8s, Helm, monitoring, Terraform, GitOps (§7) |

Pour chaque version : un document `docs/NN-*.md` validé, puis une PR.

## Points à valider

1. **Tes prérequis non négociables** : communes ou rayon, taux minimum, contrats acceptés, langues, mots interdits, salaire minimum.
2. **Langage : TypeScript** (Fastify, comme le projet trading) ? Le `.gitignore` du dépôt est celui de Python. Si tu veux pratiquer Python, c'est le moment de le dire. Sinon je remplace ce `.gitignore`.
3. **PostgreSQL dès la 0.1** au lieu de SQLite, pour la migration Kubernetes (§7).
4. **Adresse Gmail dédiée + IMAP avec mot de passe d'application** (§9).
5. **Détail des offres** : niveaux A puis B, et C en secours (§2).
6. **Seuil de notification** ntfy : score ≥ 70 ?
7. **Objectif mensuel ORP** : combien de candidatures te demande ton conseiller ?
8. **Plafond mensuel du coût IA** : 10 CHF pour commencer ?
9. **Dépôt public** : on le garde public avec les règles du §8, ou tu le passes en privé ?
