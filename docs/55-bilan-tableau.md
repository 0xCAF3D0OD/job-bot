# 55 — Le Bilan dans le style du tableau de bord (version 0.45.0)

> Statut : **validé** le 2026-10-15, livré.
> Aujourd'hui est devenu un tableau de bord en 0.44.0 (docs/54) : grandes cartes arrondies, pictogrammes dans des bulles, barres et jauge. Le **Bilan** (Candidatures › Bilan, docs/42) est la page de chiffres de la plateforme, mais il reste une ligne de nombres et quatre listes de texte. Il passe dans le même style, pour que les deux pages se ressemblent.

## 1. Ce qu'il y a aujourd'hui

- En haut, le **parcours** en une ligne : « 412 offres reçues · 96 retenues · 31 candidatures · 11 réponses · 4 entretiens · 0 engagement ».
- Le délai de réponse en petite phrase, puis la phrase de tête si un écart est net.
- **Quatre cartes de texte** (source, note, contact, relance) : « jobup 5 sur 12 ».
- Pour un mois, le bouton « Résumé pour l'ORP ».

Rien de faux, mais il faut lire chaque nombre pour voir ce qui ressort.

## 2. La page proposée (ordinateur)

```
[3 derniers mois | Un mois | Tout]

┌────────────┬────────────┬────────────┬────────────┐
│(◷) Candid. │(✉) Réponses│(☺) Entret. │(⧗) Délai   │
│  31        │  11        │  4         │  9 j       │
│ sur 96 ret.│ 35 % des   │ dont 1 à   │ de 2 à 21 j│
│ (violet)   │ envois     │ venir      │            │
└────────────┴────────────┴────────────┴────────────┘
┌──────────────────────────────────────┐ ┌──────────────────────┐
│ Ton parcours                         │ │ Par mois             │
│ Offres reçues ████████████████ 412   │ │  ▇                   │
│ Retenues      ████ 96                │ │  ▇  ▇   ▇            │
│ Candidatures  ██ 31                  │ │  ▇  ▇   ▇            │
│ Réponses      █ 11                   │ │ août sept oct        │
│ Entretiens    ▏4                     │ │ ■ candidatures       │
│ Engagement    ▏0                     │ │ ■ réponses           │
└──────────────────────────────────────┘ └──────────────────────┘
┌ (★) Tes candidatures avec un contact obtiennent plus souvent une réponse. ┐  (si écart net)
┌──────────────────────┐ ┌──────────────────────┐
│(⌂) D'où vient l'offre│ │(★) Note de l'IA      │
│ jobup    ███░░░ 5/12 │ │ 80+      ████░ 6/11  │
│ Indeed   █░░░░░ 1/9  │ │ 60–79    ██░░░ 3/14  │
│ spontanée ··· 2/3    │ │ < 60     ··· 0/2     │
│   trop peu pour conclure                      │
└──────────────────────┘ └──────────────────────┘
┌──────────────────────┐ ┌──────────────────────┐
│(☎) Contact           │ │(↻) Relance           │
└──────────────────────┘ └──────────────────────┘
┌ Résumé pour l'ORP (un mois seulement)  [Copier] ┐
```

- **Quatre tuiles**, comme sur Aujourd'hui (bulle, nom, grand chiffre, une ligne dessous) :
  1. **Candidatures** (violet plein, la tuile principale) : le nombre, « sur N offres retenues ».
  2. **Réponses** : le nombre, « N % des envois ».
  3. **Entretiens** : le nombre, « dont N à venir » s'il y en a.
  4. **Délai de réponse** : « 9 j », « de 2 à 21 jours » ; « — » s'il n'y a pas encore de réponse.
