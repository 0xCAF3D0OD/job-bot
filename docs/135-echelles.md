# 135 — Les échelles de design : peu de valeurs, les mêmes partout (versions 1.6.x)

> Statut : **validé** le 2026-10-23 : graisses en option A (600), sauf les liens inactifs du menu en 400 ; lettre, CV et feuille ORP hors échelle ; les trois règles modifiées. `--faint` est corrigé dans une version à part, juste après la 1.6.0 (§5). Les variables Figma changent une fois la 1.6.0 fusionnée.
> Origine : l'inventaire des styles fait pour les variables Figma (22 octobre 2026) et ta demande : une échelle d'espacements en base 4 px de 8 valeurs, 6 à 7 tailles de texte, 3 rayons, les graisses 400, 600 et 700, une seule couleur orange (logo-spark réservé au logo), la fusion des doublons.

## Le constat

| | Aujourd'hui dans le code | Proposé |
|---|---|---|
| Espacements (padding, margin, gap) | 44 valeurs différentes, toutes écrites en dur | 8 |
| Tailles de texte | 39 valeurs, de 0,62 à 2,4 rem | 7 |
| Rayons | 20 valeurs, de 2 à 24 px ; seul `--radius` (12 px) est nommé et il est écrit en dur 27 fois | 3 |
| Graisses | 400, 500, 600, 650, 700 | 400, 600, 700 |
| Oranges | `--orange`, `--warn`, `--logo-spark`, plus deux oranges écrits en dur | 1 orange pour l'interface, 1 pour le logo |

La règle 10.2 de `docs/regles-ui-ergonomie.md` (« aucune valeur en dur ») ne peut pas tenir sans ce resserrage.

## La phrase qui guide

**Une valeur de l'échelle ou rien ; un écart de moins de 2 px ne se voit pas, et ceux qui se voient sont listés ici.**

Règle d'arrondi : vers la valeur la plus proche. À égalité, la valeur la plus proche d'une règle déjà validée dans `docs/interface.md`, sinon la plus grande (les pages restent aérées).

---

## 1. Espacements : 8 valeurs, base 4 px

