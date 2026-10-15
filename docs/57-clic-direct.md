# 57 — Cliquer sur l'élément, sans « › » ni « Continuer » (version 0.45.2)

> Statut : **validé** le 2026-10-15, livré.
> Retour du 2026-10-15 : « tu mets souvent des “›” pour accéder à un contenu, ou alors “Continuer”, ce qui devrait plutôt être d'avoir un survol sur ce qu'on peut cliquer, et y accéder en cliquant directement sur l'élément ».

## 1. La règle

- **Ce qui ouvre un contenu est cliquable en entier** (ligne, carte, tuile, titre de carte), avec un **survol** qui le montre : fond légèrement teinté pour une ligne, bordure violette pour une carte (comme les tuiles d'Aujourd'hui), et le curseur main. Au clavier, le même état au focus.
- **Plus de « › »** en bout de ligne ou de lien, ni de « Continuer › » / « Ouvrir › » quand l'élément suffit.
- **Les vraies actions restent des boutons** (Postuler, Relancer, Copier, Marquer comme envoyée…), avec leur verbe, sans flèche.
- Restent : le chemin écrit dans un texte (« Candidatures › Suivi », ce n'est pas un lien) et la petite flèche qui **tourne** sur les lignes repliables (« Comment ça marche ») : elle dit ouvert / fermé, elle n'ouvre pas une autre page.

## 2. Ce qui change, page par page

| Page | Aujourd'hui | Après |
|---|---|---|
| **Aujourd'hui** › À examiner en priorité | « › » au bout de chaque offre ; « Continuer › » dans Commencées | **la ligne entière** ouvre l'offre, ou sa préparation (Commencées) ; survol de la ligne |
| Aujourd'hui › Objectif ORP | « octobre 2026 › » en haut à droite | **la carte** ouvre le Suivi du mois |
| Aujourd'hui › Progresser, Actualités | « Formations › », « Actualités › » en haut à droite | **le titre de la carte** est le lien ; chaque formation ou article reste cliquable |
| Aujourd'hui, au-dessus des tuiles | « Ouvrir les candidatures › » | retiré : les tuiles y mènent déjà |
| **Offres** (filtres) | « › » au bout de chaque ligne de filtre | retiré (la ligne est déjà cliquable) |
| **Fiche d'offre** | « Contacts · 2 › », « Voir sur jobup › », lien « Postuler › » | « Contacts · 2 » (ouvre le panneau), « Voir sur jobup », « Postuler » sans flèche |
| **Suivi** › carte | « Relancer › », « Préparer › »… | le verbe seul (c'est une action) ; la carte s'ouvre toujours d'un clic |
| Suivi › panneau | « Lien de candidature › » | sans flèche |
| Suivi, Formulaire ORP | « Compléter 2 lignes › » | sans flèche |
| **Profil › Parcours** | « › » au bas de chaque bloc ; « Ouvrir le fichier › » | retiré (le bloc est déjà cliquable) ; « Ouvrir le fichier » |
| **Alertes** (assistant de création) | « Continuer › », « Ouvrir jobup › », « C'est fait, site suivant › » | les mêmes boutons, sans flèche (ce sont des étapes) |
| **Préparer** | « Revenir aux offres › », lien de l'annonce « › » | sans flèche |
| **Formations** | « Page officielle › », « Gérer › » | sans flèche |
| Candidature spontanée | bouton « Continuer » (étape suivante du formulaire) | garde son nom : c'est un bouton d'étape, pas un accès à un contenu |

Les liens vers un autre site (annonce, page officielle, fichier) s'ouvrent comme aujourd'hui dans un nouvel onglet.

## 3. Rien ne change ailleurs

Pas d'API ni de base. Le pictogramme `chevron` reste seulement pour la flèche qui tourne des lignes repliables. Mobile : mêmes règles (pas de survol au toucher, l'élément reste cliquable en entier).

## 4. Livraison

Une PR (**0.45.2**), captures avant / après d'Aujourd'hui, de la fiche d'offre, du Suivi et du Parcours.

## Points à valider

1. **La règle** : l'élément cliquable en entier avec un survol, plus de « › » ni de « Continuer › » pour ouvrir un contenu ; les actions gardent leur verbe (§1).
2. **Restent** : les chemins écrits dans les textes et la flèche qui tourne des lignes repliables (§1).
3. **Le tableau** des changements (§2).
4. **Une PR** (§4).

## Écarts avec la livraison

- **Aujourd'hui** : dans le tableau, toute la ligne ouvre l'offre (ou sa préparation dans « Commencées ») ; le titre reste un vrai lien pour le clavier, et la ligne se teinte au survol ou au focus. La colonne vide du « › » disparaît. La jauge entière ouvre le Suivi **du mois affiché** (`?mois=`), le mois reste écrit en haut à droite, sans flèche. « Progresser » et « Comprendre le marché » : le titre (avec sa bulle) est le lien, en violet au survol ; chaque formation en cours mène aux Formations, la formation suggérée et les articles s'ouvrent sur leur titre (le « Voir » à part disparaît).
- **Filtres des Offres** : la flèche des lignes qui se déplient **reste**, car elle tourne à l'ouverture (même règle que les lignes repliables, §1) ; elle disparaît des lignes qui ne se déplient pas.
- **Suivi** : « Relancer », « Sans réponse », « Préparer »… sans flèche, ce sont des actions ; la carte s'ouvre toujours d'un clic.
- **« Collecter »** (en-tête) : c'est une action, sa flèche disparaît aussi. Le pictogramme `chevron` n'est plus utilisé (gardé dans `AppIcon`).
- **Vérifié** : captures avant / après d'Aujourd'hui, de la fiche d'offre (seule l'animation d'ouverture diffère), du Suivi et du Parcours ; un test pour le clic sur la ligne et la jauge.
