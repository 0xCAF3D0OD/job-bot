# 100 — Le logo choisi : un trait qui entoure le diamant (version 0.71.6)

> Statut : **validé** le 2026-10-19.
> **Remplacé par docs/102** (0.74.0) : le logo devient le visage du 1.
> Origine : ta planche du 2026-10-19, « voici le logo qu'on a choisi ». Elle contient le logo, les tests (couleur, sombre, noir seul, icône d'app, 48 / 32 / 16 px) et la mascotte.
> Remplace le logo de docs/98. Se construit sur la 0.71.5 (PR #218, fusionnée).

## Ce que dit la planche

- **Le logo** : « un trait au stylo qui entoure, une seule fois, et qui dépasse ; au centre, un diamant pêche tracé au même trait ».
  - **Une seule boucle bleue**, presque ronde, qui se referme en haut à droite et dépasse un peu son point de départ.
  - **Le diamant pêche** au centre, au trait, avec la même épaisseur que la boucle (aujourd'hui, il est 1,1 fois plus épais).
  - **« jobA1 »** à droite, en gras, couleur du texte.
- **Les tests** :
  - **couleur** : boucle `#2340C8`, diamant `#F4A261` ;
  - **sombre** : boucle `#9DB0FF`, diamant `#E8B48A`, sur fond sombre ;
  - **noir seul** : la boucle et le diamant en noir, pour l'impression et les documents ;
  - **icône d'app** : un carré bleu aux coins arrondis, la boucle blanche et le diamant pêche ;
  - **un trait plus épais sous 32 px**, et la même forme à 48, 32 et 16 px. On ne passe plus à une version différente aux petites tailles.

## Ce qui change

| Endroit | Aujourd'hui (docs/98) | Après |
|---|---|---|
| **Barre du haut** (28 px) | deux boucles, le diamant | **une boucle**, le diamant |
| **Favicon** (SVG et 32 px) | une boucle, un grand diamant | **le nouveau logo**, trait épaissi |
| **Icônes de l'application** (180, 192, 512, maskable) | le logo blanc sur le carré bleu | **la boucle blanche et le diamant pêche** sur le carré bleu, comme la planche |
| **Version noire** | n'existe pas | **un `logo-noir.svg`** dans `frontend/public/`, pour les PDF ou les documents qui en auraient besoin plus tard |

- **Les paliers du trait** (viewBox 100) : fin en grand, plus épais sous 32 px, pour que la boucle reste lisible à 16 px dans l'onglet. Je les règle sur les captures pour retrouver le rendu de la planche à 48, 32 et 16 px.
- **Le tracé** de la boucle est repris de la planche. Si la planche existe en SVG dans le canevas, je copie ses tracés tels quels. Sinon, je les redessine au plus près et je te montre la comparaison côte à côte avant la PR.

## Ne change pas

- **La mascotte** (0.71.5) : les trois visages et le bouton sont déjà ceux de la planche.
- **« jobA1 »** dans la barre : le texte et sa taille.
- **L'icône de l'extension** : elle changera dans une version de l'extension, après l'envoi à Mozilla.

## Retiré

- La deuxième boucle et le petit diamant réservé aux petites tailles (`LOGO_DIAMOND_SMALL_SIZE`).

## Vérifié avant la PR

- **Tests** :
  - le logo : une boucle et le diamant à toutes les tailles ;
  - le trait plus épais sous 32 px ;
  - décoratif (`aria-hidden`).
- **Les icônes** sont régénérées par `frontend/scripts/icones.py`.
- **Captures**, comparées à la planche :
  - la barre en clair et en sombre, sur ordinateur et sur téléphone ;
  - le favicon à 16 et 32 px ;
  - l'icône d'app ;
  - la version noire.
- **L'audit des rangées** est vide.

## Écarts

- **Les tracés viennent de la planche « Le logo final »** du canevas « Pistes de logo jobA1 », copiés tels quels : la boucle, le diamant et le diamant agrandi pour les petites tailles. La vue passe à `4 6 92 92`, comme sur la planche.
- **Les paliers du trait** sont ceux de la planche : 3,6 en grand (100 px et plus), 5 dès 60 px, 5,5 jusqu'à 33 px. À 32 px et moins, la boucle a un trait de 8,5 et le diamant un trait de 8, avec le diamant agrandi.
- **La barre (28 px) prend donc la version épaisse**, puisqu'elle est sous 32 px.
- **L'icône d'app** : le logo occupe 69 % du carré, comme sur la planche (66 px sur 96). La version « maskable » garde 50 %, pour rester dans la zone sûre.
- **La mascotte « réfléchit »** a maintenant un point plein pour bouche, de la taille des yeux, à ta demande du 2026-10-19, à la place du « o » au trait de la 0.71.5.
- **Vérifié** :
  - 327 tests de l'interface (le logo : une boucle et le diamant au même trait, les paliers, le diamant agrandi à 32 px et moins ; la mascotte « réfléchit » à trois points), lint et typecheck ;
  - audit des rangées vide ;
  - captures sur la démo : la barre en clair, en sombre et sur téléphone ; les icônes 32 et 192 ; les trois visages.
