# 96 — La page choisie, entourée à main levée (version 0.71.1)

> Statut : **retiré** en 0.71.4 (2026-10-19), à ta demande : « enlève cette forme de sélection, je vais changer le logo ».
> Origine : ta demande du 2026-10-19, « une sorte de halo sur Aujourd'hui ou Candidatures pour marquer que c'est sélectionné », puis « et entourer de façon stylo à main levée ? », puis la maquette du même jour. Choix : le **trait moyen**.

## Ce qui change

- **Dans le menu principal** (ordinateur), la page en cours, Aujourd'hui ou Candidatures, est **entourée d'une boucle tracée à main levée**. Elle remplace le trait souligné actuel.
- **La boucle** :
  - c'est une ellipse un peu irrégulière qui ne se referme pas tout à fait et dépasse son point de départ, comme un trait de stylo ;
  - elle est violette, la couleur du menu ;
  - le trait est **moyen** (1,9 px), aux bouts arrondis ;
  - elle déborde de 6 px autour du mot.

  Une seule forme sert partout. Elle s'étire à la taille du mot, et l'épaisseur du trait reste constante.
- **Elle se dessine** quand on arrive sur la page, en 0,6 s, du point de départ jusqu'au bout. Si « réduire les animations » est activé, elle est là d'emblée.
- **Sur téléphone**, dans la barre d'onglets du bas, la boucle entoure **l'icône** de l'onglet choisi, avec la même forme et le même trait. Le nom de l'onglet passe en gras, et le violet de l'onglet reste.
- **Le survol** d'une autre page ne dessine rien : seule la couleur du texte change, comme aujourd'hui.

## Accessibilité

- **La boucle est décorative** (`aria-hidden`). La page en cours reste annoncée par `aria-current="page"`.
- **Le texte de la page choisie passe en gras moyen et en couleur pleine**, pour qu'elle reste reconnaissable sans la boucle, par exemple en mode contraste élevé.

## Le mouvement

**0,6 s sort des trois durées** de `docs/interface.md` (150, 250 et 500 ms). Le cas est écrit comme une exception, comme la carte d'une réussite : c'est un tracé qu'on suit des yeux.

## Ce qui ne change pas

- Les onglets des pages (Offres, Suivi…) gardent leur trait souligné.
- La capsule.
- Les pastilles.

## Vérifié avant la PR

- **Tests** :
  - la boucle est sur la page en cours seulement ;
  - elle passe à l'autre page au changement ;
  - elle est décorative et `aria-current` est conservé ;
  - sur téléphone, elle est sur l'icône de l'onglet choisi.
- **L'audit des rangées** (docs/94) est vide.
- **Captures**, sur ordinateur et téléphone, en clair et en sombre :
  - la boucle complète ;
  - une image au milieu du tracé.

## Écarts

- **La boucle déborde plus que prévu** : 15 px sur les côtés et 9 px en haut et en bas (au lieu de 6 px), parce que le lien du menu n'a pas de marge latérale ; à 6 px, elle touchait les lettres.
- **Le menu garde de la place autour de ses liens** (0,7 rem en haut et en bas, 1,1 rem sur les côtés) : il défile à l'horizontale s'il manque de place, ce qui rognait la boucle.
- **Un composant `HandLoop`** porte la forme, partagée par le menu et la barre d'onglets.
- **Vérifié** :
  - 325 tests de l'interface (la barre d'onglets : la boucle sur l'onglet choisi, décorative, qui change d'onglet), lint et typecheck ; `aria-current="page"` sur la page en cours, contrôlé sur la démo ;
  - audit des rangées vide ;
  - captures sur la démo : la boucle complète, une image au milieu du tracé (280 ms), en sombre, et sur téléphone autour de l'icône.

## Retrait (0.71.4)

- **La boucle est retirée** du menu et de la barre d'onglets, avec le composant `HandLoop`, ses styles et l'exception de durée dans `docs/interface.md`.
- **Le menu revient à son état d'avant** : la page en cours en violet, en gras, soulignée ; `aria-current="page"` reste.
- **Vérifié** : 325 tests de l'interface, lint et typecheck ; audit des rangées vide ; captures sur la démo (menu en clair et en sombre, barre d'onglets du téléphone).
