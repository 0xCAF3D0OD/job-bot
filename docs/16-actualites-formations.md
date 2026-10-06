# 16 — Actualités ciblées et catalogue de formations (version 0.9.0)

> Statut : **validé** le 2026-10-06. livré : PR a (domaine, pays, langue, relevé immédiat), PR b (sources suggérées, veilles).
> Retours d'usage du 2026-10-06, après la 0.8.0-b. Complète [15-cloche-actualites.md](15-cloche-actualites.md) §2.

## 1. Page vide après la mise à jour

**Constat** : la tâche `news` tourne toutes les 6 heures (0 h, 6 h, 12 h, 18 h UTC). Juste après la mise à jour, rien n'a encore été relevé.

**Correction** :
- un relevé part **tout de suite** quand la page est ouverte et que rien n'a jamais été relevé, et après l'ajout d'une source (seulement cette source) ;
- un bouton **« Relever maintenant »** sur la page, à côté de la date du dernier relevé (« relevé il y a 2 h »).

## 2. Filtrer selon ton domaine

**Proposition** : un réglage **« Mon domaine »**, une liste de mots-clés, par exemple `DevOps · Kubernetes · CKA · cloud · CI/CD · Linux · Terraform`.

- Il est **pré-rempli une fois** à partir de ton profil : les mots-clés « Poste » des offres que tu as notées le mieux ou auxquelles tu as postulé. Tu le modifies dans Réglages → Actualités.
- Sur la page, un interrupteur **« Mon domaine » / « Tout »**. « Mon domaine » ne garde que les contenus dont le titre ou le résumé contient l'un des mots-clés (sans tenir compte des majuscules ni des accents).
- Les mots trouvés sont surlignés sur la carte, pour voir pourquoi elle est là.
- **Exception** : les sources marquées **« marché de l'emploi »** (SECO, par exemple) restent toujours visibles, car les chiffres du chômage te concernent quel que soit ton domaine. C'est une case à cocher par source.
- **Coût** : aucun, la comparaison se fait sur la plateforme, sans IA.

> Variante, non proposée par défaut : un tri par l'IA (Claude Haiku), plus fin (« article sur l'emploi dans la tech » sans le mot « DevOps »), environ 1 à 2 $ par mois pour une centaine de contenus par jour. On pourra l'ajouter si les mots-clés laissent passer trop de bruit ou en manquent trop.

## 3. Pays et langue

- Chaque source a un **pays** (Suisse, France, Belgique, international…) et une **langue** (français, allemand, anglais…).
  - La langue est relevée dans le flux quand il la donne (`<language>`), sinon déduite du texte. Elle reste modifiable.
  - Le pays se choisit à l'ajout. Il vaut « international » par défaut pour une chaîne YouTube.
- Sur la page, deux listes : **Pays** et **Langue** (plusieurs choix possibles). Elles sont retenues d'une visite à l'autre.
- Les sources actuelles : SECO (Suisse ; français et allemand mêlés, chaque contenu porte sa propre langue), RTS et Le Temps (Suisse, français), TechWorld with Nana et KodeKloud (international, anglais).

## 4. Ajouter des sources

L'ajout par adresse existe déjà (Réglages). Deux façons en plus :

### 4.1 Catalogue de sources suggérées

Dans Réglages → Actualités, un bouton **« Parcourir les suggestions »** liste des sources que j'ai vérifiées (le flux répond, contenu récent), classées par **domaine**, **pays** et **langue**. Elles s'ajoutent en un clic. Exemples à vérifier :

| Domaine | Exemples |
|---|---|
| Marché de l'emploi (Suisse) | SECO, Office fédéral de la statistique (chômage, salaires), RTS, Le Temps, Swissinfo |
| DevOps, cloud | blog Kubernetes, CNCF, blogs AWS, Azure et Google Cloud, The New Stack, InfoQ DevOps |
| Vidéos tech | TechWorld with Nana, KodeKloud, chaîne CNCF, chaînes francophones (par exemple Xavki, Cookie connecté, Grafikart) |
| Recherche d'emploi | chaînes et blogs francophones sur le CV et les entretiens, à choisir ensemble |

Le catalogue est un fichier du dépôt (`news/catalog.yaml`), public, sans donnée personnelle. Je le complète au fil des domaines.

### 4.2 Veilles par recherche

Pour suivre un sujet plutôt qu'un site : **mots-clés + pays + langue**, par exemple « Kubernetes emploi » en Suisse et en français.

