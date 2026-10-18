# 73 — Des offres plus légères (version 0.60.0)

> Statut : **validé** le 2026-10-18.
> Origine : retour du 2026-10-18 sur la page Offres, « trop chargée ». Proposition faite en image, puis l'idée de Kevin : une ligne par jour, avec les offres du jour en dessous. Consigne : le texte doit rester bien aéré.

## 1. Le constat

- **Une carte d'offre prend une dizaine de lignes** : titre, entreprise, note, date, puis trois rangées d'étiquettes (Poste, Demande, Offre), puis une ligne de lieu, taux, télétravail, site et « chez l'employeur ».
- **On voit trois offres à l'écran.** Pour en comparer dix, il faut beaucoup défiler.
- **Une bonne partie se répète.** Le panneau de droite, ouvert au clic, montre déjà le détail, et la date figure sur chaque carte alors que la liste est déjà groupée.
- **Les filtres prennent toute la colonne de gauche**, même ceux qu'on touche rarement.

## 2. Le principe

**La liste sert à choisir, le panneau à détailler.** Une offre tient sur une ligne compacte, et les jours structurent la liste.

## 3. Une ligne par jour

- En tri **« Par jour »** (le tri par défaut), chaque jour a **sa ligne de date** :
  - **« Aujourd'hui »**, **« Hier »**, puis le jour en toutes lettres (**« Jeudi 15 octobre »**) ;
  - à côté, en plus discret, le nombre d'offres (« 3 offres ») ;
  - un trait fin prolonge la ligne jusqu'au bord, pour bien séparer les journées.
- **Les offres du jour suivent, dans un seul bloc** : des lignes séparées par un filet, plutôt qu'une carte par offre.
- **La date sort des offres** : la ligne du jour la donne.
- Ces lignes remplacent les intertitres d'aujourd'hui (« Aujourd'hui », « Cette semaine », « Plus ancien »). Une offre ouverte par un lien reste posée en tête, sans ligne de date.

**Autres tris** (« Par note »…) : les jours se mélangent, il n'y a donc plus de lignes de date. La date revient alors en petit dans chaque offre (« Exemple SA · Lausanne · hier »).

## 4. Une offre sur une ligne

| Reste dans la liste | Passe dans le panneau de droite (déjà là au clic) |
|---|---|
| le logo (ou l'initiale), le titre, l'entreprise et la ville | les étiquettes Poste, Demande, Offre |
| la note, à droite | le taux, le télétravail, le site d'origine, « chez l'employeur » |
| une seule ligne d'alerte, **seulement si nécessaire** : « Il te manque : Go », « À vérifier », « Arnaque possible », « Retirée » | le résumé de l'IA |

- La ligne d'alerte reprend ce qui compte pour décider :
  - les exigences que ton profil ne couvre pas (les étiquettes « ✗ » d'aujourd'hui) ;
  - les doutes (offre à vérifier, arnaque possible) ;
  - une offre retirée.
- **Un clic sur la ligne** ouvre le panneau de droite, comme aujourd'hui. Sur téléphone, il ouvre la fiche.
- La ligne choisie reste marquée, comme la carte aujourd'hui.

## 5. Du texte aéré

Une liste plus dense ne doit pas devenir serrée. Règles, mesurées sur captures :
- **Chaque ligne d'offre** a au moins 0,75 rem de marge en haut et en bas, et le titre et la ligne « entreprise · ville » ne se touchent pas.
- **La ligne de date** a plus d'air au-dessus (1,5 rem) qu'en dessous (0,6 rem) : elle appartient à ses offres, pas à celles de la veille.
- **La ligne d'alerte** est séparée du reste par un petit espace, et n'est jamais en gras.
- **Le texte garde sa taille** : titre comme aujourd'hui, ligne secondaire à 13 px au moins, rien en dessous de 12 px.
- **Une seule couleur forte par ligne** : la note. L'alerte est colorée, mais en texte simple, sans pastille.
- Chaque groupe de règles est vérifié sur ordinateur et sur téléphone, sans débordement.

## 6. Des filtres plus légers

- **Toujours visibles** : la recherche, le statut, le tri et la note.
- **Repliés dans « Plus de filtres »** : le télétravail, le taux minimum, les sites, les cantons, « chez l'employeur uniquement » et « masquer les offres à vérifier ». Entre parenthèses, le nombre de ceux qui sont actifs : « Plus de filtres (2) ».
- **« Personnaliser les filtres » reste**, dans « Plus de filtres » : un filtre que tu y coches remonte parmi les filtres toujours visibles.

## 7. Ce qui ne change pas

- Le panneau de droite, avec « Préparer ma candidature », et la page de préparation.
- Les filtres eux-mêmes, et les données : aucune règle de tri ni de note ne change.
- La page Aujourd'hui, qui a son propre tableau d'offres.

## 8. Livraison

Une PR, **0.60.0**, sans migration. Le serveur ne change pas : la liste est seulement présentée autrement.

Vérification sur captures, ordinateur et téléphone, avec la démo (`make demo`) : nombre d'offres visibles avant et après, espacements mesurés.

## Points à valider

1. **Une ligne par jour** (« Aujourd'hui », « Hier », « Jeudi 15 octobre »), avec les offres du jour en un bloc dessous, et la date qui sort des offres. Dans les autres tris, la date revient dans l'offre (§3).
2. **Une offre sur une ligne** : logo, titre, entreprise, ville, note, et une ligne d'alerte seulement si nécessaire ; le reste dans le panneau de droite (§4).
3. **Du texte aéré**, avec les règles d'espacement du §5.
4. **Des filtres repliés** dans « Plus de filtres (n) », sauf la recherche, le statut, le tri et la note (§6).
5. **Une PR 0.60.0**, sans migration (§8).

## Écarts avec le cadrage

- **Une ligne par jour pour tous les jours**, y compris les plus anciens : avec des offres sur une ligne, la liste reste courte. Le jour d'une offre est celui de Zurich.
- **L'alerte, par ordre d'importance** : la raison d'une offre écartée (« Lieu : Zürich, ZH n'est pas dans tes lieux acceptés »), puis le doute (« À vérifier », « Arnaque possible », expliqué au survol et lu par les lecteurs d'écran), puis « Retirée », puis ce qui manque (trois au plus : « Il te manque : Go, Bicep »), puis un télétravail fermé depuis la Suisse.
- **Les étiquettes ne sont pas recopiées dans le panneau** : il montre déjà le résumé complet (Poste, Demande, Offre), le taux, le télétravail, le contrat et les liens vers les sites. Les exigences non couvertes restent visibles dans la ligne d'alerte.
- **« Plus de filtres »** : un lien sous la note, « Plus de filtres (2) » quand des filtres repliés sont actifs ; il s'ouvre d'office s'il y en a au chargement. « Personnaliser les filtres » y est rangé. Un filtre coché dans « Personnaliser » ne remonte pas parmi les filtres toujours visibles : il reste dans « Plus de filtres ».
- **Les offres d'un jour forment un bloc** : une bordure commune, des coins arrondis au début et à la fin du jour, un filet entre les offres. L'offre choisie est marquée par un trait à gauche et un fond teinté.
- **Espacements mesurés** (téléphone, 375 px) : 12,8 px au-dessus et au-dessous d'une offre (14 px sur ordinateur), 5 px entre le titre et la ligne de l'entreprise, texte secondaire à 13,6 px, aucun débordement. Sur ordinateur, environ six offres tiennent dans l'écran au lieu de trois.
- **Styles de l'ancienne carte retirés** (`job-card`, étiquettes, ligne de méta) : plus utilisés nulle part.
