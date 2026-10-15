# 54 — Aujourd'hui en tableau de bord (version 0.44.0)

> Statut : **validé** le 2026-10-15, livré.
> Retour du 2026-10-15, avec une maquette de tableau de bord (« Cryptech ») : « j'ai un problème avec le dashboard Aujourd'hui, j'aimerais que ça ressemble plus à cela ; attention, il faut garder une cohérence avec le design du reste de la plateforme ».

## 1. Ce que la maquette apporte, et ce qu'on en garde

| Dans la maquette | Ce qu'on en garde | Ce qu'on ne prend pas |
|---|---|---|
| Une grille de **grandes cartes arrondies**, toutes à la même hauteur dans une rangée | oui : la page devient une grille, plus de suite de sections titrées | — |
| **Quatre tuiles** : icône ronde, nom, petite tendance (« 0,34 % ↗ »), **grand chiffre**, petite courbe | oui, pour nos quatre chiffres | — |
| **Une tuile colorée en plein** (vert-jaune), une autre teintée (bleu clair) | oui, avec **nos couleurs** : violet de la plateforme pour la tuile principale, menthe pâle pour la seconde | le vert-jaune |
| **Graphique en barres** de la semaine, sélecteur de période, bulle sur la barre survolée | oui : l'activité de la semaine | — |
| **Tableau** « All Crypto » : lignes claires, colonnes alignées, petite courbe par ligne | oui : les offres à examiner en priorité | les courbes par ligne |
| **Jauge** « Fear and Greed » avec trois cases de comparaison | oui : l'objectif ORP du mois, comparé aux mois précédents | — |
| Menu en pilule, avatar | non : la barre de navigation reste celle de toute la plateforme | menu, avatar |

## 2. La page proposée (ordinateur)

```
Jeudi 15 octobre                                         (en-tête habituel)
[ Preuves de septembre à remettre : échéance passée le 5 octobre · Préparer la remise ]  (si urgent)

┌──────────────┬──────────────┐ ┌─────────────────────────────────────────┐
│▣ À examiner  │◷ Octobre     │ │ Ta semaine        [Offres reçues|Candid.]│
│  +5 sem. ↗ ~ │  +2 sem. ↗ ~ │ │  ▇                                       │
│  21          │  4 / 10      │ │  ▇   ▇        ▇                          │
│ (violet)     │              │ │  ▇ ▇ ▇ ▇  ▇  ▇ ▇                         │
├──────────────┼──────────────┤ │ lun mar mer jeu ven sam dim              │
│↻ À relancer  │▤ Preuves ORP │ │                                          │
│  dont 1 contact│ septembre  │ │                                          │
│  5           │  5 octobre   │ │                                          │
│              │ (menthe)     │ │                                          │
└──────────────┴──────────────┘ └─────────────────────────────────────────┘
┌──────────────────────────────────────────────┐ ┌────────────────────────┐
│ À examiner en priorité   [Mieux notées|Commencées 1]│ Objectif ORP          │
│ Offre                 Note  Lieu      Reçue  │ │      ╭──────╮          │
│ (S) Cloud Architect    92   Genève    6 oct ›│ │    ╱    4    ╲         │
│     Sion Compute SA                          │ │   │  sur 10   │        │
│ (H) DevOps Engineer    88   Fribourg  6 oct ›│ │                         │
│ …  (5 lignes)                                │ │ Sept. 8 · Août 10 · Juil.12│
└──────────────────────────────────────────────┘ └────────────────────────┘
┌──────────────────────────────┐ ┌──────────────────────────────┐
│ Progresser : CKA, module 6/12│ │ Actualités de ton domaine (3) │
└──────────────────────────────┘ └──────────────────────────────┘
   Comment ça marche · Pour bien démarrer   (lignes repliables, comme aujourd'hui)
```

