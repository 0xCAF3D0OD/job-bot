# 36 — Téléphone : Candidatures et Profil (version 0.29.0)

> Statut : **validé** le 2026-10-15. livré.
> Suite du travail sur le téléphone (docs/33, 34). **Tout ce qui suit ne vaut que sur téléphone** (moins de 820 px) ; sur ordinateur, rien ne change.

## 1. Le constat (393 px)

| Où | Ce qui coince |
|---|---|
| **En-tête de Candidatures** (Offres, Suivi, Alertes) | la pastille « CANDIDATURES » et un grand titre sur deux lignes (« Tes candidatures et tes preuves ORP ») : près de 300 px avant le contenu. L'en-tête compact de docs/33 ne s'y applique pas (cette rubrique a son propre en-tête). |
| **Offres** | chaque carte fait 270 px (logo, titre, entreprise, note, date, extrait, lieu, site) : à peine trois offres par écran. « Filtres » ouvre un plein écran, alors qu'Actualités et Formations ont « Filtrer · N » en carte. |
| **Suivi** | avant le calendrier : le mois, le nombre, l'objectif, l'échéance ORP et « Ajouter une candidature » sur cinq lignes. |
| **Profil** | les trois onglets (« Ce que je cherche », « Mon parcours », « Mes coordonnées ») passent chacun sur **deux lignes**. |

## 2. En-tête compact partout

L'en-tête de Candidatures suit la règle de docs/33 §3.4 : **ni pastille ni sous-titre**, titre plus petit sur une ligne (« Les offres pour toi », « Ton suivi », « Tes alertes »). Les onglets Offres, Suivi et Alertes suffisent à se repérer.

## 3. Offres : des lignes compactes, « Filtrer » en carte

- **Une offre = une ligne** d'environ 90 px, comme les Actualités : le **titre** (deux lignes au plus), en dessous « **Entreprise · Lieu** », et à droite la **note** (ou « à noter ») avec la date courte dessous. Le logo de l'entreprise devient une petite pastille à gauche. Pas d'extrait : le détail s'ouvre en plein écran (docs/33).
- Les signaux « à vérifier » (docs/30) restent visibles par une petite pastille orange sur la ligne.
- **« Filtrer · N »** remplace « Filtres » : comme pour les Actualités et les Formations, une **carte sur toute la largeur** qui descend sous le bouton et **pousse la liste**, avec le même contenu qu'aujourd'hui (statut, tri, note, télétravail…) et, en bas, « Afficher N offres ».
- Environ **huit offres par écran** au lieu de trois.

## 4. Suivi : l'essentiel sur une ligne

- Au-dessus du calendrier, une seule ligne : **« ← Octobre 2026 → »** et, à droite, **« 2 · objectif 10 »** ; dessous, l'échéance ORP en petit (« remise avant le 5 novembre »).
- **« Ajouter une candidature »** devient un petit bouton **＋** rond à côté du mois (même action).
- Le calendrier, la légende et les cartes du jour ne changent pas.

## 5. Profil : des onglets sur une ligne

Sur téléphone, les onglets prennent un nom court : **« Recherche »**, **« Parcours »**, **« Coordonnées »**. Ils tiennent sur une ligne, sans défilement.

## 6. Hors périmètre

- **La lettre et le CV en cours d'édition** (préparation) n'ont pas pu être regardés sur téléphone : il faut une lettre rédigée par l'IA, qui n'est pas configurée sur l'instance de test. À revoir avec une vraie lettre.

## 7. Livraison

Une PR (**0.29.0**), sans migration ni changement d'API. Vérifiée à 393 et 1280 px.

## Points à valider

1. **En-tête de Candidatures compact** sur téléphone (§2).
2. **Offres en lignes compactes**, détail en plein écran, **« Filtrer · N » en carte** qui pousse la liste (§3).
3. **Suivi** : mois, nombre et objectif sur une ligne, **＋** pour ajouter (§4).
4. **Profil** : onglets au nom court sur une ligne (§5).
5. **Une PR**, téléphone seulement (§7).

## Écarts avec la livraison

- **Offres** : lignes de 77 à 106 px à 393 px (contre 270), soit environ huit offres par écran. La note, la date courte, et « À vérifier » ou « Arnaque possible » restent visibles ; mots-clés, résumé, extrait, lieu en bas, site et taux passent dans le détail.
- **« Filtrer · N »** : la carte reprend le panneau de filtres existant, sans la poignée ni le titre « Filtres » de l'ancien panneau du bas ; « Afficher N offres » la referme. Le libellé « Filtrer · N » vaut aussi entre 820 et 860 px, où le bouton existait déjà (« Filtres (N) »).
- **Suivi** : sur une ligne « ← Octobre 2026 → », le nombre (« 2 / 10 » quand l'objectif est saisi, sinon « 1 candidature(s) » en plus petit) et **＋** ; l'échéance ORP dessous. La barre de progression et « Objectif ORP à saisir dans les Réglages » ne s'affichent pas sur téléphone (Aujourd'hui le rappelle déjà).
- **Vérifié** à 393 px (Offres, carte des filtres, Suivi, Profil) et à 1280 px (ordinateur inchangé).
