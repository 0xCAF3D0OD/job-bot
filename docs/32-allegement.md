# 32 — Alléger la plateforme : aides, sections dépliables, pages compactes, Actualités (version 0.25.0)

> Statut : **validé** le 2026-10-15. livré : PR a (bulle, lignes dépliables, panneau latéral, préparation compacte).
> Retours d'usage du 2026-10-15 :
> - trop de textes d'explication, qui surchargent les pages (préparation, et partout ailleurs) ;
> - le style actuel des sections dépliables (« ▸ Contacts chez … ») ne plaît pas ;
> - la préparation manque de symétrie : des éléments bien plus longs que le reste ;
> - la bulle « Collecte lancée… » ne disparaît jamais ;
> - les Actualités : le rangement plaît, mais il y a trop d'informations.

## 1. Les textes d'aide

### 1.1 Le constat

Environ **80 phrases d'aide** sont écrites en permanence sous les éléments : 7 dans les Réglages, 6 sur Aujourd'hui, 6 dans les sources d'actualités, 5 dans le détail d'une offre, 3 dans la section Contacts… Utiles la première fois, elles deviennent du bruit ensuite.

### 1.2 La règle proposée

Un texte reste **écrit sur la page** seulement s'il dit **un état ou une action à faire** : une erreur, « Aucune lettre pour cette offre », « Sans réponse : relancer Marie ? ». Tout ce qui **explique** passe ailleurs :

| Ce que dit le texte | Où il va |
|---|---|
| Comment marche un élément (« recherches LinkedIn déjà remplies, ouvertes dans un nouvel onglet ») | derrière le petit **« ? »** à côté du titre de la section (composant déjà en place, docs/29) |
| Ce que reçoit l'IA et ce que ça coûte | une **pastille discrète dans le bouton** : « Rédiger un message · 0,002 $ » ; le détail (« jamais de nom… ») derrière le « ? » |
| Une règle générale (« une prise de contact ne compte pas pour l'ORP ») | dans **« Comment ça marche »** (page Aujourd'hui), plus sur chaque page |
| Ce qui se devine (« Postule avec le bouton en haut de la page, puis… ») | **retiré** |

- Le « ? » s'ouvre au clic, au toucher et au clavier, comme aujourd'hui ; c'est la **seule** manière d'expliquer, partout.
- Chaque page est passée en revue ; la liste des textes gardés, déplacés et retirés est jointe à la PR.

## 2. Remplacer les sections dépliables

Deux formes, selon la taille de ce qui se déplie.

### 2.1 Le contenu court : la ligne dépliable, comme les filtres

Le style des **filtres des offres** plaît : on le reprend partout (Mon parcours, Formulaire ORP du mois, légende du calendrier, réglages avancés…).

- Une **ligne** : le titre à gauche, un **résumé** à droite en gris (« 2 contacts », « 3 lignes à compléter »), puis une petite flèche **›**.
- Au clic, la flèche **tourne vers le bas** et le contenu **glisse** en s'ouvrant (animation courte, 0,2 s ; aucune si l'ordinateur demande moins d'animations).
- Contenu ouvert : le **trait vertical** des filtres à gauche, sans fond gris.
- Dans un même groupe, **une seule ligne ouverte à la fois**.

### 2.2 Le contenu long : le panneau latéral