- La plateforme utilise le flux public de **Google Actualités** pour cette recherche (aucun compte, aucune clé), relevé comme les autres sources.
- **Confidentialité** : Google reçoit seulement les mots-clés de la veille, le pays et la langue. Rien sur toi.
- Les liens passent par une redirection de Google Actualités avant d'arriver sur l'article.
- Les doublons (même article dans plusieurs veilles ou sources) ne sont affichés qu'une fois.

## 5. Catalogue de formations

**Nouvelle page « Formations »**, dans le menu après Actualités. C'est un catalogue de formations en ligne, filtré selon ton domaine (le même réglage « Mon domaine »).

### 5.1 Contenu d'une fiche

| Champ | Exemple |
|---|---|
| Formation | Certified Kubernetes Administrator (CKA) |
| Organisme | The Linux Foundation |
| Type | certification · cours · parcours · atelier |
| Format | en ligne, à ton rythme · en ligne, en direct · en présentiel |
| Langue | anglais |
| Prix | gratuit · payant (le prix exact est sur le site, il change souvent) |
| Durée indicative | environ 40 h de préparation |
| Niveau | débutant · intermédiaire · avancé |
| Préparation conseillée | « Kubernetes for the Absolute Beginners » puis « CKA » (KodeKloud), simulateur d'examen |
| Lien | page officielle de l'organisme |

### 5.2 Sources du catalogue

1. **Catalogue vérifié** dans le dépôt (`trainings/catalog.yaml`), que je constitue et vérifie lien par lien. Pour ton domaine, par exemple :
   - **Certifications** : CKA, CKAD et CKS (Linux Foundation), Terraform Associate (HashiCorp), AWS, Azure et Google Cloud (niveaux associé et professionnel), LFCS (Linux) ;
   - **Cours gratuits** : AWS Skill Builder, Microsoft Learn, Google Cloud Skills Boost, cours d'introduction de la Linux Foundation (edX), documentation interactive de Kubernetes ;
   - **Cours payants** : KodeKloud, A Cloud Guru / Pluralsight, Udemy, Coursera.
2. **Suggestions de l'IA**, sur demande (bouton « Chercher d'autres formations ») : Claude Haiku avec la recherche web reçoit **seulement ton domaine** (les mots-clés) et ta langue, et propose jusqu'à 10 formations avec leur page source.
   - Elles arrivent marquées « à vérifier ». Tu les gardes ou tu les écartes.
   - **Coût** : environ 0,02 à 0,05 $ par recherche, dans le plafond mensuel (`llm_calls`, `purpose = training`).

### 5.3 Formations et chômage en Suisse

- Une mention générale sur chaque fiche payante : l'assurance chômage peut financer certaines formations (« mesures du marché du travail »), **sur demande à ton conseiller ORP et avec son accord préalable**. La plateforme ne dit pas si une formation sera acceptée : c'est la décision de l'ORP.
- Un lien vers les pages officielles sur les mesures du marché du travail (travail.swiss et le site de l'office cantonal de l'emploi).

### 5.4 Suivi

Chaque fiche peut être marquée **« Intéressé »**, **« En cours »** (avec une progression libre, par exemple « module 4/12 ») ou **« Terminée »** (date, certificat obtenu oui/non). Un onglet **« Mes formations »** les regroupe.

> **Idée pour plus tard**, non incluse : une formation terminée pourrait être proposée comme bloc de profil (lettres et CV) ; une demande de financement pourrait être préparée pour l'ORP.

## 6. Base (migration 0024)

```
news_sources   + country?, language?, labour_market (bool), query?   -- query : veille par recherche
news_items     + language?
settings       + domain_keywords[], news_filters (pays, langues, mon domaine)
trainings      id, title, provider, kind, format, language, price (free|paid), duration?, level?,
               url UNIQUE, domains[], origin (catalog|ai), verified (bool), created_at
training_marks training_id PRIMARY, status (interested|in_progress|done), progress?, done_at?,
               certified?, updated_at
```

## 7. Livraison en trois PR

| PR | Contenu | Prérequis de ton côté |
|---|---|---|
| **0.9.0-a** | Relevé immédiat ; « Mon domaine » ; pays et langue ; filtres de la page | aucun |
| **0.9.0-b** | Sources suggérées ; veilles par recherche (Google Actualités) | choisir les chaînes francophones |
| **0.9.0-c** | Page Formations : catalogue vérifié, suggestions de l'IA, suivi | aucun |

## Points à valider