| Variable | Valeur | Rôle (d'après `docs/interface.md`) |
|---|---|---|
| `--space-1` | 4 px (0,25 rem) | entre un titre et sa sous-ligne |
| `--space-2` | 8 px (0,5 rem) | entre deux faits, deux pastilles |
| `--space-3` | 12 px (0,75 rem) | entre un titre et son contenu, entre deux repliables |
| `--space-4` | 16 px (1 rem) | entre étiquettes, titre et faits |
| `--space-5` | 20 px (1,25 rem) | entre deux cartes ; marge intérieure minimale d'une carte |
| `--space-6` | 24 px (1,5 rem) | marge intérieure d'une carte ; sous « Enregistrer » |
| `--space-8` | 32 px (2 rem) | entre les grands blocs d'une page |
| `--space-12` | 48 px (3 rem) | marges de page (haut des écrans vides, bas de page) |

Le nom dit le multiple de 4 px, pour qu'on retrouve la valeur sans ouvrir le fichier.

### Arrondis

| Valeur actuelle | Emplois | Devient | Écart | Où l'écart se verra |
|---|---|---|---|---|
| 0,1 rem · 0,12 · 0,15 · 0,2 rem | 84 | 4 px | +0,8 à +2,4 px | Lignes d'Aujourd'hui, du Suivi et des listes calmes : la sous-ligne grise s'écarte à peine du titre. |
| 0,25 rem | 58 | 4 px | 0 | — |
| 0,3 · 0,35 rem | 121 | 4 px | −0,8 à −1,6 px | Invisible (écart entre icône et texte dans les boutons, les pastilles). |
| 0,4 · 0,45 rem | 108 | 8 px | +0,8 à +1,6 px | Invisible. |
| 0,5 rem | 141 | 8 px | 0 | — |
| 0,55 · 0,6 rem | 143 | 8 px | −0,8 à −1,6 px | À peine : les rangées de boutons (« Garder · Écarter », actions des fiches) se resserrent de 1,6 px. |
| 0,65 · 0,7 rem | 38 | 12 px | +0,8 à +1,6 px | Invisible. |
| 0,75 rem | 146 | 12 px | 0 | — |
| 0,8 · 0,85 rem | 55 | 12 px | −0,8 à −1,6 px | À peine : marge des lignes d'offres, des toasts, des tableaux du journal. |
| 0,9 · 0,95 rem | 72 | 16 px | +1,6 à +0,8 px | À peine : les lignes d'offres, d'Aujourd'hui et du Suivi (écart entre logo et texte), les onglets, le panneau de l'assistant gagnent 1,6 px. |
| 1 · 1,05 rem | 219 | 16 px | 0 à −0,8 px | — |
| 1,1 rem | 33 | 16 px | −1,6 px | À peine : marge des toasts, cartes de bloc du CV, puces des listes. |
| 1,15 · 1,2 · 1,25 · 1,3 · 1,35 rem | 83 | 20 px | −0,8 à +1,6 px | Invisible. |
| 1,4 · 1,5 · 1,6 rem | 116 | 24 px | +1,6 à −1,6 px | À peine : connexion, carte de note, entraînement à l'entretien (1,4 rem) gagnent 1,6 px. |
| **1,75 · 1,8 rem** | 7 | 32 px | **+4 px** | **Visible** : espace entre les liens du menu du haut ; marges des cartes de formulaire (Profil, Réglages) ; en-tête des Offres et des Candidatures ; rubriques des Réglages. |
| 2 · 2,2 rem | 35 | 32 px | 0 à −3,2 px | À peine : signature de la lettre (si la lettre suit l'échelle, voir §6). |
| **2,5 rem** | 14 | 32 px | **−8 px** | **Visible** : au-dessus de chaque titre de section (toutes les pages), Bilan › Ce qui marche, écrans vides illustrés, connexion, Rendez-vous › Le mois, colonnes des Alertes. C'est l'égalité 32/48 tranchée par la règle « 2 rem entre les grands blocs ». |
| 3 rem | 6 | 48 px | 0 | — |
| **4 · 4,5 rem** | 6 | 48 px | **−16 à −24 px** | **Visible** : le vide en bas de chaque page (bande grise), la page des Offres, le corps des Candidatures, la page introuvable, Découvrir. |
| Négatifs (−0,2 à −1 rem) | 21 | −4, −8 ou −16 px | ±1,6 px | Invisible ; ils compensent une marge voisine et suivent la valeur compensée. |

**Hors échelle**, inchangés : les valeurs en `em` (elles suivent la taille du texte), les pourcentages, les `calc()` qui réservent la place d'un élément fixe (barre d'onglets, dock « Postuler » : 5,5, 9 et 11 rem), les retraits qui laissent la place d'une icône ou d'un bouton (2,1 rem dans la recherche, 3,25 rem), la compensation de la zone tactile de l'info-bulle (−0,9 rem pour une cible de 2,75 rem), `1px` et `-1px` des bordures.

---

## 2. Tailles de texte : 7

| Variable | Valeur | Rôle |
|---|---|---|
| `--font-caption` | 12 px (0,75 rem) | pastilles, compteurs, étiquettes en capitales, légendes |
| `--font-small` | 14 px (0,875 rem) | texte secondaire, sous-lignes, champs de filtre |
| `--font-body` | 16 px (1 rem) | texte courant, champs (16 px évite le zoom de l'iPhone), menu |
| `--font-title` | 18 px (1,125 rem) | titre de carte, de panneau, de tuile |
| `--font-section` | 22 px (1,375 rem) | titre de section (aujourd'hui 1,35 rem) |
| `--font-figure` | 26 px (1,625 rem) | chiffres mis en avant (tuiles, compte du mois) ; titres de connexion |
| `--font-page` | 32 px (2 rem) | titre de page |

### Arrondis

| Valeur actuelle | Emplois | Devient | Écart | Où l'écart se verra |
|---|---|---|---|---|
| **0,62 · 0,65 · 0,68 · 0,7 · 0,72 rem** | 20 | 12 px | **+0,5 à +2 px** | **Visible** : les compteurs de la barre d'onglets et de la cloche, les pastilles de l'en-tête de navigation, l'étiquette en capitales (eyebrow), les marques du calendrier du Suivi grossissent ; les pastilles rondes devront peut-être s'élargir. |
| 0,75 · 0,76 · 0,78 · 0,8 rem | 54 | 12 px | 0 à −0,8 px | À peine : en-têtes de tableaux, sélecteurs segmentés, pastilles de filtre. |
| 0,82 à 0,93 rem | 202 | 14 px | −0,9 à +0,9 px | Invisible ; c'est la moitié du texte de l'application. |
| 0,95 · 0,98 · 1 · 1,05 rem | 62 | 16 px | −0,8 à +0,8 px | Invisible (le menu du haut, les titres des lignes d'offres). |
| 1,08 · 1,1 · 1,15 · 1,2 rem | 22 | 18 px | +0,7 à −1,2 px | À peine : le nom jobA1 à côté du logo, titres de la carte de note et de la réussite (1,2 rem) un peu plus petits. |
| 1,25 · 1,3 · 1,35 · 1,4 · 1,45 rem | 17 | 22 px | +2 à −1,2 px | À peine : la phrase du jour d'Aujourd'hui (1,3 rem) et les titres des Premiers pas grossissent de 1,2 px ; les titres de section ne changent pas (21,6 → 22 px). |
| 1,5 · 1,55 · 1,6 · 1,7 · 1,75 · 1,9 rem | 17 | 26 px | +2 à −4,4 px | **Visible par endroits** : le titre de la fiche d'une offre (1,5 rem) et la page introuvable grossissent de 2 px ; le nom du CV (1,7 rem) rapetisse de 1,2 px ; le titre de la connexion (1,6 rem) ne change pas. |
| 2 rem | 5 | 32 px | 0 | — |
| **2,4 rem** | 2 | 32 px | **−6,4 px** | **Visible** : le grand chiffre du mois ORP (Aujourd'hui) et du Rendez-vous. |

**Hors échelle** : les textes des graphiques en SVG (7 à 12 unités, mis à l'échelle avec le dessin).

## 3. Rayons : 3

| Variable | Valeur | Rôle |
|---|---|---|
| `--radius-sm` | 8 px | boutons, champs, logos d'entreprise, surlignages |
| `--radius` | 12 px | cartes, panneaux, menus, toasts (le nom actuel est gardé) |
| `--radius-pill` | 999 px | pilules, pastilles, sélecteurs |

Les cercles (`50 %` : visage du 1, initiale du compte, points) sont une forme, pas un rayon : ils restent.

| Valeur actuelle | Emplois | Devient | Où l'écart se verra |
|---|---|---|---|
| 2 · 3 · 4 px | 20 | 8 px | **Visible** : les mots surlignés (formations, actualités) et les liens au survol deviennent plus ronds. |
| 6 · 7 · 0,5 rem · 8 · 9 px · 0,6 rem | 39 | 8 px | Invisible ; les logos d'entreprise passent de 9,6 à 8 px (règle « Coins » 4 à mettre à jour). |
| 10 px | 25 | 12 px | À peine : toasts, onglets, menus « ⋯ », notes. |
| 12 px · 0,75 rem | 28 | `var(--radius)` | Aucun ; le nom remplace la valeur en dur. |
| 14 px | 21 | 12 px | À peine : cartes de formation, repliables, panneau de la cloche et du compte. |
| **16 px** | 19 | 12 px | **Visible sur les grandes cartes** : panneau de la fiche d'une offre, cartes de formulaire (Profil, Réglages), panneau de l'assistant, cartes de l'accueil. |
| **18 · 20 · 22 · 24 px** | 13 | 12 px | **Clairement visible** : tuiles et carte du haut du Bilan, carte de réussite, Rendez-vous › Le mois, bulles de Découvrir. |

## 4. Graisses : 400, 600, 700

| Valeur actuelle | Emplois | Devient | Où l'écart se verra |
|---|---|---|---|
| 400 | 17 | 400 | — |
| **500** | 86 | **600** (recommandé) | **Visible partout** : titres de page et de section, boutons, lien actif du menu, titres des lignes d'offres, en-têtes de tableaux deviennent plus gras. |
| 600 | 72 | 600 | — |
| 650 | 1 | 600 | Invisible (la note en cercle, presque plus utilisée). |
| 700 | 18 | 700 | — |

**Tranché (option A)** : tout le 500 passe à 600, sauf les liens inactifs du menu, en 400. La 1.3.1 (docs/130 §F) avait fixé les titres en 500 ; `docs/interface.md` (Structure 8) est mis à jour. L'option B (titres en 400) est écartée.

Variables : `--weight-regular` (400), `--weight-semibold` (600), `--weight-bold` (700).

## 5. Couleurs

### Une seule orange pour l'interface

| Variable | Clair | Sombre | Remplace |
|---|---|---|---|
| `--orange` | #e08a2e | #e08a2e | `--orange` (#fca863) et `--warn` (#e08a2e) |
| `--orange-text` | #a34b07 | #f0a35a | `--warn-text`, et #f3b67a écrit en dur en sombre |
| `--orange-soft` | #fff1e4 | #3a2a1a | les fonds d'étiquette écrits en dur (9 endroits avec le sombre) |

C'est **une seule orange**, déclinée comme l'accent (`--accent`, `--accent-soft`) : le texte orange a besoin d'une teinte plus foncée pour être lisible (5,9:1 sur blanc ; #e08a2e n'a que 2,7:1). #e08a2e est gardé plutôt que #fca863 : plus de contraste (2,7:1 contre 1,9:1 sur blanc) pour les points et les bordures.

Où l'écart se verra :
- **Visible** : les points « relancée » du calendrier et de la légende du Suivi, le point d'avertissement des indicateurs, la tuile en alerte du Bilan, les semaines manquées du Rythme, les mots surlignés des certificats deviennent d'un orange plus soutenu ; l'initiale d'entreprise de couleur « c1 » aussi (le texte foncé y reste lisible, 7:1).
- À peine : les étiquettes orange en sombre (#f3b67a → #f0a35a).

`--logo-spark` (#f4a261, #e8b48a en sombre) **reste réservé au logo et au visage du 1** ; il n'est plus employé ailleurs. Le visage n'a plus de repli sur `--orange`.

### Les doublons fusionnés

| Doublon | Fusion | Changement visible |
|---|---|---|
| `--accent-text` = `--accent` (clair et sombre) | `--accent` partout (45 emplois) | aucun |
| `--logo-line` = `--mascot-face` | `--logo-line` | aucun |
| `--mascot-star` = `--logo-spark` en clair | `--logo-spark` | à peine : l'étoile de la mascotte en sombre prend la pêche adoucie du logo |
| `--mascot-line` (#fff / #12121f) ≈ `--on-accent` (#fff / #0f0f1a) | `--on-accent` | aucun |
| `--panel` (#f6f6fa) ≈ `--band` (#f7f7fa) en clair | `--panel` prend #f7f7fa en clair ; en sombre, ils restent distincts | aucun |
| `--faint` redéfini en sombre avec la même valeur | ligne supprimée | aucun |
| `--border-strong` utilisé, jamais défini | `--border` | aucun |
| `#11111f` écrit en dur (5 fois) | `--text`, sauf là où le texte doit rester foncé sur un fond clair en sombre (à vérifier un par un) | aucun |

`--bg` et `--surface` sont tous deux blancs en clair mais différents en sombre : ce n'est pas un doublon, ils restent.

**`--faint`** (#9a9aae) n'a que 2,8:1 sur blanc ; il est employé 7 fois en texte. Il passe à au moins 4,5:1 sur tous ses fonds, en clair et en sombre, dans une version à part juste après la 1.6.0 (la 1.6.1).

## 6. Tranché

1. **Les graisses** : option A, sauf les liens inactifs du menu en 400 (§4).
2. **Les feuilles imprimables** (lettre, CV, feuille ORP) imitent le papier et le PDF : elles restent **hors échelle**, pour que l'aperçu reste fidèle au PDF.
3. **Les règles validées mises à jour** dans `docs/regles-ui-ergonomie.md` (§10.5 : une règle change d'abord dans ce document), puis dans `docs/interface.md` :
   - Structure 6, les filets : 1,75 rem → 2 rem (32 px) ;
   - Coins 4, les logos d'entreprise : 0,6 rem → 8 px ;
   - Structure 8, la graisse des titres : 500 → selon le choix A ou B.

## 7. La migration, page par page

Une version par étape, chacune sur sa branche partie de main, avec ta validation avant la suivante.

| Version | Étape | Ce qui change |
|---|---|---|
| 1.6.0 | **Le socle, sans rien de visible** | Les variables entrent dans `style.css` ; chaque valeur déjà sur l'échelle passe par sa variable ; les doublons de même valeur fusionnent ; `12px` → `var(--radius)`. Les captures avant et après doivent être identiques au pixel près. |
| 1.6.1 | **`--faint` lisible** | Au moins 4,5:1 sur tous ses fonds, en clair et en sombre. |
| 1.6.2 | **Le commun** | Barre du haut et menu, boutons, champs, pastilles, cartes, repliables, toasts, pied de page, l'orange, les graisses. Visible sur toutes les pages : captures de toutes les pages. |
| 1.6.3 | Aujourd'hui | Lignes, phrase du jour, compte du mois, Premiers pas. |
| 1.6.4 | Candidatures › Offres et la fiche d'une offre, Préparer | |
| 1.6.5 | Suivi | Calendrier, colonne, panneau d'une candidature. |
| 1.6.6 | Bilan | Tuiles, Mois précédents, les vues du détail. |
| 1.6.7 | Rendez-vous | |
| 1.6.8 | Alertes, Profil, Réglages | |
| 1.6.9 | Formations, Actualités, l'assistant | |
| 1.6.10 | Connexion, inscription, accueil, Découvrir, pages légales, page introuvable | Puis le garde-fou ci-dessous. |

**Pour chaque étape** :
- captures **avant et après**, côte à côte, à 1440 et 390 px, en clair et en sombre, sur la démo et sur un compte neuf (base jetable) ; avec, pour chaque paire, une image des différences (les pixels changés en couleur), pour voir d'un coup d'œil ce qui a bougé ;
- les trois audits (règles, alignement, accessibilité, avec exploration des repliables et des vues) à zéro ;
- les tests de l'interface, lint et vue-tsc.

**Le garde-fou (1.6.10)** : un contrôle ajouté à `frontend/scripts/regles.py` (ou un test) refuse dans les styles un espacement, une taille de texte, un rayon ou une graisse qui ne passe pas par une variable, sauf les exceptions listées aux §1 et §2.

## 8. Figma

Les variables actuelles de Figma reflètent le code d'aujourd'hui (20 espacements nommés par leur valeur, 19 tailles, 8 rayons, 4 graisses, 29 couleurs). **Elles changent une fois la 1.6.0 fusionnée** : elles prennent alors les noms et valeurs du §1 au §5 (ceux que la 1.6.0 a mis dans le code).

## Garde-fous

- Rien ne disparaît : seules des valeurs changent, aucune information ni action.
- Un écart visible qui n'est pas dans ce document est un défaut : il se corrige ou s'ajoute ici avant la PR.
- Les règles validées (`docs/interface.md`) ne changent qu'avec ton accord, au §6.

## Écarts (1.6.0)

- **978 valeurs** passent par leur variable : celles qui étaient déjà exactement sur une échelle (espacements de 0,25 à 3 rem, tailles 0,75, 1 et 2 rem, rayons 8, 12 et 999 px, graisses 400, 600 et 700). Les autres changent page par page à partir de la 1.6.2. La lettre, le CV et la feuille ORP ne sont pas touchés.
- **L'orange** : `--warn-text` devient `--orange-text` ; `--orange-soft` remplace le fond des étiquettes écrit en dur (#fff1e4, #3a2a1a en sombre). `--orange` et `--warn` gardent leurs valeurs jusqu'à la 1.6.2, où ils deviennent une seule orange.
- **Doublons fusionnés** (même valeur) : `--accent-text` → `--accent`, `--mascot-face` → `--logo-line`, `--faint` redéfini en sombre, `--border-strong` → `--border`. Ceux dont la valeur change un peu (`--mascot-line`, `--mascot-star`, `--panel` en clair) attendent la 1.6.2, pour que la 1.6.0 reste identique au pixel près.
- **Les règles** (`docs/regles-ui-ergonomie.md` §4 bis, `docs/interface.md` : filets, coins des logos, graisse des titres) sont à jour dès maintenant ; le code les rejoint au fil des 1.6.x.
- **Deux outils** pour toute la migration : `frontend/scripts/captures.py` photographie chaque page et chaque état (repliables ouverts, vues choisies) à 1440 et 390 px, en clair et en sombre ; `frontend/scripts/compare.py` compare deux séries et produit, pour chaque capture changée, avant | après | différences en rouge. Pour qu'une série soit reproductible : l'horloge de la page est figée, le rendu de Chrome est stabilisé (sans quoi l'anticrénelage du texte variait de quelques pixels), chaque capture part du haut de la page, après le voile de chargement, et deux navigateurs au plus tournent en même temps.

## Vérifié (1.6.0)

- **Identique au pixel près** : 168 captures de la démo et 128 d'un compte neuf, avant et après. Seule « Bilan › Actualités » (sombre, 1440 px) diffère de 450 pixels, autant qu'entre deux séries d'avant : la ligne « Relevé il y a … », calculée par le serveur.
- Test de contraste mis à jour (`--accent`, `--orange-text`, le texte orange sur son fond en clair et en sombre). 438 tests de l'interface, lint, vue-tsc.
- Les trois audits à zéro sur la démo et sur un compte neuf (l'accessibilité aussi en sombre).
