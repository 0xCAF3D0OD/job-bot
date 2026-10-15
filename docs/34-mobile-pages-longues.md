# 34 — Téléphone : raccourcir les pages longues (version 0.27.0)

> Statut : **validé** le 2026-10-15. livré.
> Suite du travail sur le téléphone (docs/33). **Tout ce qui suit ne vaut que sur téléphone** (moins de 820 px de large) ; sur ordinateur, rien ne change.

## 1. Le constat (iPhone, 393 px)

| Page | Hauteur | Ce qui la rallonge |
|---|---|---|
| **Formations** | 7 600 px, soit neuf écrans | 24 cartes de 280 px (titre, organisme, faits, description, avertissement ORP, trois boutons de statut) ; au-dessus, l'encadré « Formation et chômage » (170 px) et quatre filtres sur deux lignes |
| **Réglages** | 5 200 px, six écrans | « Recherche d'emploi » (1 850 px : critères, coordonnées, objectif ORP, seuils) et « Actualités » (1 500 px : mots-clés, sources, catalogue) dépliés en entier ; le sommaire en haut prend 80 px |
| **Aujourd'hui** | 2 800 px, plus de trois écrans | « Comment ça marche » et « Pour bien démarrer » dépliés en entier avant l'essentiel du jour |

Les autres pages tiennent en un ou deux écrans.

## 2. Formations : une liste, la fiche en plein écran

- **Liste fine**, comme les Actualités (docs/32 §5) : pour chaque formation, le **titre** et, en dessous en petit, une ligne de faits (« Certification · AWS · payant · en ligne »). Si tu as choisi un statut, une pastille l'indique à droite (« En cours »).
- Un appui ouvre la **fiche en plein écran**, dans le panneau latéral (docs/32 §2.2) : description, avertissement « financement avec l'accord de l'ORP », lien vers l'organisme, et les trois statuts (Intéressé, En cours, Terminé). Les champs de « Mes formations » (dates, note) y sont aussi.
- **En haut** : « Mon domaine / Tout » et **« Filtrer · N »** (type, prix, langue), comme les Actualités.
- **L'encadré « Formation et chômage »** devient une **ligne dépliable** (docs/32 §2.1), fermée par défaut : « Formation et chômage · accord de l'ORP ». Les deux liens utiles restent dedans.
- Environ 70 px par formation au lieu de 280 : la page passe de neuf écrans à **deux ou trois**.

## 3. Réglages : une ligne par section

- Le **sommaire** disparaît sur téléphone : chaque section devient une **ligne dépliable**, avec un résumé à droite, et une seule section est ouverte à la fois.

| Section | Résumé à droite (exemples) |
|---|---|
| Recherche d'emploi | « Lausanne, Genève · 80-100 % » |
| Actualités | « 6 mots-clés · 9 sources » |
| Notifications | « actives » ou « non configurées » |
| IA | « 3,20 $ / 10 $ ce mois » |
| Profils d'essai | « 2 profils » |
| Connexion | « kevin » |
| Extension du navigateur | « 1 jeton » |

- Un lien vers une section (par exemple « Réglages › Actualités » depuis une autre page) **ouvre directement** la bonne ligne.
- Fermée, la page tient en **un écran** ; une section ouverte ne fait défiler que son contenu.

## 4. Aujourd'hui : l'essentiel d'abord

- **« Comment ça marche »** et **« Pour bien démarrer »** deviennent deux **lignes dépliables fermées par défaut**, avec leur avancement à droite (« 3 / 5 », « 2 / 6 ») ; elles passent **sous** le point du jour (candidatures, à relancer, actualités).
- « Masquer » reste dans chaque bloc ouvert.
- Le reste de la page ne change pas.

## 5. Livraison

Une seule PR (**0.27.0**), sans migration ni changement d'API. Vérifiée à 375, 393 et 768 px, puis à 1280 px pour s'assurer que l'ordinateur n'a pas bougé.

## Points à valider

1. **Formations** en liste fine, fiche en plein écran, filtres derrière « Filtrer », encadré ORP replié (§2).
2. **Réglages** : une ligne dépliable par section, sans sommaire, une ouverte à la fois (§3).
3. **Aujourd'hui** : « Comment ça marche » et « Pour bien démarrer » repliés, sous l'essentiel du jour (§4).
4. **Téléphone seulement**, ordinateur inchangé, **une PR** (§5).

## Écarts avec la livraison

- **Mesures à 393 px** : Formations de 7 600 à **2 260 px** (24 lignes de 68 px) ; Réglages de 5 200 px à **un écran** toutes lignes fermées ; Aujourd'hui de 2 800 à **1 670 px**.
- **Formations** : la fiche en plein écran reprend exactement le contenu de la carte d'ordinateur (même composant) : faits, description, préparation conseillée, avertissement ORP, « Garder / Écarter » pour une suggestion de l'IA, statuts, progression et date de fin. La ligne montre le type, l'organisme et le prix ; une pastille indique le statut choisi ou « à vérifier ». « Chercher d'autres formations · 0,02 à 0,05 $ » reste visible sous les filtres.
- **Réglages** : résumés réellement disponibles sur la page : « objectif 10 / mois · alerte dès 70 », « mots-clés et sources », « actives / non configurées », « plafond 10 CHF / mois », « profils fictifs », le nom du compte ou « désactivée », « jetons ». Les exemples du cadrage (communes, dépenses du mois, nombre de sources) demanderaient des appels en plus : pas fait.
- **Aujourd'hui** : « Comment ça marche » et « Pour bien démarrer » sont en bas de page, repliés, une seule ouverte à la fois ; « Masquer » reste dedans.
- **Ordinateur** : vérifié inchangé à 1280 px (cartes et encadré des Formations, sommaire et titres des Réglages, blocs d'Aujourd'hui).
- **Largeurs vérifiées** : 393 px (téléphone) et 1280 px (ordinateur) seulement ; 375 et 768 px, prévus au §5, n'ont pas été passés en revue.