Ce qui est long et secondaire (**Contacts**, **Entreprise : adresse et annonce chez l'employeur**, **Fiche pour le formulaire**) ne s'insère plus dans la page : il s'ouvre dans un **panneau qui glisse depuis la droite**, comme l'Assistant.

- Ouvert par un **lien dans la barre d'actions** (« Contacts · 2 », « Entreprise », « Fiche pour le formulaire »).
- La page dessous **ne bouge pas** : pas d'allongement, pas de décalage.
- Fermeture : ×, Échap ou clic à côté. Sur téléphone, le panneau prend tout l'écran.

## 3. Des pages compactes et symétriques

**Règle** : les colonnes d'une page ont **la même hauteur** ; rien ne dépasse le reste de beaucoup ; sur un écran d'ordinateur courant, l'essentiel tient sans défiler.

**Préparation** (2ᵉ photo) :

- La section Contacts quitte le haut de page pour le **panneau latéral** (§2.2) : les onglets « Lettre » et « CV » remontent juste sous la barre d'actions.
- Colonne de droite : la carte **« Rédiger la lettre »** seule ; la carte d'explication « Postule avec le bouton en haut… » est **retirée** (§1.2).
- La zone « Aucune lettre pour cette offre » prend **la hauteur de la carte de droite**, pas plus.

Les autres pages sont vérifiées avec la même règle (Aujourd'hui l'est déjà depuis la PR du 2026-10-14).

## 4. La bulle d'information

- Elle **disparaît seule** après **5 secondes** (8 s pour une erreur) ; le compte s'arrête tant que la souris est dessus.
- Un **×** pour la fermer tout de suite.
- La ligne de collecte d'Aujourd'hui (« Collecte il y a 2 h ») n'est pas touchée.

## 5. Actualités : moins d'informations, plus d'allure

### 5.1 Le constat

Neuf cartes de même taille avec, chacune, source, date, titre en gras et trois lignes de résumé : tout a le même poids, l'œil ne sait pas où se poser. En haut, sept réglages sur une ligne (Mon domaine / Tout, « ? », Pays, Langue, « Relevé il y a 20 h », « Relever maintenant »).

### 5.2 Proposé : une page « journal »

- **À la une** : l'article le plus récent de ton domaine, en **grand**, avec son image et **deux lignes** de résumé.
- **En dessous, une liste fine** : pour chaque article, **le titre seul**, et sur la même ligne, en petit gris, la source et la date (« SECO · 13 oct. »). Pas de résumé : il s'affiche **au survol** (ou au toucher) sous le titre, sinon un clic ouvre l'article.
- **Groupés par jour** (« Aujourd'hui », « Cette semaine », « Plus ancien »), comme les offres « Par jour ».
- **En haut** : « Mon domaine / Tout » seulement. Pays et langue passent derrière un bouton **« Filtrer »** (avec le nombre de filtres actifs) ; « Relevé il y a 20 h » et « Relever maintenant » vont en bas de page, en petit.
- Les **Vidéos** gardent leurs cartes avec vignette (l'image y est l'information).

## 6. Livraison en trois PR

| PR | Contenu |
|---|---|
| **0.25.0-a** | Bulle temporaire (§4), sections dépliables et panneau latéral (§2), préparation compacte (§3) |
| **0.25.0-b** | Textes d'aide : la règle appliquée à toutes les pages (§1) |
| **0.25.0-c** | Actualités en page « journal » (§5) |

Sans migration ni changement d'API.

## Points à valider

1. **Textes d'aide** : sur la page seulement les états et les actions ; les explications derrière le « ? », le coût dans le bouton (§1).
2. **Lignes dépliables** au style des filtres pour le contenu court (§2.1).
3. **Panneau latéral** pour Contacts, Entreprise et Fiche pour le formulaire (§2.2).
4. **Préparation compacte**, colonnes de même hauteur (§3).
5. **Bulle** qui disparaît après 5 s, avec × (§4).
6. **Actualités** : une à la une, puis une liste de titres groupés par jour, filtres derrière « Filtrer » (§5).
7. **Trois PR** (§6).

## Écarts avec la PR a

- **Retours à la validation** : le bouton « ? » est **toujours rond** (il ne se déforme plus dans une ligne étroite) ; **aucun libellé de bouton ou de lien ne passe à la ligne** (« Contacts · 2 » reste sur une ligne) ; les éléments d'une barre restent alignés.
- **Lignes dépliables** : Mes enseignements et Formulaire ORP du mois (Suivi, regroupés, une seule ouverte à la fois), Légende du calendrier, Plus d'options (formulaire ORP), Pour les formulaires en ligne (coordonnées), Alertes reçues, Tu as donné une autre adresse sur le site ?, Recherches mises de côté. Le contenu reste chargé quand la ligne est repliée (comme avant), il est seulement masqué.
- **« En savoir plus »** (textes d'explication repliés) n'est pas transformé ici : ces textes passent derrière le « ? » dans la PR b.
- **Panneau latéral** : **Contacts** (détail d'une offre, préparation et carte du Suivi), **Entreprise** (détail d'une offre, à côté de « Voir sur … ») et **Fiche pour le formulaire** (préparation). Le nombre de contacts s'affiche dans le lien (« Contacts · 2 »).
- **Contacts rangés en trois rubriques** : « Trouver quelqu'un » (liens en liste, ↗), « Premier message » (rôle et canal côte à côte, « Rédiger un message · 0,002 $ »), « Mes prises de contact ». Les trois phrases d'explication sont derrière le « ? » du panneau.
- **Préparation** : carte « Postule avec le bouton en haut… » retirée (« ← Retour aux offres » est déjà en haut) ; « Aucune lettre pour cette offre » prend la hauteur de la colonne de droite.
- **Bulle** : 5 s, 8 s pour une erreur (collecte non configurée, API injoignable), le compte s'arrête au survol ou au clavier, × pour fermer.
