# 27 — Filtres des offres : cartes, courbe des notes (version 0.20.0)

> Statut : **à valider**.
> Retours d'usage du 2026-10-14 : le format des filtres ne plaît pas ; modèle proposé : un panneau « Filtre » en cartes arrondies, une ligne par filtre avec sa valeur et une flèche, la **courbe des notes** au-dessus d'un curseur à deux poignées, et en bas « Effacer tout (5) » et « Afficher 16 ».

## 1. Le principe

- Les filtres sont **regroupés en cartes** blanches sur fond gris clair, coins arrondis, comme le modèle.
- **Une ligne par filtre** : son nom à gauche, sa valeur actuelle à droite en gris (« Par jour », « jobup, LinkedIn », « tous »), puis **›**. Un clic ouvre le choix **dans le même panneau** (comme une page suivante, avec « ‹ Retour »), au lieu d'empiler toutes les cases à cocher.
- La **note** garde sa place d'honneur : la courbe et le curseur restent visibles, sans clic.
- **En bas**, collés au panneau : **« Effacer tout (n) »** (nombre de filtres actifs) et **« Afficher N offres »**.

## 2. Les cartes, de haut en bas

| Carte | Lignes | Valeur affichée (exemples) |
|---|---|---|
| **Liste** | Statut · Tri | « À examiner · 12 » · « Par jour » |
| **Note** | courbe + curseur à deux poignées + deux champs | 60 – 100 |
| **Le poste** | Télétravail · Taux minimum · Chez l'employeur uniquement | « Au moins partiel » · « 80 % » · interrupteur |
| **D'où viennent les offres** | Sites · Cantons | « jobup, LinkedIn » · « VD, GE » · « tous » |

« Personnaliser les filtres » reste un petit lien sous les cartes ; un filtre masqué disparaît de sa carte, une carte vide disparaît.

## 3. La courbe des notes

- **Une courbe lissée** (comme le modèle, en vert menthe de la plateforme) : combien d'offres de la liste affichée ont chaque note, par tranches de 5 points. Elle suit les autres filtres (sites, cantons, télétravail…), pas le curseur lui-même : on voit ce qu'on écarte.
- **Deux poignées** : note minimale et maximale (aujourd'hui seulement la minimale). La partie choisie de la courbe est en couleur, le reste en gris.
- **Deux champs** sous la courbe (« 60 » – « 100 ») pour taper une valeur précise.
- Les offres **pas encore notées** : une ligne discrète sous la courbe, « 4 offres pas encore notées : visibles » ; elles sont masquées dès que le minimum dépasse 0, comme aujourd'hui.
- Sans offre notée : la courbe est remplacée par « Aucune offre notée pour l'instant ».

## 4. Ouvrir un choix

- **Statut**, **Tri**, **Télétravail** : la liste des choix, un clic choisit et revient.
- **Sites**, **Cantons** : cases à cocher avec le nombre d'offres, « Tout décocher » en haut.
- **Taux minimum** : le curseur actuel (0 à 100 %).
- **Chez l'employeur uniquement** : interrupteur directement sur la ligne, sans page suivante.

## 5. Ordinateur et téléphone

- **Téléphone** : le bouton « Filtres » ouvre ce panneau **par le bas** (comme le modèle, avec la petite poignée et ×) ; « Afficher N offres » le ferme.
- **Ordinateur** : le même panneau reste à gauche de la liste ; les filtres s'appliquent tout de suite, donc pas de bouton « Afficher » ; « Effacer tout (n) » reste en bas du panneau.
- Les filtres restent dans l'adresse de la page (partageable, gardés au rechargement), comme aujourd'hui.

## 6. Ce que la plateforme ajoute

- **Note maximale** : `?note=60-90` (aujourd'hui `?note=60`, toujours compris).
- **Répartition des notes** de la liste affichée, rendue avec les autres facettes (compteurs par tranche de 5) ; aucun appel à l'IA, aucune migration.

## 7. Livraison

Une seule PR (**0.20.0**), sans migration.

## Points à valider

1. **Cartes et lignes « nom · valeur · › »**, choix ouverts dans le même panneau (§1, §2, §4).
2. **Ordre des cartes** : Liste, Note, Le poste, D'où viennent les offres (§2).
3. **Courbe des notes** lissée, par tranches de 5, avec curseur à deux poignées et deux champs (§3).
4. **Téléphone** : panneau par le bas avec « Afficher N offres » ; **ordinateur** : panneau à gauche, application immédiate (§5).
5. **Une PR** (§7).
