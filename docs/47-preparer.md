# 47 — Préparer une candidature : un parcours en trois temps (version 0.39.0)

> Statut : **validé** le 2026-10-15, livré.
> Revue de la page « Préparer ma candidature » (`/candidatures/offres/:id/preparer`), dernière page du parcours pas encore reprise après docs/44 à 46. Captures du 2026-10-15 (« Cloud Architect », une lettre fictive de test).

## 1. Ce qui ne va pas

| # | Constat |
|---|---|
| 1 | **Une barre de cinq éléments sans ordre** : « Ouvrir l'annonce sur jobup », « Marquer comme envoyée », puis trois liens « Lettre (PDF) », « Contacts », « Fiche pour le formulaire ». On ne sait pas par quoi commencer. |
| 2 | **Deux fois le téléchargement** : « Lettre (PDF) » en haut, « Télécharger en PDF / en Word » à droite. |
| 3 | **Libellés coupés sur deux lignes** : « Télécharger / en PDF », « Télécharger / en Word » (contraire à la règle : jamais de bouton sur deux lignes). |
| 4 | **« Aucune modification »** est un bouton grisé : il n'a rien à faire là tant qu'on n'a rien modifié. |
| 5 | **Rien ne rappelle l'offre** pendant qu'on écrit : la note, les points forts et les manques sont restés sur la fiche de l'offre. |
| 6 | « ← Retour aux offres » flotte seul entre l'en-tête et la barre. |

## 2. La page proposée

Le parcours est toujours le même : **la lettre, le CV, puis postuler**. La page le dit.

```
┌ Cloud Architect                                         ┐
│ Jura Data SA · Fribourg · ← Offres                       │
│ ① Lettre ✓   ② CV   ③ Postuler                           │  ← onglets numérotés
├──────────────────────────────────┬──────────────────────┤
│                                  │ Pour cette offre     │
│   (la lettre, modifiable)        │ 88/100 · 2 points    │
│                                  │ forts · 1 manque     │
│                                  │──────────────────────│
│                                  │ Nouvelle version     │
│                                  │ Langue · consigne    │
│                                  │ [Nouvelle version]   │
│                                  │──────────────────────│
│                                  │ [PDF]  [Word]        │
│                                  │ Versions (2)         │
└──────────────────────────────────┴──────────────────────┘
```

- **En-tête** : titre, entreprise · lieu, et « ← Offres » sur la même ligne (le lien flottant disparaît).
- **Trois onglets numérotés** : ① Lettre, ② CV, ③ Postuler ; une coche quand la lettre ou le CV existe.
- **Colonne de droite** (Lettre et CV) :
  - **Pour cette offre** : la note, les points forts et les manques en résumé (repris de la fiche, docs/45), repliés à 3 lignes ;
  - **Nouvelle version** : comme aujourd'hui ;
  - **Télécharger** : « PDF » et « Word », deux boutons courts côte à côte ; « Enregistrer mes modifications » n'apparaît **que si** la lettre a été modifiée ;
  - **Versions** : comme aujourd'hui.
- **③ Postuler** réunit ce qui était dans la barre, dans l'ordre où on le fait :
  1. **« Postuler sur … ›»** (chez l'employeur si on le connaît) ;
  2. **Fiche pour le formulaire** : les champs à recopier, affichés directement ;
  3. **Contacts** chez l'entreprise ;
  4. **« J'ai postulé »** : marquer comme envoyée (le formulaire de candidature, comme aujourd'hui).
- La barre du haut et « Lettre (PDF) » disparaissent.

## 3. Téléphone

Les onglets numérotés restent en haut ; la colonne de droite passe sous la lettre. En bas, fixé : l'action de l'onglet (« Nouvelle version » sur ① et ②, « Postuler sur … » sur ③).

## 4. Rien ne change ailleurs

Pas de changement de base ni d'API : la présentation seulement. Les lettres, CV, versions et le formulaire « Marquer comme envoyée » gardent leur comportement.

## 5. Livraison

Une PR (**0.39.0**). Ordinateur et téléphone, captures avant / après.

## Points à valider

1. **Trois onglets numérotés** : Lettre, CV, Postuler ; la barre du haut disparaît (§2).
2. **Colonne de droite** : Pour cette offre (note, points forts, manques), Nouvelle version, Télécharger (PDF / Word sur une ligne), Versions ; « Enregistrer » seulement après modification (§2).
3. **Onglet Postuler** : Postuler sur …, Fiche pour le formulaire, Contacts, J'ai postulé (§2).
4. **Une PR** (§5).

## Écarts avec la livraison

- **③ Postuler** en deux colonnes, comme Lettre et CV : à gauche les étapes numérotées **1. Postuler**, **2. Fiche pour le formulaire**, **3. J'ai postulé** ; à droite, **Contacts chez …**, non numérotés (on peut s'en servir à tout moment, avant ou après avoir postulé). Une seule colonne laissait la moitié droite vide.
- **« Pour cette offre »** : la note, « N points forts · N manques », puis la liste repliée à 3 lignes avec « Tout voir » ; rien quand l'IA n'a pas encore résumé l'offre.
- **Télécharger** : « PDF » et « Word », deux boutons courts côte à côte ; le titre « Cette version » devient « Télécharger ». Le bouton « Enregistrer » ne paraît qu'après une modification, avec la phrase qui l'explique.
- **Téléphone** : l'action fixée en bas suit l'onglet : « Nouvelle version » (ou « Rédiger la lettre »), « Préparer le CV », « Postuler sur … ». Vérifié à 390 px, sans débordement.
- Une candidature déjà envoyée garde son bandeau « Candidature envoyée · Revenir aux offres · Voir le suivi ».
