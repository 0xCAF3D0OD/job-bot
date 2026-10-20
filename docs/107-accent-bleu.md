# 107 — L'accent au bleu du logo (version 0.76.2)

> Statut : **validé** le 2026-10-20.
> Origine : nos lectures du 2026-10-20 (Laws of UX, « 58 rules for beautiful UI design »), et la règle 60-30-10 : une seule couleur d'accent. Les boutons étaient violets (`#635BFF`, la maquette « Hirace »), le logo et la mascotte bleus (`#2340C8`). Ton choix : **aligner l'accent sur le bleu du logo**.

## Les jetons

| Jeton | Clair (avant → après) | Sombre (avant → après) |
|---|---|---|
| `--accent` (boutons, liens, pastilles, focus) | `#635bff` → **`#2340c8`** | `#8780ff` → **`#9db0ff`** |
| `--accent-strong` (survol) | `#5148f0` → `#1a3099` | `#9d97ff` → `#b8c6ff` |
| `--accent-soft` (fonds pâles) | `#efeeff` → `#eaeefc` | `#25234f` → `#1e2550` |
| `--accent-text` (texte sur fond pâle) | `#5148f0` → `#2340c8` | `#9d97ff` → `#9db0ff` |
| **`--on-accent`** (nouveau : le texte posé sur l'accent) | `#fff` | **`#0f0f1a`** |

L'accent est donc **exactement** la couleur du logo, `--logo-line`, en clair comme en sombre.

## Le texte sur l'accent

En sombre, le bleu clair du logo ne porte pas un texte blanc (2:1). Le violet d'avant ne le portait pas non plus (3,2:1, sous le seuil de 4,5:1). Le texte posé sur l'accent passe par `--on-accent` : blanc en clair, **foncé en sombre**. 16 règles qui écrivaient `#fff` sur l'accent l'utilisent maintenant (boutons pleins, onglets choisis, pastilles, compteurs, tuile mise en avant, jours du rythme…).

| Contraste | Avant | Après |
|---|---|---|
| Bouton plein, clair | 4,7:1 | **8,0:1** |
| Bouton plein, sombre | 3,2:1 | **9,1:1** |
| Lien sur la carte, sombre | 5,5:1 | **8,4:1** |
| Texte sur fond pâle, clair | — | 6,9:1 |

## Aussi

- **L'extension** : ses jetons suivent (`popup.css`), et le contour des champs qu'elle remplit sur Job-Room et les sites passe au même bleu.
- **Ne change pas** : la pêche de la bille (une seule touche d'accent, docs/103), les couleurs d'état (vert, orange, rouge), l'orange, la menthe et le bleu ciel des logos d'entreprise.

## Vérifié

- Captures en clair et en sombre : l'accueil, les étapes 1 et 2 de l'assistant des alertes.
- Tests, lint, typecheck.