- **Quatre tuiles** (gauche, 2 × 2), chacune cliquable vers sa page :
  1. **À examiner** (violet plein) : le nombre d'offres, « +N cette semaine ↗ », la courbe des offres reçues sur 7 jours.
  2. **Le mois** : « 4 / 10 » candidatures, « +N cette semaine », la courbe des envois sur 7 jours.
  3. **À relancer** : le nombre, « dont N contacts ».
  4. **Preuves ORP** (menthe pâle ; orange pâle si l'échéance est proche ou passée) : la date limite et le mois concerné.
- **Ta semaine** (droite) : barres du lundi au dimanche, **Offres reçues** ou **Candidatures envoyées** ; au survol d'une barre, sa valeur dans une bulle sombre, comme la maquette.
- **À examiner en priorité** : tableau des 5 offres les mieux notées (logo, titre et entreprise, note, lieu, date de réception, « › » qui ouvre l'offre) ; un second onglet **Commencées** pour les candidatures en préparation (« Continuer › »).
- **Objectif ORP** : jauge en demi-cercle (du rouge au vert, comme la maquette, adoucie) avec le compte du mois au centre, et trois cases : les **trois mois précédents** (« 8 · manqué », « 10 · atteint »).
- **En bas** : Progresser et Actualités en deux cartes ; les guides restent des lignes repliables.

## 3. Cohérence avec le reste

- Mêmes cartes que partout (bord, rayon, ombre), mêmes couleurs (violet, menthe, orange pâle des avertissements), même police, thème sombre compris.
- Les chiffres reprennent ceux d'aujourd'hui : rien de nouveau à comprendre, seulement une autre mise en page.
- L'urgence reste en premier (bandeau), une seule tuile en orange au plus (docs/43).

## 4. Téléphone (sous 820 px)

Les quatre tuiles en 2 × 2 (chiffres plus petits, sans courbe), puis Ta semaine, l'Objectif ORP, le tableau en lignes (titre, entreprise, note), Progresser et Actualités l'un sous l'autre.

## 5. Ce qu'il faut à l'API

`GET /api/today` gagne deux listes, calculées depuis la base (aucun appel à l'IA) :

- `week` : les 7 derniers jours, pour chacun le nombre d'**offres reçues** et de **candidatures envoyées** ;
- `orp_history` : les 3 mois précédents, leur nombre de candidatures et l'objectif.

## 6. Livraison

Une PR (**0.44.0**) : API (deux listes, tests), page, captures avant / après sur ordinateur et téléphone, clair et sombre.

## Points à valider

1. **Grille de cartes** : quatre tuiles (violet plein, menthe), Ta semaine en barres, tableau des offres, jauge ORP (§2).
2. **Nos couleurs**, pas celles de la maquette ; la navigation ne change pas (§1, §3).
3. **Deux listes** ajoutées à l'API (§5).
4. **Une PR** (§6).

## Écarts avec la livraison

- **Pictogrammes dans des bulles** (demande à la validation : « inspire-toi de celles de la maquette ») : tracés fins dans un rond, sur les quatre tuiles (offres reçues, envoi, relance, preuves) et sur les cartes Progresser et Actualités ; dans le tableau, le logo de l'entreprise dans son rond. Nouvelles icônes dans `AppIcon` : inbox, send, refresh, file, trend, book, news.
- **Tuiles** : le mois sans l'année (« Octobre »), libellés et tendances sur une ligne ; la tuile « À relancer » passe en orange pâle quand c'est l'urgence du jour, « Preuves ORP » sinon (une seule à la fois, docs/43).
- **Ta semaine** : la valeur s'affiche aussi au clavier (focus sur une barre) ; « N offres sur 7 jours » sous le titre.
- **Objectif ORP** : sous le chiffre, « sur 10 · dans les temps / à rattraper / atteint » selon le jour du mois ; sans objectif saisi, « objectif à saisir » et pas de marqueur.
- **Tableau** : les deux onglets (Mieux notées, Commencées) ; « › » ouvre l'offre, « Continuer › » sa préparation. Sur téléphone, sans les colonnes Lieu et Reçue.
- **Téléphone** : tuiles 2 × 2 sans courbe, puis Ta semaine, Objectif ORP, le tableau. Vérifié à 390 px, sans débordement.
- **Ordinateur** : vérifié en clair et en sombre (captures).
