# 91 — La capsule qui se déroule (version 0.70.4)

> Statut : **validé** le 2026-10-19.
> Origine : ta demande du 2026-10-19, « que le menu ait la logique de déroulement du menu de Sphere, et le même style pour les menus déroulants principaux », puis la maquette animée du même jour, corrigée : « juste une ligne discrète qui sépare chaque composant ».

## Le principe, pris à Sphere

- **La capsule devient le menu.** Rien ne surgit à côté : le cadre de la capsule s'agrandit vers le bas, et le menu apparaît à l'intérieur. La rangée du haut (cloche, initiale) ne bouge pas.
- **Des zones, pas des boutons.**
  - Dans la capsule, la cloche, l'initiale et ☰ n'ont ni cadre ni fond.
  - Des **filets verticaux fins** les séparent.
  - Au survol, seule la couleur change, du gris au noir.
- **Un déroulé, pas un clignement** : la hauteur s'agrandit, puis le contenu apparaît en fondu.

## Ce qui change

### 1. La capsule (ordinateur)

- **L'aspect** :
  - un cadre de 2,5 rem de haut, une bordure fine, des coins de 10 px (plus une pilule, pour se dérouler proprement) ;
  - les zones séparées par des filets sur toute leur hauteur, avec 0,5 rem de marge en haut et en bas.
- **Avec l'initiale**, la capsule s'élargit à 15 rem et se déroule. Elle montre le menu du compte, sous un filet horizontal :
  - l'identifiant ;
  - Profil, Réglages, Données personnelles, Diagnostic ;
  - Collecter maintenant ;
  - puis, après un filet, Se déconnecter.

  Le ▾ se retourne.
- **Avec la cloche**, la capsule s'élargit à 24 rem et montre les alertes. C'est le panneau d'aujourd'hui, à l'intérieur de la capsule.
- **Une seule chose ouverte à la fois** : cliquer sur l'autre zone change le contenu sans refermer la capsule.
- **Elle se ferme** par un nouveau clic sur la zone, Échap, un clic ailleurs ou le choix d'une page. Le focus revient alors à la zone.

### 2. Sur téléphone (sous 820 px)

- **La capsule prend toute la largeur**, sous la marge. Elle contient le logo, puis la cloche, l'initiale et ☰, chacun séparé par un filet.
- **☰ devient ✕** et déroule les trois pages en grand, dans la capsule. Le panneau latéral actuel disparaît.
- **L'initiale** déroule le menu du compte dans la capsule, de la même façon.
- **La cloche garde son comportement** : sa carte s'ouvre sous la barre et pousse la page (retour du 2026-10-15).

### 3. Les menus « ⋯ » (14 écrans)

Ils sont trop petits pour se dérouler depuis une capsule. Ils prennent seulement **le même style** :
- la même bordure fine ;
- des coins de 10 px ;
- les mêmes lignes (taille, survol en fond léger) ;
- Supprimer en rouge après un filet, comme aujourd'hui ;
- presque plus d'ombre ;
- un **déroulé court** (hauteur et fondu) depuis « ⋯ ».

Leur comportement (clavier, Échap, une action visible) ne change pas.

### 4. Ce qui ne change pas

- Les listes de choix des formulaires restent celles du navigateur : clavier et téléphone.
- Les panneaux latéraux (fiche d'offre, candidature…) ne sont pas des menus.

## Le mouvement (exception écrite dans `docs/interface.md`)

| | Hauteur et largeur | Contenu |
|---|---|---|
| La capsule | 350 ms, courbe `cubic-bezier(0.72, 0.01, 0, 1)` (celle de Sphere) | fondu de 250 ms, 150 ms après le début |
| Un menu « ⋯ » | 250 ms, même courbe | fondu de 150 ms |
| À la fermeture | même durée | le contenu s'efface d'abord (150 ms) |

- 350 ms sort des trois durées (150, 250, 500 ms). C'est écrit comme une exception, comme la carte d'une réussite.
- Avec « réduire les animations », tout s'ouvre et se ferme d'un coup.

## Accessibilité

- Les zones restent de vrais boutons :
  - avec leur nom : « Alertes, 2 non lues », « Compte : kevin », « Menu » ;
  - avec `aria-expanded` ;
  - avec un contour visible au clavier, à l'intérieur de la zone.
- Le menu du compte garde le clavier de la 0.70.2 : le premier choix prend le focus, puis flèches et Échap.
- La taille au doigt reste d'au moins 2,75 rem sur téléphone.

## Vérifié avant la PR

- **Tests** :
  - l'ouverture et la fermeture (clic, Échap, clic ailleurs, page choisie) ;
  - le passage de la cloche au compte sans refermer ;
  - ☰ et ✕ sur téléphone ;
  - le focus rendu à la zone ;
  - « réduire les animations ».
- **Captures** (ordinateur et téléphone, clair et sombre) :
  - capsule fermée, compte ouvert, alertes ouvertes ;
  - ☰ ouvert ;
  - un menu « ⋯ ».
- **Pas de débordement** à 390 px.

## Écarts

- **Sur téléphone, le logo reste hors de la capsule** : fermée, elle garde la cloche, l'initiale et ☰ à droite ; ouverte, elle s'élargit vers la gauche sur toute la largeur et passe par-dessus le logo. Le mettre dedans aurait déplacé le logo à chaque ouverture.
- **À la fermeture**, le contenu disparaît d'un coup et le cadre se replie en 350 ms (le fondu de sortie n'apportait rien de visible).
- **Les menus « ⋯ »** se déroulent par un découpage de haut en bas (`clip-path`), sans mesurer leur hauteur ; même courbe, 250 ms.
- **Le focus** va sur Profil à l'ouverture du menu du compte sans faire défiler la capsule (sinon la rangée du haut disparaissait pendant le déroulé).
- **Une règle ancienne cachait tout `nav` de la barre sur téléphone** : elle ne vise plus que le menu principal, pour que les pages s'affichent dans la capsule.
- **Vérifié** :
  - 322 tests de l'interface (nouveaux : une seule zone ouverte et le passage de l'une à l'autre, Échap qui rend le focus, clic ailleurs, page choisie, la cloche sur téléphone), lint et typecheck ;
  - captures sur la démo, sur ordinateur en clair et en sombre et sur téléphone : capsule fermée, en cours de déroulé (six images de 0 à 600 ms), compte ouvert, alertes ouvertes, ☰ ouvert, un menu « ⋯ » ; sans débordement à 390 px.
