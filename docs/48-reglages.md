# 48 — Réglages : une rubrique à la fois, des lignes calmes (version 0.40.0)

> Statut : **validé** le 2026-10-15, livré.
> Revue de la page Réglages après docs/44 à 47. Capture du 2026-10-15, ordinateur, données de test : 6 sites suivis, 5 sources d'actualités.

## 1. Ce qui ne va pas

| # | Constat |
|---|---|
| 1 | **Une seule page de cinq écrans** : huit rubriques à la suite (Recherche d'emploi, Actualités, Notifications, IA, Profils d'essai, Connexion, Agenda, Extension). Le sommaire à gauche fait défiler, mais on perd vite où l'on est, et les rubriques courtes (Connexion : une phrase) sont noyées entre les longues. |
| 2 | **Chaque source d'actualités porte six contrôles sur sa ligne** : région, langue, « marché de l'emploi », « suivie », « Retirer » ; avec cinq sources, une trentaine de champs visibles d'un coup. |
| 3 | **Sites suivis** : même constat en plus léger (« aucune alerte », case « suivi », « Retirer » sur chaque ligne) ; « Retirer » en rouge sur toutes les lignes attire l'œil vers l'action la plus rare. |
| 4 | « Recherche de l'annonce chez l'employeur » et « Seuil de notification » sont deux nombres sur 100 côte à côte, sans dire lequel sert à quoi sans ouvrir l'aide. |

## 2. Une rubrique à la fois

Le sommaire de gauche devient une **navigation** : un clic affiche **la rubrique seule** (adresse `/reglages?rubrique=actualites`), comme les onglets de Profil. La page fait au plus deux écrans.

```
┌ Tes réglages ─────────────────────────────────────────┐
│ Recherche d'emploi ● │ Recherche d'emploi               │
│ Actualités           │ ┌ Objectifs ORP ──────────────┐  │
│ Notifications        │ │ 10 candidatures · le 5      │  │
│ IA                   │ └─────────────────────────────┘  │
│ Profils d'essai      │ ┌ Sites suivis ───────────────┐  │
│ Connexion            │ │ jobup     lecteur intégré ● │  │
│ Agenda               │ │ Indeed    lecteur intégré ● │  │
│ Extension            │ │ …                           │  │
│                      │ └─────────────────────────────┘  │
└───────────────────────────────────────────────────────┘
```

- Rubriques regroupées pour éviter les pages d'une ligne : **Connexion** rejoint **Profils d'essai** sous « **Compte** » ; **Agenda** et **Extension** sous « **Outils** ». Six entrées : Recherche d'emploi, Actualités, Notifications, IA, Compte, Outils.
- Sur téléphone : la liste des rubriques d'abord, puis la rubrique choisie avec « ← Réglages » (comme aujourd'hui avec les lignes repliables).

## 3. Des lignes calmes, le détail dans le panneau

Même principe que les formations, la fiche d'offre et le Suivi :

- **Sources d'actualités** : une ligne par source, **nom**, une ligne courte (« articles · Suisse · français · marché de l'emploi »), et à droite un **interrupteur « suivie »**. Un clic sur la ligne ouvre le **panneau latéral** : région, langue, « marché de l'emploi », filtre, et **« Retirer cette source »** en bas.
- **Sites suivis** : nom, ligne courte (« lecteur intégré · jobup.ch · dernière alerte le 12 oct. »), interrupteur « suivi » ; le panneau donne le détail et « Retirer ce site ».
- « Retirer » quitte les lignes : il n'est plus qu'une fois, dans le panneau.

## 4. Les deux seuils dits clairement

- « **M'avertir d'une offre à partir de** 70 / 100 » (Notifications, docs/19).
- « **Chercher l'annonce chez l'employeur à partir de** 70 / 100 » (docs/20).

Chacun dans sa rubrique, avec sa phrase, au lieu de deux champs « / 100 » côte à côte.

## 5. Rien ne change ailleurs

Pas de changement de base ni d'API : la présentation seulement. Les réglages gardent leurs valeurs et leurs règles d'enregistrement ; les anciens liens `/reglages#actualites` mènent à la bonne rubrique.

## 6. Livraison

Une PR (**0.40.0**). Ordinateur et téléphone, captures avant / après.

## Points à valider

1. **Une rubrique à la fois**, six rubriques (Compte = Profils d'essai + Connexion, Outils = Agenda + Extension) (§2).
2. **Lignes calmes** pour les sources et les sites : interrupteur, détail et « Retirer » dans le panneau (§3).
3. **Les deux seuils** reformulés, chacun dans sa rubrique (§4).
4. **Une PR** (§6).

## Écarts avec la livraison

- **Sur ordinateur**, la rubrique choisie s'affiche seule ; la plus longue (Recherche d'emploi : chiffres de l'ORP et six sites) tient sur un écran et demi. **Sur téléphone**, les six lignes repliables restent, et `?rubrique=…` ouvre la bonne.
- **Compte** : « Profils d'essai » et « Connexion » en sous-titres. **Outils** : les cartes Agenda et Extension ont déjà leur titre, pas de sous-titre en plus.
- **Lignes calmes** : nom, ligne courte et interrupteur. Pour une veille, la ligne donne ses mots-clés (« veille « Kubernetes emploi » · Suisse · français »). Le panneau d'un site donne la lecture, les adresses d'envoi, les alertes reçues et, s'il y en a, les non reconnues ; les sites intégrés (jobup, Indeed) n'ont pas « Retirer ».
- **Seuils** : « Chercher l'annonce chez l'employeur à partir de » reste dans Recherche d'emploi, sur toute la largeur ; « M'avertir d'une offre à partir de » passe dans Notifications, avec son bouton Enregistrer.
- Le lien « Réglages des Actualités » de la page Actualités mène à `?rubrique=actualites` ; les anciens liens `#…` restent valables.
