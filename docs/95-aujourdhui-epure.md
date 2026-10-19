# 95 — Aujourd'hui épuré (version 0.71.0)

> Statut : **validé** le 2026-10-19.
> Origine : ta question du 2026-10-19, « Aujourd'hui, est-ce que ce n'est pas trop chargé, est-ce qu'on pourrait s'inspirer de Sphere ? », puis la maquette du même jour.

## Le constat (démo, 2026-10-19)

- **11 blocs** sur ordinateur. Sur téléphone, presque **trois écrans** de défilement (2 700 px).
- **L'objectif ORP apparaît trois fois** : la carte « Octobre 6 / 10 », la carte « Semaine 0 / 2 », la jauge « Objectif ORP » et ses trois mois.
- **Les offres reçues apparaissent deux fois** : la petite courbe de « À examiner » et le graphique « 7 derniers jours ».
- **Progresser et Comprendre le marché** font double emploi avec l'étincelle de la capsule (docs/92).
- **Quatre cartes de couleurs différentes** en haut.
- **« Comment ça marche 5 / 5 »** reste affiché alors que le guide est terminé.

## La page, de haut en bas

### 1. La phrase du jour (à la manière de Sphere)

- **L'étiquette en capitales** : « Lundi 19 octobre · collecte il y a 11 h ».
- **Une phrase en grand** (1,75 rem, 1,3 rem sur téléphone) dit la situation. Les nombres à traiter sont en violet. Elle se construit avec ce qui existe, dans cet ordre :
  - les offres à examiner ;
  - les relances ;
  - ce qu'il reste à faire pour tenir la semaine.

  Exemples :
  - « **3 offres** à examiner, **2 relances**, et encore 2 candidatures pour tenir ta semaine. »
  - Rien à faire : « Tout est à jour. Ta semaine est faite. »
  - Jour sans recherche : « Jour sans recherche. Les offres t'attendent pour demain. »
  - En pause : « En pause jusqu'au 3 novembre. »
- **Un seul bouton** sous la phrase. C'est l'action la plus utile :
  - « Examiner les offres » s'il y en a ;
  - sinon « Relancer » ;
  - sinon rien.

### 2. Les bandeaux urgents (seulement s'il y a lieu)

**Un bandeau par chose datée, trois au plus**, avec un filet violet à gauche et l'action à droite :
- le rendez-vous ORP, aujourd'hui ou demain ;
- un entretien, aujourd'hui ou demain ;
- un entretien passé, à faire le point ;
- les preuves ORP à remettre.

Ce sont les avertissements d'aujourd'hui, qu'on réunit dans un même style.

### 3. À faire (la carte large)

- **Meilleures offres** : les 3 mieux notées, en lignes (logo carré, poste, entreprise et lieu, note). Le sélecteur « Mieux notées / Commencées » reste.
- **À relancer** : les 2 plus urgentes, avec « Relancer » au bout de la ligne, puis le lien « Toutes les relances » vers le Suivi.
- **Rien à faire** : une phrase, sans illustration.

### 4. Ton mois ORP (la carte étroite)

- **Le compte** : « 6 / 10 candidatures en octobre », en grand. Une barre, puis une phrase : « Encore 4 d'ici le 31 octobre », ou « Objectif atteint ».
- **Cette semaine** : le compte (« 0 / 2 ») et un point par jour, comme la carte Semaine d'aujourd'hui.
- **Le lien « Voir le bilan »**.

### 5. Les guides (seulement s'ils ne sont pas terminés)

« Pour bien démarrer » et « Comment ça marche » restent repliés en bas, et **disparaissent une fois terminés**.

## Ce qui quitte la page, et où le retrouver

| Bloc | Où |
|---|---|
| Les quatre cartes du haut (À examiner, Octobre, À relancer, Preuves ORP) | dans la phrase du jour, les bandeaux et Ton mois ORP |
| 7 derniers jours (graphique) | Candidatures › Bilan, « Par mois », qui montre déjà les semaines d'un mois |
| La jauge Objectif ORP et les trois mois précédents | Candidatures › Bilan, en tête quand on regarde un mois |
| Semaine | dans Ton mois ORP |
| Progresser, Comprendre le marché | l'étincelle de la capsule (docs/92) |

## Aéré (docs/93)

- **L'espacement** : 2 rem entre la phrase et les bandeaux, puis entre les bandeaux et les cartes. Les cartes ont 1,5 rem de marge intérieure.
- **Les cartes sont neutres** : fond blanc, bordure fine. La couleur ne sert qu'aux nombres à traiter, à la barre et aux notes.
- **La grille** :
  - sur ordinateur, À faire et Ton mois ORP côte à côte (3 / 2) ;
  - sur téléphone, l'une sous l'autre, À faire d'abord.

  But : la page tient en environ un écran et demi sur téléphone.

## L'assistant

**`assistant-v13`** décrit la nouvelle page Aujourd'hui, et dit que la jauge et le graphique sont dans le Bilan.

## Vérifié avant la PR

- **Tests** :
  - la phrase dans ses cas (offres et relances, rien à faire, jour sans recherche, pause) ;
  - le bouton qui suit la situation ;
  - les bandeaux (trois au plus, seulement s'il y a lieu) ;
  - À faire (3 offres, 2 relances) ;
  - Ton mois ORP ;
  - les guides cachés une fois terminés ;
  - la jauge dans le Bilan.
- **L'audit des rangées** (docs/94) est vide.
- **Captures**, sur ordinateur et téléphone, en clair et en sombre :
  - la démo ;
  - un jour sans rien à faire ;
  - un jour avec un rendez-vous ORP ;
  - la hauteur de la page sur téléphone, mesurée.

## Écarts

- **« Mois ORP » plutôt que « Ton mois ORP »** : la règle de docs/88 interdit les possessifs dans les titres.
- **La phrase** : les nombres en violet, sans gras ; « et » avant le dernier élément, pas de virgule devant.
- **Les relances** : `/api/today` renvoie maintenant les deux plus anciennes (`follow_ups`) ; « Relancer » ouvre la candidature dans le Suivi, sur son mois (`?candidature=ID`, nouveau).
- **Les bandeaux** : les preuves ORP à remettre apparaissent dès qu'il y a un mois à remettre (avant, seulement à 5 jours de l'échéance, le reste du temps dans une tuile) ; les alertes qui n'envoient rien rejoignent les bandeaux.
- **Hauteur sur téléphone** : 1 900 px au lieu de 2 700 dans la démo (environ deux écrans et quart, pas un écran et demi) : les deux cartes restent complètes. Sur ordinateur, 1 280 px au lieu de 1 713.
- **Le graphique des 7 jours** (`WeekChart`) est retiré : le Bilan montre déjà les semaines d'un mois. La jauge (`OrpGauge`) est dans le Bilan, pour le mois en cours et les dernières semaines.
- **Vérifié** :
  - 325 tests de l'interface (Aujourd'hui réécrit : la phrase dans ses cas, le bouton, les bandeaux, À faire, Mois ORP, le guide terminé qui disparaît ; la jauge dans le Bilan) et 530 tests serveur (nouveau : `follow_ups`), lint et typecheck ;
  - audit des rangées vide ;
  - captures sur la démo, ordinateur et téléphone ; le Bilan avec la jauge.
