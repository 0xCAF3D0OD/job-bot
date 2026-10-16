# 61 — Une carte qui vient devant, une transition pour les pages qui chargent, des images pour les blocs trop larges (version 0.48.0)

> Statut : **validé** le 2026-10-16, livré pour essai.
> Retour du 2026-10-16 sur 0.47.2, capture de Préparer › Postuler à l'appui :
> - « la lettre envoyée ne va pas du tout, trop grand ; ça devrait être une animation quand on a envoyé la candidature : une carte qui vient devant, de manière souple » ;
> - « des animations pour tout composant qui prend toute la largeur de l'écran alors qu'il n'en a pas besoin », comme dans Profil (« des éléments trop longs pour la largeur, compensés par l'image, qui doit avoir du sens ») ; par exemple « À recopier sur le site de l'employeur », beaucoup trop long ;
> - « ou une animation avant d'accéder à la page : en cliquant sur Actualités, l'écran est grisé avec l'animation des Actualités au centre » ; pas pour tout, « pour ce qui doit charger des données ».
>
> Sur ordinateur ; le téléphone est indiqué à part.

## 1. Les réussites : une carte qui vient devant

La grande image posée dans la page (candidature envoyée, preuves remises) disparaît. À la place, au moment de l'action :

```
        (page légèrement grisée derrière)
              ✈  ← l'avion en papier s'envole et se pose sur le bord de la carte
        ┌──────────────────────────────────┐
        │ Candidature envoyée               │
        │ chez Sarine IT SA                 │
        │ Comptée pour l'ORP d'octobre : 7/10│
        │                         [ Fermer ]│
        └──────────────────────────────────┘
```

- La carte **monte et grandit doucement** jusqu'au centre (250 ms, avec un léger rebond), la page derrière se grise.
- L'illustration n'est **pas dans la carte** : elle est posée **au-dessus**, à cheval sur son bord (160 px), et joue son animation une fois.
- Elle se ferme d'elle-même après **4 secondes**, ou avec « Fermer », Échap, ou un clic à côté ; elle redescend en s'effaçant.
- Même carte pour **preuves remises** (la coche, « Prochaine remise avant le 5 novembre »).
- **Engagement** garde sa grande fête par-dessus la page (0.47.2).
- Téléphone : la même carte, en bas de l'écran.

## 2. Les pages qui chargent : une transition au centre

Quand on ouvre une page qui va chercher des données, et qu'elles ne sont pas encore là :

- la page **se grise** (voile clair ou sombre selon le thème) ;
- **l'illustration de la page** apparaît au centre (220 px), avec son nom dessous, et joue son animation ;
- dès que les données sont là, le voile et l'image s'effacent (250 ms) et la page apparaît.

| Page | Illustration |
|---|---|
| Aujourd'hui | morning-plans (le café et la liste du jour) |
| Candidatures › Offres | mobile-inbox |
| Candidatures › Suivi | date-picker |
| Candidatures › Bilan | stepping-up |
| Candidatures › Alertes | mailbox |
| Actualités | newsfeed |
| Formations | certification |

- **Seulement à l'arrivée sur la page** (clic dans le menu, lien), pas en changeant un filtre, un mois ou un onglet sur la même page.
- **Pas d'attente imposée au rapide** : si les données arrivent en moins de 0,15 s, rien ne s'affiche ; sinon la transition reste **au moins 0,5 s**, pour ne pas clignoter.
- Les blocs gris à la forme de la page restent dessous : quand le voile s'efface, rien ne saute.
- Profil, Réglages, Préparer, Diagnostic : pas de transition (peu de données, ou déjà un formulaire).
- Téléphone : la même transition, image de 160 px.
- « Réduire les animations » : le voile et l'image fixe, sans mouvement.

## 3. Les blocs trop larges : une image à côté

Comme Profil › Coordonnées : le bloc garde une largeur de lecture (40 rem environ) et l'image, qui dit à quoi sert le bloc, occupe le reste.

