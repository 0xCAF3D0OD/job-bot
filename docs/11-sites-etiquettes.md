# 11 — Expiration signalée, sites ajoutés, étiquettes en mots-clés (version 0.7.0)

> Statut : **validé** le 2026-10-05, sites retenus : **jobs.ch** et **LinkedIn**. livré : PR a (expiration signalée), PR b (mots-clés), PR c (sites suivis).
> Retours d'usage du 2026-10-05. S'appuie sur [10-ergonomie.md](10-ergonomie.md) §1 (offres expirées), [03-collecte-gmail.md](03-collecte-gmail.md) (alertes e-mail) et [06-note-ia.md](06-note-ia.md) (résumé).

## 1. Signaler une offre expirée (ou non)

La détection automatique (page jobup introuvable, 30 jours sans alerte pour Indeed) se trompe parfois. Tu peux trancher :

- **Dans le détail d'une offre** : « Signaler comme expirée ». L'offre part dans l'onglet Expirées, avec la mention « signalée par toi ».
- **Sur une offre expirée** (détectée ou signalée) : « Pas expirée ». L'offre revient dans sa liste.
- **Ton choix passe avant la détection** :
  - une offre que tu dis « pas expirée » n'est plus marquée par la règle des 30 jours ni par la revérification jobup ;
  - une offre que tu signales expirée ne revient pas si elle réapparaît dans une alerte (seules les expirations automatiques sont annulées dans ce cas).
- Une candidature déjà envoyée reste intouchable.

## 2. Ajouter des sites

**Aujourd'hui** : la plateforme lit les alertes de jobup et d'Indeed. Celles d'un autre site arrivent dans le Journal comme « non reconnues ».

**Ce qui change** : une section **« Sites suivis »** dans Réglages liste les sites, avec pour chacun le nombre d'alertes reçues et la date de la dernière. Un bouton **« Ajouter un site »** demande :

| Champ | Exemple |
|---|---|
| Nom | jobs.ch |
| Adresse(s) d'expédition des alertes | `noreply@jobs.ch` |
| Adresse du site | `https://www.jobs.ch` |

**Comment les offres d'un nouveau site sont lues :**

1. **Sites connus** : la plateforme sait déjà les lire, sans IA.
   - **jobs.ch** appartient au même groupe que jobup : même format d'alerte et de page, donc lecture complète (lien de candidature, texte, expiration).
   - **Job-Room** était déjà prévu.
2. **Autres sites** : l'**IA lit l'e-mail d'alerte** et en extrait les offres (titre, entreprise, lieu, taux, lien).
   - Ton nom et tes coordonnées sont retirés de l'e-mail avant l'envoi, comme pour le CV.
   - Seuls les liens réellement présents dans l'e-mail sont gardés : l'IA ne peut pas en inventer.
   - Effort bas, environ 0,01 $ par e-mail, dans le plafond mensuel (`llm_calls`, `purpose = extract`).
   - Sans clé API, les e-mails restent « non reconnus », comme aujourd'hui.
3. Pour ces sites, l'expiration suit la règle des 30 jours sans alerte (pas de lecture de page).

**De ton côté** : créer l'alerte sur le site, puis la faire arriver dans ton libellé Gmail `job-bot`, comme pour jobup. Pour le premier e-mail de chaque nouveau site, transfère-m'en un exemple : je vérifie la lecture et j'en fais un exemple anonymisé pour les tests, que tu relis avant qu'il entre dans le dépôt.

Un site peut être **mis en pause** (ses alertes ne sont plus lues) ou supprimé ; ses offres déjà collectées restent.

## 3. Étiquettes des offres : des mots-clés

**Constat** : sur les cartes, les lignes Poste, Demande et Offre sont des phrases coupées, donc peu utiles.

**Ce qui change** : l'IA produit en plus des **mots-clés courts** (25 caractères au plus chacun). La carte les affiche en **pastilles**, sur une ligne par catégorie :

| Catégorie | Nombre | Exemple |
|---|---|---|
| Poste | 3 au plus | DevOps · AWS · astreintes |
| Demande | 5 au plus | 3 ans d'exp. · Kubernetes · allemand B2 |
| Offre | 4 au plus | 80-100 % · CDI · télétravail 2 j |

- Les demandes que ton profil ne couvre pas sont **en orange**, d'après les manques déjà calculés par la note.
- Le **détail** de l'offre garde les trois phrases complètes, utiles pour lire avant d'ouvrir l'annonce.
- **Offres déjà notées** : leurs mots-clés n'existent pas encore. Je propose de renoter en lot les offres à examiner, plus tard et en préparation : environ 220 offres, à moitié prix en lot, soit environ 2 $. En attendant, la carte garde les phrases.

