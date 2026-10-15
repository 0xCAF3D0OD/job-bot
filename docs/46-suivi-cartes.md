# 46 — Suivi : une carte, une prochaine étape, le reste à part (version 0.38.0)

> Statut : **validé** le 2026-10-15, livré.
> Même constat que pour les formations (docs/44) et la fiche d'offre (docs/45), sur les cartes de la colonne « À relancer » du Suivi (et celles d'un jour choisi dans le calendrier). Capture du 2026-10-15 (septembre 2026, données de test).

## 1. Ce qui ne va pas

| # | Constat |
|---|---|
| 1 | **Une carte empile jusqu'à huit éléments** : nom, poste · date, menu « ⋯ », champ « Statut », phrase de relance avec son lien, cadre « Pour l'ORP, il manque… », rangée de liens (Lettre, CV, Lien de candidature, Copier pour Job-Room, Contacts), parfois les liens d'entretien et le tableau Job-Room déplié **dans la carte**. |
| 2 | **Trois couleurs d'alerte dans la même carte** : la relance en orange, le manque ORP dans un cadre, la relance de contact en dessous. On ne sait pas laquelle traiter en premier. |
| 3 | **Le champ « Statut »** est un menu déroulant posé dans chaque carte : on change un statut par accident en faisant défiler la colonne. |
| 4 | La colonne est **coupée en bas** (fondu) dès la troisième carte : on ne voit que deux candidatures sur ordinateur. |

## 2. La carte proposée

```
┌──────────────────────────────────────────┐
│ Helvetia Tech SA                         │
│ DevOps Engineer · 6 sept.                │
│ ● En attente                             │
│──────────────────────────────────────────│
│ Sans réponse depuis 10 jours  Relancer › │
└──────────────────────────────────────────┘
```

- En haut : l'entreprise (avec ORP / Spontanée si c'est le cas), le poste · la date, et le statut en **pastille** (même couleur qu'au calendrier), plus en menu déroulant.
- En bas, **une seule prochaine étape**, la plus urgente, toujours au même endroit, et un lien qui la fait :
  1. entretien à venir : « Entretien jeudi 22 à 14 h » · **Préparer ›**
  2. entretien passé sans retour : « Entretien passé » · **Faire le point ›**
  3. relance due (10 jours) : « Sans réponse depuis 10 jours » · **Relancer ›**
  4. relancée sans réponse (14 jours) : « Pas de réponse depuis la relance » · **Sans réponse ›**
  5. il manque quelque chose pour l'ORP : « Pour l'ORP : adresse manquante » · **Compléter ›**
  6. sinon : **Gérer ›** seul.
- Toute la carte (ou « Gérer ») ouvre le **panneau latéral**. Le « ⋯ » quitte la carte.

## 3. Le panneau d'une candidature

Le panneau latéral déjà utilisé (Contacts, Relancer, Formations), sur ordinateur comme sur téléphone. En tête : entreprise, poste, date d'envoi, et « ⋯ » (Modifier, Supprimer, Demander à l'assistant). Puis des **sections titrées**, chacune seulement si elle a du contenu :

| Section | Contenu |
|---|---|
| **Statut** | le choix du statut (les mêmes valeurs qu'aujourd'hui), la relance due et son bouton |
| **Entretiens** | Préparer l'entretien, Ajouter à mon agenda, Faire le point, Voir le retour |
| **Pour l'ORP** | ce qui manque et « Compléter », puis les champs Job-Room avec « Copier » (déplié directement, plus de bouton « Copier pour Job-Room ») ; la remarque télétravail à l'étranger |
| **Documents** | Lettre, CV, Lien de candidature |
| **Contacts** | les contacts de la candidature (le panneau Contacts actuel, dans la section), et « relancer X ? » quand c'est dû |

## 4. La colonne

Avec des cartes de quatre lignes, la colonne « À relancer » montre **quatre à cinq candidatures** sans défiler. Le fondu en bas reste quand il y en a plus.

## 5. Rien ne change ailleurs

Pas de changement de base ni d'API : la présentation seulement. La vue **Liste** garde son tableau ; le nom de l'entreprise y ouvre le même panneau (au lieu d'aller chercher la carte dans le calendrier).

## 6. Livraison

Une PR (**0.38.0**). Ordinateur et téléphone, captures avant / après.

## Points à valider

1. **Carte calme** : pastille de statut, une seule prochaine étape en bas, dans l'ordre du §2 (§2).
2. **Panneau** en cinq sections : Statut, Entretiens, Pour l'ORP (Job-Room déplié), Documents, Contacts (§3).
3. **Liste** : le nom de l'entreprise ouvre le même panneau (§5).
4. **Une PR** (§6).

## Écarts avec la livraison

- **Carte** : le statut est à droite du nom de l'entreprise (point de couleur du calendrier + libellé), pas sur une ligne à lui : la carte fait trois lignes, et la colonne en montre quatre entières sur ordinateur (deux avant), la cinquième en fondu.
- **Prochaine étape** : « Relancer › » ouvre directement le panneau de relance ; « Sans réponse › » change le statut ; « Compléter › » ouvre le formulaire ; « Préparer › » et « Faire le point › » ouvrent les fiches d'entretien. Le haut de la carte ouvre le panneau.
- **Panneau** : « Statut » est toujours là ; les autres sections seulement si elles ont du contenu. Les formulaires (Modifier, entretien, préparation) **prennent la place** du panneau au lieu de s'ouvrir dessous.
- **Liste** : le nom de l'entreprise est un lien qui ouvre le panneau ; le reste du tableau ne change pas.
