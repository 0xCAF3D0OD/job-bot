# 102 — Le logo, le visage du 1 (version 0.74.0)

> Statut : **validé** le 2026-10-20.
> Origine : ton plan « le visage du 1 » (prévu en 0.70.8), repris sur main le 2026-10-20 : « Option 2. Nouvelle version 0.74.0 sur main actuel ».
> Remplace le logo de docs/100. Se construit sur la 0.73.0 (PR #221, fusionnée).

## Le symbole

Un visage complice fait avec le 1 du nom :

- **le 1** trace le sourcil et le nez ;
- **un œil bleu**, plein ;
- **un œil pêche** : la bille, la seule touche d'accent ;
- **un sourire discret**.

## Deux réglages

| Réglage | Où | Le dessin |
|---|---|---|
| **S4, penché** | l'en-tête, à côté de « jobA1 » (32 px) | le visage bleu penché de −6°, viewBox `8 8 86 86`, trait de 14 ; suit le mode sombre |
| **S5, droit** | les icônes | le visage blanc et la bille pêche sur du bleu, le sourire plus court |

Les tracés sont dans `frontend/src/brandPaths.ts` (`LOGO_*` pour S4, `ICON_*` pour S5). Le composant reste `BrandMark.vue`.

## Les icônes

Tirées de S5 par `frontend/scripts/icones.py`, fond transparent hors du carré.

| Forme | Le dessin | Fichiers |
|---|---|---|
| **Badge** | carré bleu aux coins arrondis (rx 26), visage à 72 %, trait de 15,4 | `favicon.svg`, `favicon-32.png` ; extension : `icons/16.png`, `32.png`, `48.png`, `128.png` |
| **Plein** | carré bleu plein, visage à 70 % | `apple-touch-icon.png` (180), `icon-192.png`, `icon-512.png` |
| **Maskable** | comme « plein », visage à 52 %, dans la zone sûre | `icon-maskable-512.png` |
| **Noir seul** | le visage en noir, sans carré | `logo-noir.svg` |

## Les jetons

| Jeton | Clair | Sombre |
|---|---|---|
| `--logo-line` (le 1, l'œil, le sourire) | `#2340c8` | `#9db0ff` |
| `--logo-spark` (la bille) | `#f4a261` | `#e8b48a` |

`--logo-ink` et `--logo-star` (docs/97) disparaissent.

## La règle

**Une couleur et une seule touche d'accent** : tout le visage en bleu (ou en blanc sur le bleu), la bille seule en pêche.

## Ce qui change ailleurs

- **Le diamant quitte la marque.** Il ne restait que dans le logo : le bouton « Assistant » porte la mascotte, et aucun badge « Meilleure du jour » n'existe sur main. Rien d'autre à remplacer par la bille.
- **Le titre** : « jobA1 » est déjà écrit en entier, sans personnage à la place du 1 (0.71.3).
- **L'extension** prend les nouvelles icônes (docs/100 les laissait de côté).

## Ne change pas

- **La mascotte de l'Assistant** (docs/99) : même famille de visages, pour l'IA seulement.
- **L'étincelle à 4 branches** (icône « spark » des Réglages, rubrique IA) : elle reste réservée à l'IA (docs/101).
- **L'animation des lettres** : hors de cette version.

## Vérifié

- 344 tests de l'interface (le logo : `aria-hidden`, viewBox `8 8 86 86`, penché de −6°, deux traits, un œil, une bille), lint et typecheck.
- Planche de contrôle : l'en-tête en clair et en sombre, les icônes 16, 32, 48, 128, 192, maskable et la version noire.