- **Ton parcours** : les six étapes en **barres horizontales**, de la plus longue (reçues) à la plus courte ; chaque ligne mène à sa liste, comme aujourd'hui. Le chiffre reste écrit au bout de la barre.
- **Par mois** (à côté) : pour « 3 derniers mois » et « Tout », candidatures et réponses par mois en barres doubles, avec la valeur dans une bulle au survol, comme « Ta semaine ». Pour « Un mois », la carte montre les **semaines** du mois.
- **Phrase de tête** : une bande menthe pâle avec sa bulle, seulement si l'écart est net (règle de docs/42 inchangée).
- **Les quatre comparaisons** : en cartes de deux colonnes, chacune avec sa bulle ; chaque groupe a une **barre de réponses sur envois** (« 5 / 12 »). Sous 5 candidatures, la barre est en pointillés gris avec « trop peu pour conclure », comme aujourd'hui.
- **Résumé pour l'ORP** : une carte en bas, le texte visible directement avec « Copier » (plus besoin de le déplier).

## 3. Cohérence

- Mêmes cartes, tuiles, bulles et barres qu'Aujourd'hui (on réutilise `DashTile`, le style des barres de `WeekChart` et les mêmes pictogrammes), thème sombre compris.
- Mêmes chiffres, mêmes règles qu'en docs/42 : rien de nouveau à interpréter. Toujours en nombres (« 5 / 12 ») ; le seul pourcentage est celui de la tuile Réponses.
- Une seule tuile en violet plein, pas d'orange : le Bilan n'a pas d'urgence.

## 4. Téléphone (sous 820 px)

Tuiles en 2 × 2, puis Ton parcours, Par mois, la phrase de tête, les quatre comparaisons l'une sous l'autre, le résumé. Le sélecteur de période reste sur une ligne.

## 5. Ce qu'il faut à l'API

`GET /api/insights` gagne deux choses, calculées depuis la base (pas d'IA) :

- `periods` : pour chaque mois de la période (ou chaque semaine pour un mois choisi), le nombre de **candidatures** envoyées et de **réponses** reçues ;
- `interviews_upcoming` : les entretiens encore à venir.

Le reste (parcours, délai, comparaisons) existe déjà.

## 6. Livraison

Une PR (**0.45.0**) : API (deux champs, tests), page, captures avant / après sur ordinateur et téléphone, clair et sombre.

## Points à valider

1. **Quatre tuiles** en tête (Candidatures en violet, Réponses, Entretiens, Délai) (§2).
2. **Parcours en barres** et **Par mois** à côté, semaines pour un mois choisi (§2).
3. **Comparaisons en barres**, toujours en nombres, seuil de 5 inchangé (§2, §3).
4. **Résumé ORP** visible directement (§2).
5. **Deux champs** ajoutés à l'API (§5), **une PR** (§6).

## Écarts avec la livraison

- **Tuile Délai** : nommée « Délai » (« Délai de réponse » était coupé sur téléphone) ; dessous, « de réponse, de 2 à 18 j » ou « de réponse, d'habitude », « pas encore de réponse » sinon. Elle ne mène nulle part (les trois autres mènent au Suivi).
- **Entretiens** : « dont N à venir » s'il y en a, sinon « sur N réponses ».
- **Par mois** : les réponses comptées sont celles des candidatures **envoyées** ce mois-là, comme dans le parcours (la somme des barres redonne les tuiles). « Tout » montre les 12 derniers mois au plus, depuis la première candidature. Pour un mois choisi, la carte s'appelle « Par semaine » : semaines du lundi, la première commence au 1er, jusqu'à aujourd'hui.
- **API** : `buckets` (début, candidatures, réponses), `unit` (`month` ou `week`) et `interviews_upcoming` (entretiens à venir parmi les candidatures de la période).
- **Barres** : candidatures en violet et réponses en menthe, en dégradé comme « Ta semaine » ; le parcours en barres pleines, à l'échelle des offres reçues.
- **Pictogrammes** : trois de plus dans `AppIcon` (reply, clock, star) ; source → globe, note → étoile, contact → personne, relance → flèche circulaire, résumé → document.
- **Vérifié** sur ordinateur en clair et en sombre (3 derniers mois et un mois), et sur téléphone à 390 px, sans débordement.