| Endroit | Ce qui est trop large aujourd'hui | Image |
|---|---|---|
| **Préparer › Postuler › 2. À recopier** | le tableau Prénom / Nom / … / Copier sur toute la largeur | guidelines (une fiche à remplir, cochée) |
| **Réglages › Recherche d'emploi** | objectif, date limite, seuil, sur toute la largeur | stepping-up |
| **Réglages › Actualités** | « Mon domaine » et les sources | newsfeed |
| **Réglages › Notifications** | un seul champ | lock-screen-notifications |
| **Réglages › IA** | un seul champ (plafond) | artificial-intelligence |
| **Réglages › Compte** | profils d'essai, connexion | security-on |
| **Réglages › Outils** | agenda, extension | online-connection |

- Dans Préparer, l'image est **à droite du tableau** (la colonne des contacts reste plus à droite).
- Dans les Réglages, la liste des rubriques est déjà à gauche : l'image se met **à droite** du formulaire, et reste visible quand on fait défiler.
- Les pages déjà denses (Offres, Suivi, Bilan, Formations, Actualités, Diagnostic) ne changent pas.
- Téléphone : pas d'image, rien ne change.

## 4. Les illustrations

Quatre de plus : morning-plans, guidelines, artificial-intelligence, security-on (newsfeed et certification sont déjà dans le dépôt). morning-plans et guidelines sont déjà animées dans `animees/` ; **artificial-intelligence** et **security-on** sont animées selon `CONSIGNES.md`. Toutes jouées une fois, couleurs du thème.

## 5. Livraison

Une PR (**0.48.0**) : la carte des réussites (§1), la transition des pages (§2), les images des blocs larges (§3). Une courte vidéo de la carte et de la transition, captures des Réglages et de Préparer, clair et sombre.

## Points à valider

1. **La carte qui vient devant** pour « envoyée » et « preuves remises », l'image posée au-dessus de la carte, fermeture seule après 4 s (§1).
2. **La transition des pages qui chargent** : voile gris, illustration de la page au centre ; rien sous 0,15 s, au moins 0,5 s sinon ; seulement à l'arrivée sur la page (§2, et la liste des pages).
3. **Les blocs trop larges** : Préparer › À recopier, et les six rubriques des Réglages, avec leur image (§3).
4. **Une PR** (§5).

## Écarts avec la livraison

- **Carte des réussites** (`SuccessCard`) : la carte monte en grandissant avec un léger rebond (420 ms), la page derrière grisée ; l'illustration (170 px) est posée **au-dessus**, son bas à peine sur le bord de la carte. « Candidature envoyée chez … » puis « Comptée pour l'ORP d'octobre : 7 sur 10 » ; « Preuves d'octobre remises » puis la prochaine échéance. Elle redescend en s'effaçant après 4 s, ou avec Fermer, Échap, un clic à côté. Sur téléphone, en bas de l'écran.
- **Transition des pages** : déclenchée quand le nom de la page change (menu, liens, onglets de Candidatures), pas sur un filtre, un mois ou un onglet d'Actualités. Chaque page dit quand ses données sont là ; au-delà de 8 s, le voile s'efface de lui-même. Image de 240 px (160 sur téléphone) et le nom de la page dessous, sur un voile flou.
- **Blocs trop larges** : « À recopier » garde 40 rem, l'image (guidelines, 280 px) à droite et qui reste visible en faisant défiler ; idem pour les six rubriques des Réglages, sous leur titre. Entre 820 et 1100 px, l'image passe à 220 px.
- **Illustrations** : 4 de plus (morning-plans, guidelines, artificial-intelligence et security-on, ces deux dernières animées pour l'occasion, « OK » avec `verifier.py`), 20 en tout.
- **Correctif** : une illustration pouvait rester vide quand son dessin arrivait avant son emplacement (visible sur le voile) ; le composant attend maintenant les deux.
- **Vérifié** dans le navigateur : Réglages › IA et Recherche, Préparer › À recopier, la carte « envoyée » déclenchée pour de vrai, la transition d'Actualités et de Formations avec un serveur ralenti.
