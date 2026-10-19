# 98 — Le logo au diamant, « jobA1 » sans personnage (version 0.71.3)

> Statut : **validé** le 2026-10-19.
> Origine : ta remarque du 2026-10-19 sur la 0.71.2 : « il faut enlever les personnages en face de jobA et rajouter le 1 pour jobA1 ; et je me suis trompé, il faut ce logo pour le site : Diamant en contour ».
> Se construit sur la 0.71.2 (PR #215, fusionnée).

## 1. Le logo : « Diamant en contour »

Planche « 55. Le diamant dessiné à la main », piste « Diamant en contour » :
- **les deux boucles** sont celles de la 0.71.2, à l'identique ;
- **au centre, l'étoile pleine devient un diamant tracé au stylo**, pêche, au trait un peu plus épais que les boucles (× 1,1) ;
- **aux petites tailles** (32 et 16 px, l'onglet du navigateur), la planche ne garde **qu'une boucle**, avec un diamant plus grand, pour rester lisible ;
- **les couleurs** ne changent pas : boucles `#2340C8`, diamant `#F4A261` ; en sombre `#9DB0FF` et `#E8B48A` ;
- **les épaisseurs** suivent la planche : 2,6 à 150 px, 3,8 à 56 px, 4 à 46 px, 8 à 32 px, 10 à 16 px.

Les tracés sont copiés de la planche. Les icônes (onglet, application) sont régénérées par `frontend/scripts/icones.py`.

## 2. « jobA1 » en entier, sans personnage

- **Le personnage de l'heure** qui remplaçait le « 1 » une fois connecté (docs/68) **disparaît**. La barre affiche « jobA1 » en entier, connecté ou non, à côté du logo.
- **Le composant `BrandFigure`, ses dessins et son test** sont retirés. Ses exceptions dans `docs/interface.md` sont barrées.
- **La mascotte de l'assistant** (0.71.2) ne change pas.

## Vérifié avant la PR

- **Tests** :
  - le logo : deux boucles et le diamant en contour, puis une seule boucle à 32 px et moins ;
  - « jobA1 » en entier dans la barre, sans personnage.
- **Captures**, en clair et en sombre :
  - la barre ;
  - les icônes (32 px, application) ;
  - sur ordinateur et sur téléphone.
- **L'audit des rangées** est vide.

## Écarts

- **Dans la barre**, le logo (28 px) garde les deux boucles, au trait de 5 : la version à une boucle de la planche (32 px) est réservée à l'onglet du navigateur, sous 24 px dans l'interface.
- **Le favicon** (SVG et PNG 32 px) prend la petite version de la planche : une boucle, le grand diamant, trait de 8 (8,8 pour le diamant).
- **Le script des icônes** rend chaque icône dans une page neuve : changer la taille d'une page déjà rendue laissait parfois l'ancien rendu dans la capture (l'icône 192 sortait en double).
- **Retirés** : `BrandFigure`, son test, les dessins `src/assets/personnages/`, `scripts/personnages.mjs` et leurs styles ; les mentions dans `docs/interface.md`.
- **Vérifié** :
  - 325 tests de l'interface (le logo : deux boucles et le diamant, une seule boucle sous 24 px), lint et typecheck ;
  - audit des rangées vide ;
  - captures sur la démo : la barre en clair, en sombre, sur téléphone ; les icônes 32, 180, 192, 512 et maskable.
