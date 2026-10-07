# 20 — Mes alertes et « Voir l'offre chez l'employeur » (version 0.13.0)

> Statut : **validé** le 2026-10-07. livré : PR a (Mes alertes), PR b (offre chez l'employeur).
> Retours d'usage du 2026-10-07 : créer ses alertes plus facilement, vers l'adresse de son choix ; trouver l'annonce chez l'employeur plutôt que sur une plateforme intermédiaire.

## 1. Mes alertes

### 1.1 Où

L'onglet **Journal des recherches** de la rubrique Candidatures devient **Alertes**, en deux parties :

- **Mes alertes** (nouveau, §1.2 à §1.4) : les recherches à suivre et, pour chacune, les boutons pour créer l'alerte sur chaque site.
- **Alertes reçues** : le journal actuel, inchangé (il reste l'annexe du PDF ORP).

### 1.2 Les recherches à suivre

Une **recherche** = des **mots** + un **lieu**, par exemple « DevOps · Lausanne ».

- **Proposées une fois** à partir de ton profil : les mots-clés « Mon domaine » croisés avec les lieux de « Ce que je cherche ». Par exemple « DevOps, Kubernetes » et « Lausanne, Genève » donnent quatre recherches. Tu gardes, modifies ou supprimes chacune.
- **Ajout libre** : « Ajouter une recherche » (mots, lieu).
- Une recherche peut être **mise de côté** (plus de rappel), sans être supprimée.

### 1.3 Créer l'alerte sur chaque site

Pour chaque recherche, une ligne de boutons : **jobup**, **jobs.ch**, **LinkedIn**, **Indeed**, plus les sites ajoutés dans Réglages (Sites suivis) qui ont une adresse.

- Chaque bouton ouvre, dans un nouvel onglet, la **page de résultats du site déjà remplie** (par exemple `jobup.ch/fr/emplois/?term=devops&location=Lausanne`). Les adresses de jobup, jobs.ch et LinkedIn ont été vérifiées ; celle d'Indeed sera vérifiée dans ton navigateur (Indeed refuse les lectures automatiques).
- **Sur le site**, tu cliques sur son bouton d'alerte (« Créer une alerte », « Activer l'alerte »…) et tu donnes **l'adresse e-mail de ton choix**. Un court rappel, site par site, dit où cliquer.
- **La plateforme ne crée pas l'alerte à ta place** : il faudrait se connecter à tes comptes sur ces sites, et ils bloquent les robots.

### 1.4 Faire arriver les alertes, et vérifier qu'elles arrivent

- **Ton adresse de réception** est rappelée en haut : la boîte lue par la plateforme (aujourd'hui ta boîte Gmail, libellé `job-bot`).
- Si tu as choisi **une autre adresse** sur le site : un pas-à-pas pour faire suivre ces e-mails vers la boîte lue, avec les **adresses d'expédition** de chaque site (déjà connues par Sites suivis) pour écrire le filtre.
- **État de chaque alerte**, case par case (recherche × site) :
  - **« Reçue le 6 octobre »** : une alerte de ce site, dont l'objet ou le libellé contient les mots de la recherche, est arrivée dans le journal ;
  - **« Créée, en attente »** : tu as cliqué sur « J'ai créé l'alerte », mais rien n'est encore arrivé (premier envoi souvent le lendemain) ;
  - **« À créer »** sinon.
- Un rappel discret sur Aujourd'hui si une alerte « créée » n'a toujours rien envoyé après 3 jours.

## 2. Voir l'offre chez l'employeur

### 2.1 Quand

- Pour les offres **Indeed, LinkedIn et jobs.ch**, et les offres jobup sans lien vers l'employeur.
- **Automatiquement** pour les offres notées au moins à un **seuil** (70 par défaut, réglable), après la note ; **à la demande** pour les autres, avec un bouton « Chercher l'offre chez l'employeur » dans le détail.
- **Une seule tentative par offre** ; le résultat est gardé.

### 2.2 Comment, du moins cher au plus cher

1. **Site de l'entreprise déjà connu** (annonce jobup, recherche d'adresse sur Internet) : sa page carrières est cherchée à partir de la page d'accueil (liens « Emplois », « Carrières », « Jobs »).
2. **Outil de recrutement reconnu** sur cette page (par exemple SmartRecruiters, Greenhouse, Lever, Workday, Personio, Recruitee) : quand l'outil publie la liste des postes ouverts, le poste est cherché par son titre dans cette liste. Sans IA, sans coût. Chaque outil est vérifié avant d'être ajouté.
3. **Recherche sur Internet par l'IA** (Claude Haiku, 3 recherches au plus), en dernier recours : elle reçoit **seulement l'entreprise, le titre du poste et la ville**, rien sur toi, et rend l'adresse de l'annonce chez l'employeur. Environ **0,02 à 0,03 $** par offre, dans le plafond mensuel (`purpose = employer`).

### 2.3 Vérification avant d'afficher

- La page trouvée est **lue par la plateforme** (mêmes garde-fous que pour les logos : https, aucune adresse interne, taille limitée).
- Elle n'est retenue que si elle contient **le titre du poste** (sans tenir compte des majuscules, accents et ponctuation) et **le nom de l'entreprise**, et qu'elle n'est pas une page de jobup, jobs.ch, Indeed ou LinkedIn.
- Retenue : un lien **« Voir chez l'employeur »** dans le détail et sur la carte, avec sa source (site, outil de recrutement, Internet) et la date de vérification. Il devient le lien proposé pour postuler et celui pré-rempli dans « Marquer comme envoyée ».
- La page est revérifiée avec les autres (tous les 3 jours) ; disparue, le lien est retiré.

### 2.4 Annonces d'agences de placement

Une agence publie souvent sans nommer l'employeur. Si l'entreprise est une agence connue ou si l'annonce le dit (« pour notre client »), pas de recherche : la mention **« Annonce d'agence : employeur non indiqué »** s'affiche.

## 3. Base (migration 0031)

```
alert_searches   id, terms, location, active, created_at
alert_setups     search_id, site, created_at        -- « J'ai créé l'alerte »
offers           + employer_url?, employer_url_source? (site|ats|web), employer_checked_at?
companies        + careers_url?, ats?                -- cache par entreprise
settings         + employer_search_threshold (défaut 70)
```

## 4. Livraison en deux PR

| PR | Contenu | De ton côté |
|---|---|---|
| **0.13.0-a** | Onglet Alertes : recherches, boutons par site, état des alertes | créer les alertes sur les sites |
| **0.13.0-b** | Voir l'offre chez l'employeur : site, outils de recrutement, recherche IA, vérification | aucun |

## Points à valider

1. **Onglet « Alertes »** (Mes alertes + Alertes reçues) à la place de « Journal des recherches » (§1.1).
2. **Recherches proposées** à partir de « Mon domaine » × lieux de « Ce que je cherche », modifiables (§1.2).
3. **Boutons par site** qui ouvrent la recherche déjà remplie ; l'alerte reste créée par toi sur le site (§1.3).
4. **État de chaque alerte** (reçue, créée en attente, à créer) d'après le journal (§1.4).
5. **Recherche chez l'employeur automatique dès 70** (réglable), à la demande sinon ; environ 0,02 à 0,03 $ par offre seulement quand l'IA est nécessaire (§2.1-2.2).
6. **Lien retenu seulement si la page contient le titre et l'entreprise** (§2.3).
7. **Deux PR** (§4).

## Écarts avec la PR a

- **Adresse** : l'onglet est `/candidatures/alertes` ; `/journal`, `/candidatures/journal` et les anciens liens du journal y mènent.
- **Recherches proposées** : jusqu'à 4 mots-clés de « Mon domaine » croisés avec 4 lieux de « Ce que je cherche » (8 recherches au plus), une seule fois ; les codes de canton (« VD ») sont écartés, les sites les comprennent mal. Sans lieu, la recherche vaut pour toute la Suisse.
- **Tableau** : une ligne par recherche, une colonne par site actif (Sites suivis) ; « Ouvrir » mène à la recherche remplie (page d'accueil pour un site ajouté sans recherche connue). Indeed : `ch-fr.indeed.com/jobs?q=…&l=…`, non vérifiable automatiquement.
- **« Reçue »** : une alerte du même site, des 60 derniers jours, dont l'objet ou le libellé contient tous les mots de la recherche (sans tenir compte des majuscules, accents et ponctuation) ; le lieu n'est pas exigé.
- **Rappel** : sur Aujourd'hui et en pastille de l'onglet Alertes, pour une alerte « créée » depuis 3 jours sans rien reçu.
- **API** : `/api/alert-searches` (`/api/alerts/refresh`, le bouton « Collecter », existait déjà).
- **Migration 0031** (`alert_searches`, `alert_setups`) ; les champs de « Voir l'offre chez l'employeur » viendront avec la PR b (0032).

## Écarts avec la PR b

- **Outils de recrutement pris en charge** : Greenhouse, Lever, SmartRecruiters et Personio, dont la liste publique des postes a été vérifiée le 2026-10-07. **Recruitee** (adresse publique introuvable) et **Workday** (liste accessible seulement par une requête de recherche) sont écartés pour l'instant.
- **Constat sur cinq vrais sites** (Scandit, On, Proton, Nexthink, Beekeeper) : la page carrières est bien trouvée, mais la liste des postes est construite par le navigateur ou confiée à un autre outil (par exemple Eightfold). Le chemin gratuit trouvera donc surtout les entreprises qui affichent leurs postes dans la page, ou qui utilisent l'un des quatre outils ; **le plus souvent, c'est la recherche par l'IA qui trouvera l'annonce**.
- **Page carrières** : liens « Emplois », « Carrières », « Jobs »… sur le même site (sous-domaines compris) ou vers un outil reconnu, avec un pas de plus au besoin (page carrières → liste des postes).
- **Titre** : comparé sans « (H/F) », « m/w/d » ni taux ; 75 % des mots du titre doivent se retrouver.
- **Une annonce trouvée par l'outil de recrutement** est prise telle quelle (la liste vient de l'employeur) ; celle trouvée sur le site ou par l'IA doit contenir le titre et le nom de l'entreprise.
- **Agences** : liste de 20 agences connues et formules « pour notre client », « für unseren Kunden », « on behalf of our client ».
- **Tâche `employer`** : chaque heure de 7 h à 21 h, 6 offres au plus par passage ; au plafond de l'IA, elle continue sans IA. Revérification des liens trouvés tous les 3 jours (lien retiré si la page ne répond plus).
- **Lien de candidature** : l'annonce chez l'employeur devient le lien « Postuler chez l'employeur » de la préparation et le lien pré-rempli de « Marquer comme envoyée ».
- **Migration 0032**.
- **Non essayé en réel** : la recherche par l'IA (pas de clé API sur l'instance de test) ; couverte par des tests avec une réponse simulée.
