# 14 — Page Offres : mise en page, tri des candidatures, logos (version 0.7.4)

> Statut : **validé** le 2026-10-05. livré : PR a (mise en page, pastilles, tri), PR b (logos).
> Retours d'usage du 2026-10-05.

## 1. Mise en page de la page Offres

**Constat** : la colonne de droite affiche « Choisis une offre pour voir son détail » tant qu'aucune offre n'est ouverte ; la place est perdue.

**Proposition** :

- **Sans offre ouverte** : filtres à gauche, liste des offres **centrée** dans l'espace restant, plus de colonne de droite.
- **À l'ouverture d'une offre** : la liste glisse vers la gauche et se rétrécit, le **détail entre par la droite** (glissement et fondu, environ 250 ms). À la fermeture, le mouvement inverse.
- Les personnes qui demandent moins d'animations dans leur système (réglage « réduire les animations ») ont un changement immédiat, sans glissement.
- Sur téléphone : inchangé (le détail remplace la liste).

## 2. Pastilles de statut de même taille

« Candidature envoyée » est plus étroite que « En préparation » parce que les deux pastilles n'ont pas le même style. Elles auront la même hauteur, le même espacement intérieur et la même police ; seule la couleur change (envoyée en vert, en préparation en violet, plus tard en gris, expirée en orange).

## 3. Candidatures en cours, de la plus récente à la plus ancienne

Dans l'onglet **En cours** de la page Offres, un tri **« Dernière action »** devient le tri par défaut :
- une candidature envoyée compte à sa **date d'envoi** ;
- une offre en préparation compte à la date de la **dernière lettre ou du dernier CV** rédigé ou modifié (à défaut, la date où elle est passée « en préparation ») ;
- la plus récente en haut.

Les autres tris (note, récentes, populaires) restent disponibles. La page Candidatures garde son ordre actuel (date d'envoi, la plus récente d'abord).

## 4. Logo de l'entreprise à la place de la lettre

**Sources**, dans l'ordre :

1. **L'annonce jobup** : la page de l'offre donne le logo de l'entreprise (par exemple `media.jobup.ch/…jpg`). Il est relevé pendant la lecture des pages, déjà en place, sans requête supplémentaire.
2. **Les e-mails LinkedIn et jobs.ch**, qui contiennent souvent le logo de chaque offre : l'IA de lecture des alertes relève l'image associée à l'offre.
3. **Le site de l'entreprise**, quand il est connu (annonce jobup, recherche d'adresse sur Internet) : son icône officielle (celle des onglets du navigateur).
4. À défaut : la **lettre** actuelle.

**Confidentialité et rapidité** : le logo est **téléchargé une fois par le serveur** et gardé dans le stockage local (`data/logos/`), puis servi par la plateforme. Ton navigateur n'appelle donc pas de site tiers, qui pourrait suivre ce que tu consultes. Une seule image par entreprise, 200 Ko au plus, formats image uniquement (PNG, JPEG, WebP, SVG nettoyé).

## 5. Base (migration 0021)

```
companies  + logo_key?, logo_source? (page|email|site), logo_checked_at?
offers     + logo_url?   -- adresse d'origine relevée (page ou e-mail), avant téléchargement
```

## 6. Livraison

| PR | Contenu |
|---|---|
| **0.7.4-a** | Mise en page avec transition, pastilles, tri « Dernière action » |
| **0.7.4-b** | Logos des entreprises |

## Points à valider

1. **Liste centrée, détail qui entre par la droite** avec une transition douce (§1).
2. **Pastilles de statut identiques**, seule la couleur change (§2).
3. **Tri « Dernière action »** par défaut dans l'onglet En cours (§3).
4. **Logos** : annonce jobup, e-mails d'alerte, icône du site, sinon la lettre ; **téléchargés et servis par la plateforme**, pas chargés depuis des sites tiers (§4).
5. **Deux PR** (§6).

## Écarts avec la PR a

- **Écrans moyens** (moins de 1200 px de large) : le détail s'ouvre toujours par-dessus la liste, désormais avec un glissement depuis la droite.
- **Tri « Dernière action »** : proposé seulement dans l'onglet En cours. En quittant l'onglet, le tri revient à « Récentes ». La date de passage « en préparation » n'est pas enregistrée : sans lettre ni CV, l'offre compte à sa date d'arrivée.
- **Candidatures du même jour** : départagées par l'heure d'enregistrement.

## Écarts avec la PR b

- **Base** : une table `company_logos` (un logo par entreprise, nom normalisé) au lieu de colonnes dans `companies` ; `offers` reçoit `logo_url` et `company_website` (site lu sur l'annonce jobup) ; migration **0021**.
- **E-mails d'alerte** : les images de l'e-mail sont numérotées comme les liens ; l'IA indique le numéro du logo de chaque offre (consignes `alert-v2`), elle ne peut pas inventer d'adresse.
- **Icône du site** : la plus grande icône déclarée par la page d'accueil (souvent l'icône Apple, 180 px), sinon `/favicon.ico`.
- **Rythme** : après la recherche d'adresse (tâche `enrich`), 25 entreprises au plus par passage, une requête toutes les 2 secondes ; une seule tentative par entreprise pendant 30 jours.
- **Garde-fous** : https seulement, aucune adresse privée ou locale (vérifiée après résolution DNS, à chaque redirection), 200 Ko au plus, type d'image vérifié sur le contenu, SVG refusé s'il contient script, gestionnaire d'événement ou lien externe ; servi avec une politique de sécurité qui interdit tout chargement.
- **Essai réel** : logo jobup de Moser Vernet (JPEG) et icône du site d'Infomaniak, affichés sur les cartes.
