# 97 — Le logo du site et la mascotte de l'assistant (version 0.71.2)

> Statut : **validé** le 2026-10-19.
> Origine : ta demande du 2026-10-19, à partir de la planche « Pistes de logo jobA1 ». Pour le site, « deux tours ouverts », au trait bleu. Pour l'IA, « sans le trait autour ».

## Les deux dessins, repris tels quels

**1. Le logo du site** (planche « 52. Boucles souples autour de l'étoile », piste « Deux tours ouverts », en bleu stylo) :
- deux boucles à main levée : l'une dépasse, l'autre reste ouverte ;
- au centre, l'étoile pêche ;
- en clair : trait bleu stylo `#2340C8`, étoile `#F4A261` ;
- en sombre : trait `#9DB0FF`, étoile `#E8B48A` (les couleurs sombres de la planche) ;
- le trait s'épaissit quand le logo rapetisse, comme sur la planche : 2,6 à 160 px, 3,6 à 60 px, 5 à 32 px, 7 à 16 px. Il reste lisible dans un onglet du navigateur.

**2. La mascotte de l'assistant** (planche « 35. Le D allégé », piste « Sans le trait autour ») :
- le visage plein bleu `#2340C8`, avec la pointe du nez ;
- l'œil fermé en arc blanc, l'étoile pêche à la place de l'autre œil, le sourire blanc ;
- en sombre : visage `#9DB0FF`, traits `#12121F`, étoile `#F4A261` ;
- elle aussi s'épaissit aux petites tailles (28, 16 px).

Les tracés sont copiés de la planche, sans les redessiner.

## Où ils vont

| Endroit | Aujourd'hui | Après |
|---|---|---|
| Barre du haut, devant « jobA1 » | un rond violet | **le logo** (1,6 rem) |
| Onglet du navigateur (favicon) | rond violet | **le logo**, version 32 et 16 px |
| Icônes de l'application (téléphone, écran d'accueil) | rond violet | **le logo blanc sur un carré bleu** (la version « app » de la planche) ; l'icône « maskable » garde la marge de sécurité |
| Bouton de l'assistant (en bas à droite) | un point menthe | **la mascotte** (1,75 rem) |
| En-tête du panneau de l'assistant | « Assistant » seul | **la mascotte** devant « Assistant » |
| Les réponses de l'assistant | rien | **la mascotte** en petit (1,5 rem) devant chaque réponse |

**Ne change pas** :
- le personnage de l'heure qui remplace le « 1 » de « jobA1 », une fois connecté (docs/68) ;
- les couleurs de l'interface (le violet du menu reste) ;
- **l'icône de l'extension** du navigateur : tu es en train de l'envoyer à Mozilla, on la change plus tard si tu veux, dans une version de l'extension.

## Comment

- **Deux composants**, `BrandMark` et `AssistantMascot`, avec un SVG en ligne et les tracés de la planche. La taille fixe l'épaisseur du trait (les paliers de la planche) ; le sombre se fait par variables CSS. Les deux sont décoratifs (`aria-hidden`) : le texte à côté dit ce que c'est.
- **Les fichiers d'icônes** (`favicon-32.png`, `apple-touch-icon.png`, `icon-192.png`, `icon-512.png`, `icon-maskable-512.png`) sont régénérés depuis le SVG par un petit script dans `frontend/scripts/`. Un `favicon.svg` s'ajoute pour les navigateurs qui le prennent : il est net à toute taille et suit le mode sombre.
- **La couleur du thème** dans le manifeste ne change pas : blanc.

## Vérifié avant la PR

- **Tests** :
  - le logo est dans la barre ;
  - la mascotte est sur le bouton de l'assistant, dans son en-tête et devant chaque réponse ;
  - les deux sont décoratifs.
- **Captures**, en clair et en sombre :
  - la barre ;
  - l'onglet du navigateur (favicon 16 et 32 px) ;
  - l'icône de l'application ;
  - le bouton et le panneau de l'assistant ;
  - sur ordinateur et sur téléphone.
- **L'audit des rangées** (docs/94) est vide.

## Écarts

- **Le trait du favicon SVG** est fixé à 6 (entre les paliers 32 et 16 px de la planche) : un SVG ne connaît pas sa taille d'affichage. Le PNG de 32 px a le même trait.
- **Les icônes de l'application** sont tirées d'un seul dessin (le carré bleu et le logo) ; la version « maskable » réduit le logo à la moitié pour rester dans la zone sûre.
- **Les tracés** sont dans `frontend/src/brandPaths.ts`, la régénération des icônes dans `frontend/scripts/icones.py` (commande dans `docs/exploitation.md`).
- **Vérifié** :
  - 327 tests de l'interface (nouveaux : le logo et la mascotte, leurs paliers de trait ; la mascotte dans l'en-tête et devant la réponse, pas devant la question), lint et typecheck ;
  - audit des rangées vide ;
  - captures sur la démo (assistant simulé) : la barre en clair et en sombre, le bouton et le panneau de l'assistant, sur téléphone ; les icônes 32, 180, 192 et 512 (maskable).
