# 01 — Cadrage de job-bot

> Statut : **validé le 2026-10-02**, avec les valeurs par défaut pour les points non tranchés (voir « Décisions » en fin de document).
> Décisions : journal au format ORP, collecte par alertes e-mail Gmail, mode semi-automatique (Kevin valide chaque envoi), projet local, **backend Python + frontend TypeScript**, architecture prête pour Terraform, Ansible et Kubernetes après la CKA.

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

**Aucune valeur n'est écrite dans le code.** Kevin saisit ses prérequis dans un formulaire de la plateforme (page « Prérequis »), qui les enregistre dans `criteria`. Le filtre lit cette table à chaque passage. Une modification du formulaire s'applique donc aux nouvelles offres, et un bouton « refiltrer » permet de l'appliquer aussi aux offres déjà reçues.

Les autres réglages passent aussi par un formulaire (page « Réglages », table `settings`) : objectif mensuel ORP, seuil de notification, plafond du coût IA, fréquence de collecte.

## 5. Schéma de données

```
documents        id, filename, kind(cv|certificat|diplome|autre), storage_key, sha256, uploaded_at
profile_chunks   id, document_id?, kind, title, content, tags[], active, updated_at
criteria         id, field, operator, value, active, updated_at  -- prérequis du §4, saisis par formulaire
settings         key PRIMARY, value, updated_at                  -- objectif ORP, seuil ntfy, plafond IA…
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
| File de jobs | procrastinate (file de tâches Python dans PostgreSQL, sans Redis) | inchangée |
| Fichiers (CV…) | interface `Storage` → disque local | même interface → MinIO / S3 |
| Santé | `/healthz` (vivant), `/readyz` (base joignable) | sondes liveness / readiness |
| Métriques | `/metrics` Prometheus (jobs, offres, coût IA, latence) | ServiceMonitor, Grafana, alertes |
| Logs | JSON structuré (structlog) | Loki ou équivalent |
| Arrêt propre | gestion de SIGTERM | `terminationGracePeriodSeconds` |

**Écart par rapport à ta stack trading :** là-bas tu utilises `node:sqlite`. Ici, PostgreSQL dès le départ. SQLite tient sur un seul fichier, ce qui empêche plusieurs réplicas et transforme la migration en chantier. Avec PostgreSQL dans compose, rien ne change à l'usage en local.

**Deux images, deux langages, un contrat.** Le backend Python publie son contrat OpenAPI (généré par FastAPI). Le frontend TypeScript en tire ses types (`openapi-typescript`), et la CI échoue si les deux divergent. Chaque partie se construit, se teste et se déploie séparément : c'est la situation d'une vraie équipe, et un bon terrain d'exercice pour la CI et Helm.

Feuille de route infra, à démarrer après la CKA, chaque étape étant un exercice :

1. `deploy/k8s/` : manifestes bruts sur un cluster local (kind ou k3d) : Deployment, Service, CronJob, StatefulSet, PVC, Secret, NetworkPolicy, RBAC du worker.
2. `deploy/helm/` : un chart pour backend + worker + frontend, avec des values par environnement.
3. `deploy/monitoring/` : kube-prometheus-stack, tableau de bord Grafana, alertes (job en échec, coût IA du mois).
4. `deploy/terraform/` : création des machines virtuelles, du réseau, du DNS et du stockage objet chez un hébergeur suisse (Infomaniak ou Exoscale). Pour s'exercer gratuitement, d'abord en local avec le provider libvirt ou Multipass.
5. `deploy/ansible/` : configuration des machines créées par Terraform : durcissement (SSH, pare-feu, mises à jour), containerd, puis **installation du cluster avec kubeadm** (control plane + workers). C'est exactement le geste de la CKA, rendu reproductible. Terraform génère l'inventaire Ansible.
6. GitOps (Argo CD) pour déployer le chart, CI GitHub Actions (tests, build des deux images, scan, push vers le registre).

Chaîne cible : **Terraform crée les machines → Ansible les configure et monte le cluster → Argo CD déploie l'application → Prometheus/Grafana surveillent**.

Les dossiers `deploy/k8s`, `helm`, `monitoring`, `terraform` et `ansible` existent dès le départ, vides avec un README, pour que la structure ne bouge pas.

## 8. Arborescence

```
job-bot/
├── backend/                 Python 3.13, géré avec uv
│   ├── pyproject.toml
│   ├── Dockerfile           une image, deux commandes : `api` et `worker`
│   ├── alembic/             migrations de la base
│   ├── src/jobbot/
│   │   ├── api/             FastAPI : routes REST, /healthz /readyz /metrics
│   │   ├── worker/          tâches procrastinate : collect, normalize, filter, evaluate, draft, report
│   │   ├── core/            domaine pur : règles du filtre, empreinte, format ORP (testé à fond)
│   │   ├── db/              modèles SQLAlchemy 2, sessions
│   │   ├── sources/         un analyseur d'e-mail par site : jobup, indeed, jobroom
│   │   ├── llm/             SDK Anthropic, prompts versionnés, comptage des tokens et du coût
│   │   ├── storage/         interface Storage : local / S3
│   │   └── settings.py      configuration par variables d'environnement (pydantic-settings)
│   └── tests/               pytest
├── frontend/                Vue 3 + Vite + TypeScript (même choix que trading)
│   ├── Dockerfile           build statique servi par nginx
│   └── src/api/             types générés depuis l'OpenAPI du backend
├── deploy/
│   ├── compose/             docker-compose.yml (postgres, api, worker, frontend)
│   └── k8s/  helm/  monitoring/  terraform/  ansible/   (vides au départ, voir §7)
├── docs/                    01-cadrage.md, puis un document par module
├── data/                    ← .gitignore : documents, exports ORP, rien de personnel commité
└── .env.example
```

Outils côté backend : FastAPI, SQLAlchemy 2 + Alembic, procrastinate, imap-tools, SDK `anthropic`, structlog, prometheus-client, ruff + mypy, pytest.

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
| 0.1.0 | Squelette backend + frontend, compose (PostgreSQL, api, worker, frontend), santé, métriques, CI (tests, lint, contrat OpenAPI, anti-données personnelles) |
| 0.2.0 | Collecte Gmail + analyseurs des 3 sites + journal `searches` + dédoublonnage |
| 0.3.0 | Documents + blocs de profil + formulaires « Prérequis » et « Réglages » + filtre |
| 0.4.0 | Note IA + tableau de bord + ntfy |
| 0.5.0 | Rédaction lettre et CV + suivi des candidatures |
| 0.6.0 | Export ORP + rappels |
| 1.x | Infra : k8s, Helm, monitoring, Terraform, Ansible + kubeadm, GitOps (§7) |

Pour chaque version : un document `docs/NN-*.md` validé, puis une PR.

## Décisions (2026-10-02)

1. **Prérequis** : saisis par Kevin dans un formulaire de la plateforme, rien n'est écrit dans le code (§4).
2. **Langages** : backend Python (FastAPI) et frontend TypeScript (Vue) dès la 0.1, pour éviter une réécriture.
3. **PostgreSQL dès la 0.1** (§7).
4. **Adresse Gmail dédiée + IMAP avec mot de passe d'application** (§9).
5. **Détail des offres** : niveaux A puis B, et C en secours (§2).
6. **Valeurs par défaut des réglages**, modifiables dans le formulaire : seuil ntfy à 70, plafond IA à 10 CHF par mois, objectif ORP vide tant que Kevin ne l'a pas saisi.
7. **Dépôt public**, avec les règles du §8.
8. **Infra cible** : Terraform → Ansible (kubeadm) → Argo CD → Prometheus/Grafana (§7).

Prochaine étape : `docs/02-squelette.md` (version 0.1.0), à valider avant code.
