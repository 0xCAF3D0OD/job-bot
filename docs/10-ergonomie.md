# 10 — Offres expirées, prise en main et filtres au choix (version 0.6.1)

> Statut : **validé** le 2026-10-05. PR a (offres expirées) livrée ; PR b et c à venir.
> Retours d'usage du 2026-10-05. Les rappels ORP (0.6.0-b) restent prévus, après cette version ou avant, à ton choix.

## 1. Offres expirées

**Constat.** Une offre retirée par l'employeur reste affichée. La plateforme sait déjà en repérer une partie : la lecture des pages jobup a marqué 12 offres « expirées », mais la page Offres ne s'en sert pas. Et une offre n'est vérifiée qu'une fois, à son arrivée.

**Ce qui change :**

| Site | Comment on sait qu'une offre a expiré |
|---|---|
| jobup | la page de l'offre répond « introuvable » (404 ou 410), ou annonce que l'offre n'est plus disponible |
| Indeed | impossible de vérifier (protection anti-robots, que l'on ne contourne pas) : l'offre est dite **probablement expirée** si aucune alerte ne l'a montrée depuis **30 jours** |

- **Revérification** des offres jobup encore utiles (à examiner, plus tard, en préparation) **tous les 3 jours**, au même rythme prudent que la lecture actuelle (une page toutes les 10 secondes, 30 au plus par passage).
- Une offre expirée **disparaît** de « À examiner », « Plus tard » et « Toutes ». Un nouvel onglet **Expirées** les garde, pour mémoire.
- Une offre **en préparation** qui expire n'est pas masquée : elle reçoit un bandeau « Offre expirée le … », pour que tu ne prépares pas une lettre pour rien.
- Une candidature **déjà envoyée** n'est jamais touchée : ton suivi et l'export ORP restent complets.
- L'IA ne note plus une offre expirée (économie).
- Si une offre expirée réapparaît dans une alerte, elle redevient visible.

## 2. Tout ce qui te concerne au même endroit

**Constat.** Tes informations sont dispersées : coordonnées dans Réglages, documents et blocs dans Profil, prérequis dans une page à part. Rien ne dit ce qui manque pour que la plateforme fonctionne bien.

**Proposition :**

**a) Page « Profil » en trois onglets** (au lieu de deux pages et une section de Réglages) :

| Onglet | Contenu |
|---|---|
| **Ce que je cherche** | les prérequis actuels (lieux, taux, types exclus, mots interdits, langues), en tête car ils pilotent tout le tri |
| **Mon parcours** | documents et blocs de profil (inchangés) |
| **Mes coordonnées** | déplacées depuis Réglages |

**Réglages** ne garde que le fonctionnement de la plateforme : objectif ORP, notifications, plafond de l'IA, et l'état technique (l'actuelle page État, qui quitte le menu).

**b) Une page d'accueil « Aujourd'hui »**, première page à l'ouverture, en une seule vue :

- **Démarrage** (tant qu'il reste quelque chose à faire, puis la carte disparaît) : une liste à cocher automatiquement, chaque ligne menant au bon endroit :
  1. prérequis saisis ;
  2. un CV déposé et des blocs de profil ;
  3. coordonnées complètes ;
  4. objectif ORP ;
  5. notifications configurées ;
  6. collecte Gmail configurée.
- **Le point du jour** : nouvelles offres à examiner (dont les mieux notées), candidatures du mois par rapport à l'objectif, relances à faire, prochaine échéance ORP.
- **Collecte** : dernière collecte, prochaine, bouton « Collecter ».

**c) Menu raccourci** : Aujourd'hui · Offres · Candidatures · ORP · Profil · Réglages. Le **Journal** des alertes devient un onglet de la page ORP (c'est la preuve de recherche) ; **État** passe dans Réglages.

## 3. Filtres au choix

**Constat.** Le panneau de filtres de la page Offres affiche tout (recherche, note minimale, sites, cantons, taux minimum, candidature chez l'employeur), même ce que tu n'utilises pas.

**Ce qui change :**

- Un lien **« Personnaliser »** en haut du panneau ouvre une liste de cases à cocher : un filtre par case.
- Le statut (À examiner, En cours…), la recherche et le tri restent toujours affichés.
- Ton choix est enregistré dans tes réglages (en base, pas seulement dans le navigateur) et retrouvé à chaque ouverture.
- Un filtre masqué qui était actif est remis à zéro, pour qu'aucun filtre invisible ne cache des offres.
- Par défaut : tous les filtres affichés, comme aujourd'hui.

## 4. Base (migration 0013)

```
offers     + expired_at?, expiry_source? (page|age), checked_at?   -- dernière vérification
settings   + offer_filters_visible (liste), onboarding_dismissed?
```

## 5. Livraison en trois PR

| PR | Contenu |
|---|---|
| **0.6.1-a** | Offres expirées : détection, revérification, onglet Expirées, bandeau |
| **0.6.1-b** | Profil en trois onglets, Réglages allégés, page Aujourd'hui avec le démarrage, menu raccourci |
| **0.6.1-c** | Filtres au choix |

## Points à valider

1. **Indeed** : « probablement expirée » après **30 jours** sans apparaître dans une alerte (§1).
2. **jobup** revérifiée **tous les 3 jours** (§1).
3. Offre expirée **masquée**, sauf en préparation (bandeau) et une fois envoyée (jamais touchée) (§1).
4. **Profil en trois onglets**, prérequis en premier ; coordonnées déplacées depuis Réglages (§2 a).
5. **Page Aujourd'hui** avec la liste de démarrage et le point du jour, première page à l'ouverture (§2 b).
6. **Menu** : Journal dans ORP, État dans Réglages (§2 c).
7. **Filtres au choix** : cases à cocher, choix enregistré en base ; statut, recherche et tri toujours visibles (§3). Si tu pensais plutôt à autre chose (par exemple choisir les cantons proposés), dis-le-moi.
8. **Trois PR**, les offres expirées d'abord (§5).

## Précision demandée à la validation (PR b)

Les prérequis ne sont **pas redemandés à chaque ouverture**. Ils sont saisis **une fois**, à la première utilisation (étape de la liste de démarrage). Ensuite, un bouton « Modifier ce que je cherche » les rouvre, **déjà remplis** avec les valeurs actuelles : on ne change que ce qui a bougé.

## Écarts avec la PR a

- **Redirection** : une page jobup qui renvoie ailleurs qu'une page d'offre (liste, accueil) compte comme expirée, au même titre qu'une réponse 404 ou 410. Le texte « offre plus disponible » n'est pas analysé : pas d'exemple de page pour le tester.
- **Ancienneté** : la règle des 30 jours s'applique à toute offre sans lien jobup (aujourd'hui, Indeed), pas aux offres jobup, vérifiées par leur page.
- **Réapparition** : une offre expirée revue dans une alerte redevient visible ; si sa page jobup était introuvable, elle est relue.
- **Compteurs** : « Toutes » exclut les expirées, sauf celles en cours (en préparation ou envoyées).
- Les 12 offres déjà repérées comme expirées sont reprises par la migration 0013.