1. **Relevé immédiat** si rien n'a été relevé, et bouton « Relever maintenant » (§1).
2. **« Mon domaine » par mots-clés**, sans IA ni coût, pré-rempli depuis ton profil ; sources « marché de l'emploi » toujours visibles (§2).
3. **Pays et langue** par source, filtres sur la page (§3).
4. **Sources suggérées** vérifiées, et **veilles par recherche** via Google Actualités (seuls les mots-clés sont envoyés) (§4).
5. **Page Formations** : catalogue vérifié dans le dépôt, plus des suggestions de l'IA sur demande (environ 0,02 à 0,05 $ par recherche) (§5).
6. **Mention ORP** prudente : financement possible seulement avec l'accord de ton conseiller (§5.3).
7. **Suivi** Intéressé / En cours / Terminée (§5.4).
8. **Trois PR**, dans cet ordre (§7).

## Écarts avec la PR a

- **Relevé immédiat** : à la première ouverture de la page, si aucune source active n'a jamais été relevée, et après l'ajout d'une source. C'est un relevé de **toutes** les sources actives (quelques secondes) plutôt que de la seule nouvelle source : la tâche `news` n'a pas de paramètre. La page se met à jour d'elle-même pendant le relevé (toutes les 4 s, deux minutes au plus).
- **Pré-remplissage de « Mon domaine »** : les 8 mots-clés « Poste » les plus fréquents parmi les offres auxquelles tu as postulé ou notées 70 et plus, une seule fois. Sans offre notée, la liste reste vide et la page invite à la remplir.
- **Ajout de mots-clés** : plusieurs d'un coup, séparés par des virgules ; 30 au plus.
- **Langue des contenus** : déduite du titre et du résumé (mots courants du français, de l'allemand, de l'anglais, de l'italien et de l'espagnol), sinon celle du flux ou de la source. Un contenu de langue inconnue n'est jamais caché par le filtre de langue. Les contenus déjà relevés reçoivent leur langue au prochain relevé.
- **Pays** : proposé d'après le domaine de l'adresse (.ch → Suisse, .fr → France…), « International » pour YouTube et les autres domaines ; modifiable par source.
- **Sources de départ** : SECO marqué « marché de l'emploi » ; RTS et Le Temps en Suisse, français ; les deux chaînes YouTube en international, anglais.
- **Filtres de la page** : listes Pays et Langue affichées seulement s'il y a au moins deux valeurs ; tous les filtres sont enregistrés (réglage `news_preferences`).
- **Migration 0024**.

## Écarts avec la PR b

- **Catalogue** : 25 sources, toutes vérifiées le 2026-10-06 (le flux répond, contenu de moins de deux semaines), dans `backend/src/jobbot/news/catalog.json` (JSON plutôt que YAML : aucune dépendance de plus).
  - *Marché de l'emploi* : SECO, RTS Économie, Le Temps Économie, France Travail (vidéos).
  - *Actualité informatique* : ICTjournal (Suisse, français), Inside IT et Netzwoche (Suisse, allemand), Le Monde Informatique, IT-Connect, JDN.
  - *DevOps et cloud* : blog Kubernetes, CNCF, AWS DevOps, AWS nouveautés, Azure, Google Cloud, The New Stack, HashiCorp, Docker.
  - *Vidéos* : TechWorld with Nana, KodeKloud, CNCF, xavki, Cookie connecté (DevOps en français), Grafikart (développement web).
- **Écartées** : l'OFS (dernier communiqué dans le flux il y a près de 3 ans), Swissinfo (page trop lourde, flux introuvable), InfoQ DevOps (flux arrêté), les chaînes Welcome to the Jungle, Apec et Cadremploi (inactives ou vides).
- **Flux RSS 1.0** (Le Monde Informatique) désormais lus.
- **Veilles** : le flux de Google Actualités est réservé à un usage personnel dans un lecteur de flux, ce qui est le cas ici. Pour « International », la recherche se fait sur l'édition américaine de Google Actualités. Titre sans le nom du journal, qui devient le résumé de la carte ; pas d'image. Le relevé garde les articles de moins de 60 jours.
- **Doublons** : un article déjà relevé dans les 14 derniers jours (même titre, sans tenir compte des majuscules, accents et ponctuation), dans n'importe quelle source, n'est pas repris.
- **Réglages** : trois boutons, « Parcourir les suggestions » (filtres domaine, pays, langue), « Nouvelle veille », « Ajouter par adresse » ; la veille apparaît dans la liste des sources et se met en pause ou se retire comme les autres.
- **Migration 0025** (`news_sources.query`).
- **Essai réel** : xavki ajouté depuis les suggestions (15 vidéos) et la veille « Kubernetes emploi » (Suisse, français : 6 articles de moins de 60 jours), relevés aussitôt.
