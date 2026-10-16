# 64 — Revue après 0.46 à 0.48 : l'assistant à jour, le ménage, le téléphone (version 0.48.3)

> Statut : **validé** le 2026-10-16, livré.
> Sept versions de suite sur le mouvement et les illustrations (docs/58 à 63), dont plusieurs ont défait la précédente : illustrations dans les cartes, puis à côté, puis retirées des formulaires ; frise, puis guides côte à côte, puis frise. Il en reste des traces dans le code, l'assistant ne connaît pas ce qui a été ajouté, et presque tout a été fait et vérifié sur ordinateur.

## 1. L'assistant ne connaît pas ce qui a été ajouté

| Constat | Correction |
|---|---|
| Son guide dit « Progresser (formation en cours) » ; depuis 0.48.2, la carte montre jusqu'à **trois** formations : en cours d'abord, puis des suggestions. | Guide à jour. |
| Il ne connaît pas **« Ce que donnent tes critères »** (Profil › Ce que je cherche) : à « pourquoi je reçois si peu d'offres ? », il ne peut que lire les offres une à une. | Une section dans le guide, et une **fonction de lecture** `criteres` : les critères actuels et le résumé des 3 derniers mois (offres reçues, retenues, trois raisons d'écart les plus fréquentes), calculé comme sur la page. Lecture seule, sans IA de plus, sans donnée personnelle. |
| Il ne connaît pas la **dépense du mois** à côté du plafond (Réglages › IA). | Guide à jour ; sa section « Coût de l'IA » renvoie à cette carte. |
| Sur Profil, ses suggestions ne parlent que des blocs de profil (« Que manque-t-il à mon profil ? »…), rien sur les critères. | « Quelles compétences mettre en avant ? » cède la place à **« Quel critère m'écarte le plus d'offres ? »**. |

La consigne passe en **`assistant-v5`** (même contenu, ces sections mises à jour). Les actions proposées (docs/52) ne changent pas : l'assistant **ne modifie pas** les critères, il explique et conseille.

## 2. Le ménage

| Reste | Venu de | Correction |
|---|---|---|
| Les règles `.illustrated.moment` et `.moment-links` (la réussite illustrée dans la page) | 0.47.1 et 0.47.2, remplacée par la carte qui vient devant (0.48.0) | retirées |
| `.dash-col-action` (colonne d'action du tableau d'Aujourd'hui) | 0.44.0, retirée avec les « › » (0.45.2) | retirée |
| Des commentaires qui renvoient à des documents dépassés (« docs/60 §2.1 » pour la carte de réussite, « petite illustration » pour les pages vides) | 0.47 | renvoient au document en vigueur |
| `docs/interface.md` dit « 140 px sur téléphone » et « trois durées » ; la carte de réussite (130 px, 420 ms), l'Engagement (200 px) et la transition (400 ms, 1,2 s au moins) n'y figurent pas | 0.48.0 à 0.48.2 | les **moments** et la **transition** ajoutés comme exceptions écrites (rien ne change à l'écran) |

Une recherche sur toute la feuille de style (chaque classe confrontée au code) n'a trouvé que ces restes ; les 10 illustrations du dépôt servent toutes.

## 3. Le téléphone

Vérifier à 375 px de large, clair et sombre, ce qui a été ajouté depuis 0.46 et corriger ce qui ne va pas :

- la **carte de réussite** (« Candidature envoyée », « Preuves remises ») : en bas de l'écran, l'image au-dessus de la carte, sans dépasser en haut ;
- l'**Engagement** : image, confettis et texte tiennent dans l'écran ;
- la **transition** d'une page qui charge : voile, image de 140 px, nom de la page ;
- **Profil › Ce que je cherche** : « Ce que donnent tes critères » sous le résumé, barres lisibles ;
- **Réglages › IA** : la carte de la dépense sous le champ ;
- **Aujourd'hui** : les guides en liste, Progresser avec trois formations ;
- **Suivi** : les semaines sans candidature plus basses dans le calendrier du téléphone ;
- les **pages vides** et la **connexion** : image de 140 px au-dessus du texte.

Ce qui est corrigé est décrit dans les écarts, avec une capture avant / après.

## 4. Vérifications

- Tous les tests passent, sans en retirer ; un test pour la fonction `criteres`, un pour la suggestion de Profil, un pour la consigne (elle cite « Ce que donnent tes critères » et la dépense du mois).
- Captures d'ordinateur avant / après d'Aujourd'hui, Profil et Réglages : **identiques** (le ménage ne change rien à l'écran).
- Pas de changement de base ; une fonction de plus pour l'assistant, pas de nouvelle route.

## 5. Livraison

Une PR (**0.48.3**).

## Points à valider

1. **Guide de l'assistant** à jour (Progresser, ce que donnent tes critères, dépense du mois), consigne `assistant-v5` (§1).
2. **La fonction `criteres`** pour l'assistant, en lecture seule, et une **suggestion** sur les critères dans Profil (§1).
3. **Le ménage** : règles CSS mortes, commentaires, exceptions écrites dans `docs/interface.md` (§2).
4. **Le téléphone** vérifié et corrigé pour tout ce qui vient de 0.46 à 0.48 (§3).
5. **Une PR** (§5).

## Écarts avec la livraison

- **Assistant** : consigne `assistant-v5` ; la fonction `criteres` rend les critères, la période, les offres reçues et retenues, et les raisons d'écart (même calcul que la page). Sa section Profil lui dit qu'il peut conseiller d'assouplir un critère, sans le changer lui-même.
- **Ménage** : 10 lignes de CSS retirées (réussite illustrée dans la page, colonne « › » du tableau) ; commentaires renvoyant à docs/61 et docs/62 ; exceptions écrites dans `docs/interface.md`.
- **Trouvé en vérifiant, corrigé** :
  - **Barres de « Ce que donnent tes critères »** toutes pleines, sur ordinateur comme sur téléphone : la largeur était écrite « 40 % » (avec une espace), que le navigateur ignore. Elles suivent maintenant le nombre d'offres ; un test le vérifie.
  - **Sélecteurs** (Télétravail complet, sur téléphone) : un libellé long élargissait sa colonne, et la pastille violette, calculée pour des colonnes égales, débordait sur le choix voisin. Les colonnes restent égales, le libellé passe à la ligne.
  - **Guides d'Aujourd'hui** sur téléphone : 32 px entre les deux au lieu des 20 px entre les autres cartes.
  - **Page introuvable** : le fond gris s'arrêtait sous le texte, une bande blanche dessous ; il va jusqu'en bas de l'écran, sans défilement.
- **Vérifié** à 375 px : Profil › Ce que je cherche (clair et sombre), Réglages › IA, Aujourd'hui, calendrier du Suivi, la carte « Candidature envoyée » déclenchée pour de vrai, la page introuvable ; sur ordinateur, les sélecteurs et la page introuvable inchangés à l'œil. La transition et l'Engagement sur téléphone : vérifiés dans la feuille de style (140 px et 200 px), pas rejoués.