## 4. Base (migration 0014)

```
offers        + expiry_override (expired|alive)?     -- choix de Kevin, prioritaire
evaluations   + keywords_role[], keywords_asks[], keywords_offers[]
sites         id, name, senders[], url, reader (jobup|indeed|jobroom|ai), active, created_at
```

`offers.expiry_source` accepte aussi `manual`. Les sources d'alertes (`searches.source`, `offer_links.source`) deviennent un nom de site plutôt qu'une liste fixe.

## 5. Livraison en trois PR

| PR | Contenu | Prérequis de ton côté |
|---|---|---|
| **0.7.0-a** | Signaler expirée / pas expirée | aucun |
| **0.7.0-b** | Étiquettes en mots-clés, renotation en lot | accord pour environ 2 $ de renotation |
| **0.7.0-c** | Sites suivis : section Réglages, jobs.ch, lecture par l'IA des autres sites | un exemple d'alerte par nouveau site |

## Points à valider

1. **Ton choix passe avant la détection automatique**, dans les deux sens (§1).
2. **Sites connus lus sans IA** (jobs.ch, Job-Room), **les autres par l'IA** avec un e-mail nettoyé de tes coordonnées et uniquement les liens présents (§2).
3. **Quels sites ajouter en premier ?** Par exemple jobs.ch, Job-Room, LinkedIn, jobscout24.ch, Glassdoor. Indique ceux où tu as (ou vas créer) des alertes (§2).
4. **Mots-clés en pastilles** sur les cartes, demandes non couvertes en orange, phrases complètes dans le détail (§3).
5. **Renotation en lot** des offres encore utiles, environ 2 $ (§3).
6. **Trois PR**, dans cet ordre (§5).

## Écarts avec la PR a

- **Migrations** : la 0014 ne contient que le choix de Kevin (`expiry_override`, `expiry_source = manual`). Les mots-clés et les sites auront leurs propres migrations (0015, 0016).
- **Boutons** : « Signaler comme expirée » et « Pas expirée » sont dans la ligne d'actions du détail, à côté de « Plus tard » et « Ignorer ». Absents une fois la candidature envoyée.

## Écarts avec la PR b

- **Migration 0018** (et non 0014 comme prévu au §4, décalée par la 0.7.1 et la 0.7.2).
- **Renotation** : automatique, par la tâche `score`, dès la mise à jour : toute note faite avec les anciennes consignes (« score-v1 ») est refaite, y compris pour les offres « plus tard » et « en préparation ». Au-delà de 20 offres, en lot à moitié prix.
- **Lots** : chaque lot retient ses consignes. Une note d'un lot envoyé avant la mise à jour est gardée, puis refaite pour avoir ses mots-clés. Une offre d'un lot annulé ou expiré n'est plus marquée en erreur : elle est simplement renotée.
- **Phrases** : une carte sans mots-clés (note ancienne) garde les trois phrases ; le détail les montre toujours.

## Écarts avec la PR c

- **jobs.ch** est lu par l'IA (Claude Haiku 4.5), comme LinkedIn : sans exemple d'alerte jobs.ch, impossible de vérifier qu'elle a le même format que jobup. La lecture des **pages** jobs.ch (lien de candidature, texte complet, adresse, expiration) viendra avec un exemple ; en attendant, ses offres expirent par la règle des 30 jours.
- **Modèle** : Haiku, et non Opus : environ **0,001 à 0,01 $ par e-mail** (essai : 0,0013 $ pour une alerte LinkedIn de 2 offres).
- **Liens** : chaque lien de l'e-mail est numéroté et l'IA ne peut citer qu'un numéro ; les paramètres de suivi (qui peuvent t'identifier) sont retirés, et un lien LinkedIn devient `https://www.linkedin.com/jobs/view/<numéro>/`.
- **Sites intégrés** : jobup et Indeed (non retirables, mais on peut les mettre en pause) ; **suggérés** et actifs : jobs.ch, LinkedIn ; **Job-Room** présent mais en pause.
- **Alertes déjà reçues** : « Relire les alertes non reconnues » (Réglages) les traite, par exemple après l'ajout d'un site ; aussi en ligne de commande : `jobbot reparse --unrecognized`.
- **Sans clé API ou au plafond** : l'alerte reste « non reconnue », gardée pour une relecture.
- **Identifiants de site** libres (`[a-z0-9]{2,30}`) dans `searches.source` et `offer_links.source` (migration **0020**).
