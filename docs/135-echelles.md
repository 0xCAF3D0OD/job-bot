# 135 — Les échelles de design : peu de valeurs, les mêmes partout (versions 1.6.x)

> Statut : **validé** le 2026-10-23 : graisses en option A (600), sauf les liens inactifs du menu en 400 ; lettre, CV et feuille ORP hors échelle ; les trois règles modifiées. `--faint` est corrigé dans une version à part, juste après la 1.6.0 (§5) ; le 23 octobre : le texte gris passe tout en `--muted`, `--faint` est réservé au non-texte. Les variables Figma changent une fois la 1.6.0 fusionnée.
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

## 2 bis. Interlignes : 3 (ajouté le 23 octobre)

| Variable | Valeur | Rôle |
|---|---|---|
| `--leading-none` | 1 | pastilles, icônes, compteurs |
| `--leading-tight` | 1,3 | titres de carte, lignes courtes |
| `--leading-normal` | 1,5 | texte courant (1,5 au moins, `docs/interface.md` Aéré 2) ; la base de la page (avant 1,55) |

| Valeur actuelle | Emplois | Devient | Où l'écart se verra |
|---|---|---|---|
| 1 · 1,1 | 12 | 1 | — |
| 1,15 · 1,2 · 1,25 · 1,3 · 1,35 · 1,4 | 21 | 1,3 | À peine : titres d'actualités (1,15 → 1,3), compte du mois (1,4 → 1,3). |
| 1,45 · 1,5 · 1,55 · 1,6 · 1,65 | 59 | 1,5 | **Partout un peu** : la base passe de 1,55 à 1,5, soit 0,8 px de moins par ligne de 16 px ; les descriptions des Réglages et les encadrés (1,6) se resserrent de 1,6 px par ligne. |

Dans Figma, une variable d'interligne se lit en pixels : les trois valeurs y sont des variables de documentation, et l'interligne passe par **7 styles de texte** (`jobA1/font-caption` à `jobA1/font-page`), liés aux variables de taille, interligne en pourcentage.

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

**`--faint`** (#9a9aae) n'a que 2,6 à 2,8:1 sur les fonds clairs. Décision du 23 octobre : pas deux gris quasi identiques. **Tout le texte gris passe par `--muted`** ; `--faint` ne sert plus qu'aux éléments qui ne sont pas du texte, avec au moins 3,3:1 en clair (3:1 exigé, une marge gardée) :

| Emploi de `--faint` | Nature | Devient |
|---|---|---|
| « Effacer » des filtres, désactivé | texte | règle supprimée : l'état n'existe plus, le bouton est masqué tant qu'aucun filtre n'est actif (docs/43 n° 13) |
| Le « i » des boutons d'aide | texte (une lettre) | `--muted` |
| Chevron des lignes repliables | icône | `--faint` |
| Soulignement en pointillé des aides au survol | décoration | `--faint` |
| Encre des dessins de chargement | illustration | `--faint` |

`--faint` passe à #868698 en clair (3,31 à 3,57:1 selon le fond) ; en sombre il reste #9a9aae (6 à 6,9:1). C'est la 1.6.1.

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
| 1.6.1 | **Le gris du texte** | Tout texte gris en `--muted` ; `--faint` réservé au non-texte, au moins 3,3:1 en clair. Correctif du compteur des Actualités (commit à part). |
| 1.6.2 | **Le commun** | Barre du haut et menu, boutons, champs, pastilles, cartes, repliables, toasts, pied de page, l'orange, les graisses. Visible sur toutes les pages : captures de toutes les pages. |
| 1.6.3 | Aujourd'hui | Lignes, phrase du jour, compte du mois, Premiers pas ; les initiales d'entreprise sans orange (accent, menthe, ciel). |
| 1.6.4 | **Les trois composants** (retours du 23 octobre) | Bouton, note d'une offre, repliable : Figma et code (ci-dessous). |
| 1.6.5 | Candidatures › Offres et la fiche d'une offre, Préparer | |
| 1.6.6 | Suivi | Calendrier, colonne, panneau d'une candidature. |
| 1.6.7 | Bilan | Tuiles, Mois précédents, les vues du détail. |
| 1.6.8 | Rendez-vous | |
| 1.6.9 | Alertes, Profil, Réglages | |
| 1.6.10 | Formations, Actualités, l'assistant | |
| 1.6.11 | Connexion, inscription, accueil, Découvrir, pages légales, page introuvable ; les composants partagés entre plusieurs pages | Encadrés, contacts, entraînement à l'entretien, menu « ⋯ », chargement, cartes du tableau de bord… : ce qu'aucune page seule ne peut arrondir sans toucher les autres. |
| 1.6.12 | **Le garde-fou**, seul | Ci-dessous. |

**Pour chaque étape** :
- captures **avant et après**, côte à côte, à 1440 et 390 px, en clair et en sombre, sur la démo et sur un compte neuf (base jetable) ; avec, pour chaque paire, une image des différences (les pixels changés en couleur), pour voir d'un coup d'œil ce qui a bougé ;
- les trois audits (règles, alignement, accessibilité, avec exploration des repliables et des vues) à zéro ;
- les tests de l'interface, lint et vue-tsc.

**Le garde-fou (1.6.12)** : un contrôle ajouté à `frontend/scripts/regles.py` (ou un test) refuse dans les styles un espacement, une taille de texte, un rayon ou une graisse qui ne passe pas par une variable, sauf les exceptions listées aux §1 et §2.

## 8. Figma

Les variables actuelles de Figma reflètent le code d'aujourd'hui (20 espacements nommés par leur valeur, 19 tailles, 8 rayons, 4 graisses, 29 couleurs). **Mises à jour le 23 octobre**, après la fusion de la 1.6.0 : elles portent les noms et valeurs du §1 au §5. Figma montre la cible ; le code la rejoint au fil des 1.6.x.

## 9. Bilan (25 octobre, 1.6.24)

**Le code est à l'échelle.** De la 1.6.0 à la 1.6.12, toutes les pages sont passées aux variables des §1 à §5 ;
depuis la 1.6.12, le garde-fou (`frontend/src/scales.test.ts`) refuse toute valeur en dur hors des exceptions
ci-dessous. De la 1.6.13 à la 1.6.23, les écrans ont rejoint leur référence Figma, une page à la fois.

**Figma** (fichier jobA1) :
- les variables : 55 (couleurs en clair et en sombre, tailles d'ordinateur et de téléphone, typographie,
  8 espacements, 3 rayons) et 13 styles de texte ;
- **56 composants** et 35 icônes, construits en 8 lots, chacun avec sa revue (contraste WCAG AA vérifié, un lien
  vers son code, ses états seulement s'il se clique, clair et sombre) :
  - lot 1 et premiers : bouton, note d'une offre, repliable, carte, initiales, case et progression ORP, jour,
    semaine, visage du 1, pilule, bouton icône, annulation, offre du jour, écran vide, premiers pas, tuile du visage ;
  - lot 3 (le commun) : lien, ligne de liste (ordinateur et téléphone), carte à emplacement, pied de page, bloc et
    voile de chargement, lien de navigation, cloche, compte, en-tête, onglet, barre d'onglets ;
  - lot 4 (Candidatures) : pastille, onglet de page, champ de recherche, ligne et puce de filtre, carte d'offre,
    titre de groupe ;
  - lot 5 (Bilan) : segment, sélecteur segmenté, conclusion mise en avant, tuile de chiffre, ligne de mois, barre
    de parcours ;
  - lots 6 et 7 (Suivi, détail d'une offre) : point de statut, marque de jour, jour du calendrier, navigation de
    mois, lien de retour, ligne de définition (courte et large), point fort, fait, barre d'actions ;
  - lot 8 (Alertes, Rendez-vous) : interrupteur, champ de saisie, statut d'alerte, étapes de l'assistant.
- **7 écrans de référence, 28 états**, chacun en 1440 et 390 px, en clair et en sombre (112 cadres), avec des
  notes qui citent les règles :

| Écran | États | Code |
|---|---|---|
| Aujourd'hui | journée type, écran vide, premiers pas, chargement (voile, puis blocs) | 1.6.17 |
| Candidatures (offres) | liste, écran vide, aucun résultat, chargement (voile, puis blocs) | 1.6.18 |
| Bilan | résultats, détail ouvert, écran vide, chargement | 1.6.19 |
| Suivi | suivi, calendrier ouvert, écran vide, chargement | 1.6.20 |
| Détail d'une offre | offre ouverte, sections ouvertes | 1.6.21 |
| Alertes | alertes, premiers pas, chargement | 1.6.22 |
| Rendez-vous | rendez-vous, carnet ouvert, obligation en retard, premier rendez-vous, chargement | 1.6.23 |

**Exceptions qui restent, voulues** :
- hors échelle : la lettre, le CV et la feuille ORP (et son impression), qui imitent le papier ; les valeurs en
  `em`, les pourcentages et les calculs qui réservent la place d'un élément fixe (§1) ; les textes des graphiques
  en SVG (§2) ; les illustrations (maquette de « La plateforme », confettis) ; les marges du bouton d'aide ; les
  champs à 16 px (sous 16 px, l'iPhone zoome) ;
- les règles : la date au-dessus du titre en style étiquette (§3 des règles) ; les liens inactifs du menu en 400 ;
- `--logo-spark` réservé au logo et au visage du 1 ; « Refus » en gris, pas en rouge (un refus n'est pas une erreur).

**Écarts connus entre Figma et le code** :
- la légende du calendrier du Suivi a « à compléter » (l'anneau orange d'une ligne ORP incomplète), que le Point de
  statut de Figma n'a pas ;
- la phrase de conclusion s'arrête à 40 rem de large dans le code (la largeur de lecture) : sur ordinateur, elle
  passe à la ligne là où Figma la garde sur une ligne.

**Pas encore d'écran de référence dans Figma** : Profil, Réglages, Bilan › Formations et Actualités, Préparer (la
lettre), l'assistant, et les pages publiques (connexion, inscription, « La plateforme », pages légales, accueil).
Leurs styles sont à l'échelle ; leurs écrans attendent une prochaine série.

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

- **Identique au pixel près** : 168 captures de la démo et 128 d'un compte neuf, avant et après. Seule « Bilan › Actualités » (sombre, 1440 px) diffère de 450 pixels, autant qu'entre deux séries d'avant. *Rectifié en 1.6.1* : ce n'était pas « Relevé il y a … » mais le compteur des nouveautés sur l'onglet, qui revenait parfois après la visite (une course entre deux requêtes, corrigée en 1.6.1).
- Test de contraste mis à jour (`--accent`, `--orange-text`, le texte orange sur son fond en clair et en sombre). 438 tests de l'interface, lint, vue-tsc.
- Les trois audits à zéro sur la démo et sur un compte neuf (l'accessibilité aussi en sombre).

## Écarts (1.6.1)

- **Le gris du texte** : le « i » des boutons d'aide passe à `--muted` ; `--faint` (#868698 en clair, 3,31 à 3,57:1 ; #9a9aae en sombre, 6 à 6,9:1) ne sert plus qu'au chevron des repliables, au soulignement en pointillé des aides et à l'encre des dessins de chargement. Un test vérifie le contraste et que `--faint` ne sert à rien d'autre.
- **« Effacer » désactivé n'existe pas** : le bouton est masqué tant qu'aucun filtre n'est actif (docs/43 n° 13) ; la règle `.filters-clear:disabled`, restée de la 0.20.0, est supprimée. Il n'y a donc pas de version désactivée à comparer à l'active.
- **Le compteur des Actualités** (commit à part) : la requête partie au démarrage pouvait revenir après la visite des Actualités et ramener le compteur remis à zéro, selon l'ordre d'arrivée. Elle est ignorée si une visite a eu lieu entre-temps ; un test reproduit la course (il échoue sans le correctif). C'était la capture qui bougeait toute seule en 1.6.0.
- **Les captures à heure figée côté serveur** : `frontend/scripts/serveur_fige.py` lance `jobbot` (la graine de la démo et l'API) avec l'horloge arrêtée à `CAPTURES_TIME`, la même que celle de la page. Les captures attendent aussi que la page ne défile plus avant de la photographier (ouvrir un repliable pouvait lancer un défilement qui finissait pendant la capture).
- **Figma** : les variables suivent maintenant les échelles validées (§1 à §5) : 8 espacements, 3 rayons, 7 tailles, 3 graisses, 25 couleurs (une seule orange, `--orange-text`, `--orange-soft`, `--faint` réservé au non-texte, doublons fusionnés). Le code les rejoint au fil des 1.6.x : l'orange, `--panel` et les couleurs de la mascotte changent en 1.6.2.

## Vérifié (1.6.1)

- **Deux séries d'avant identiques** (démo et compte neuf), sauf le compteur des Actualités, corrigé ici.
- **Avant / après** : 73 captures de la démo et 66 du compte neuf changent, toutes sur les pages à repliables ou à aides au survol (Réglages, Profil, Alertes, Formations, Rendez-vous, Bilan › Ce qui marche, la fiche d'une offre) ; seuls bougent le chevron, le pointillé et le « i », un peu plus foncés en clair. Le texte ne bouge pas.
- 453 tests de l'interface, lint, vue-tsc ; les trois audits à zéro sur la démo et un compte neuf, l'accessibilité aussi en sombre.

## Écarts (1.6.2)

- **Partout** : les graisses (500 → 600 ; les liens inactifs des menus et des onglets en 400, l'onglet actif de Préparer passe à 600 pour rester distinct), les interlignes (§2 bis ; la base 1,55 → 1,5), l'orange unique (`--warn` disparaît, `--orange` passe à #e08a2e ; le texte orange écrit en dur en sombre passe par `--orange-text`), `--panel` = `--band` en clair, la mascotte aux couleurs du logo et de `--on-accent`.
- **Composants communs seulement** pour les espacements, les tailles et les rayons : barre du haut, menu, cloche et compte, barre d'onglets du téléphone, boutons, champs, étiquettes et pastilles, repliables, onglets et sélecteurs, toasts, titres, aides au survol, écrans vides, pied de page. Les règles propres à une page attendent leur version (1.6.3 à 1.6.10).
- **Les marges négatives du bouton d'aide « i »** restent hors échelle (§1) : le script les avait arrondies, ce qui décalait le texte d'une carte ; rétablies.
- **L'audit des règles** ne mesure plus la partie cachée d'un texte coupé par « … » (« facult… » dans une ligne repliable était compté comme un texte à 4 px du bord, alors que la partie visible s'arrête bien avant).
- **Figma** : trois variables d'interligne (documentation : Figma lit une variable d'interligne en pixels) et sept styles de texte `jobA1/font-caption` à `jobA1/font-page`, liés aux variables de taille, interligne en pourcentage.

## Vérifié (1.6.2)

- **Avant / après** : toutes les captures changent (168 de la démo, 128 d'un compte neuf), comme attendu : l'interligne de base et les graisses touchent chaque page. Revues une à une sur Aujourd'hui, le Suivi, la fiche d'une offre, les Réglages, le Profil, en clair et en sombre, à 1440 et 390 px : même structure, lignes un peu plus serrées, titres et boutons en 600, l'orange unique sur les marques « relancer » et l'initiale orange.
- 453 tests de l'interface, lint, vue-tsc ; les trois audits à zéro sur la démo et un compte neuf, l'accessibilité aussi en sombre.

## Écarts (1.6.3)

- **Les initiales d'entreprise** n'utilisent plus l'orange (règle §4 : l'orange est réservé à ce qui demande d'agir) : trois couleurs, l'accent (`--on-accent` dessus, 8:1 en clair, 9:1 en sombre), la menthe et le ciel (initiale foncée, 11:1 et 10:1). Une entreprise peut donc changer de couleur d'initiale : le partage se fait désormais sur trois couleurs au lieu de quatre. Le test de contraste vérifie les trois et l'absence d'orange.
- **Aujourd'hui à l'échelle** : 59 valeurs (espacements, tailles, rayons) des règles propres à la page (`.today-*`, l'offre du jour, le mois ORP, Premiers pas, le rythme, la carte de réussite) et de l'initiale (`.logo`, coins 8 px). Le rythme et la carte de réussite servent aussi au Suivi et à Préparer : ils y changent de la même façon. Le grand chiffre du mois passe de 2,4 à 2 rem (prévu au §2).
- **Le test de l'audit** (`frontend/scripts/test_regles.py`, Playwright) : un vrai texte à 4 px du bord est trouvé, coupé ou non ; la partie cachée d'un texte coupé par « … » ne compte pas. Avec l'audit d'avant la 1.6.2, seul ce dernier cas échoue : le test distingue bien les deux. Il se lance à part (`uv run --with playwright --with pytest pytest ../frontend/scripts/test_regles.py`), pas dans la suite du backend.
- `--on-accent` s'écrit `#ffffff` au lieu de `#fff` (même couleur) : le test de contraste ne lit que les couleurs à six chiffres.

## Vérifié (1.6.3)

- **Avant / après** : 72 captures de la démo et 48 d'un compte neuf changent : Aujourd'hui, les initiales (Offres, la fiche d'une offre, le Suivi), et le rythme là où il apparaît aussi (Réglages, Bilan › Semaines), décalé d'1 à 2 px. Revues en clair et en sombre, à 1440 et 390 px.
- 453 tests de l'interface (dont le contraste des trois initiales), lint, vue-tsc ; les 3 tests de l'audit ; les trois audits à zéro sur la démo et un compte neuf, l'accessibilité aussi en sombre.

## Écarts (1.6.4)

Les retours du 23 octobre sur les trois premiers composants Figma (bouton, note d'une offre, repliable), appliqués dans Figma et dans le code. Les versions de pages se décalent d'un cran (Offres en 1.6.5, … , garde-fou en 1.6.11).

- **Bouton secondaire** : sa bordure passe à `--faint` (3,3 à 3,6:1 en clair, 6 à 6,9:1 en sombre ; avant 1,2:1). Elle vaut pour les boutons sans classe, `secondary` et `small`, qui ont le même aspect.
- **Bouton principal** : en sombre, le survol passe à #d4ddff (`--accent-strong`, écart de 1,55 avec le normal au lieu de 1,25) ; ce bleu sert aussi au survol des liens en sombre. Désactivé, il devient gris (`--panel`, `--border`, `--muted`) au lieu d'un bleu pâle à 60 %.
- **Repliable** : le titre reste en 600, ouvert et fermé. L'anneau de focus entoure toute la carte (autour de la seule ligne, il passait sur le contenu ouvert) ; dans une liste, il reste à l'intérieur pour ne pas mordre sur la voisine. Ouvert, le survol teinte la ligne (`--accent-soft`) ; le résumé gris y tombait à 4,3:1, il passe à l'accent (6,9:1).
- **Note d'une offre** : plus de jauge (règle §4 : le visage et un mot) ; le visage reste à 20 px ; « À creuser » passe à un gris chaud (#766b60 en clair, #968779 en sombre, 4,75:1 au moins), proposé plutôt que le ciel : en texte, le ciel n'atteint que 1,9:1, et foncé à 4,8:1 il se confond avec le bleu de « Proche ». Le mot passe à 14 px et l'écart à 8 px (l'échelle, en avance sur la 1.6.5).
- **Styles de texte** : trois styles en 600 (`jobA1/font-caption-semibold`, `font-small-semibold`, `font-body-semibold`), les seules tailles en 600 qui n'avaient qu'un style en 400 ; les styles de titre, de section et de page sont déjà en 600.
- **Le test de contraste** vérifie aussi `--score-dig`, et accepte `--faint` sur le bord des boutons secondaires.
- **CLAUDE.md** : la migration 1.6.x est dispensée de la règle « écran manquant dans Figma », tant qu'elle n'ajoute, ne retire ni ne déplace aucun élément.

## Vérifié (1.6.4)

- **Figma** : les trois composants refaits ; contraste WCAG 2.2 AA recalculé sur 56 paires (textes 4,5:1, bords et anneaux 3:1, en clair et en sombre) : tout passe, le bouton désactivé étant exempté.
- **Dans l'application** : chaque état photographié (survol, focus au clavier, désactivé, ouvert), en clair et en sombre, conforme à Figma.
- **Avant / après** : 50 captures de la démo et 68 d'un compte neuf changent, sur les pages qui ont des boutons secondaires, des notes ou un bouton désactivé.
- 455 tests de l'interface, lint, vue-tsc ; les 3 tests de l'audit ; les trois audits à zéro sur la démo et un compte neuf, l'accessibilité aussi en sombre.

## Écarts (1.6.5)

- **Offres, fiche d'une offre, Préparer à l'échelle** : 130 valeurs (espacements, tailles, rayons) des règles propres à ces pages. Une règle n'est arrondie que si aucune de ses classes ne sert aussi une autre page (`.notice`, `.meta-line`, `.jobs-head`, `.step`, les filtres des Actualités, les blocs et « Effet des critères » du Profil, l'entraînement à l'entretien…) : ces règles attendent la version de leurs autres pages. La lettre, le CV et la feuille ORP restent hors échelle.
- **« Il te manque : … »** sur une offre : à 14 px, l'interligne 1,3 collait la ligne à celle du dessus sur téléphone (l'audit l'a trouvé) ; c'est une phrase, elle passe à `--leading-normal` (1,5), comme le texte courant.
- **Le visage du 1 dans la note** est cadré au plus près de son dessin (`viewBox` 13 15 74 74 au lieu de 8 8 86 86) : il remplit ses 20 px, à la hauteur du mot. Seulement dans la note (`FaceMark snug`) : ailleurs (écrans vides, réussite, tuiles), le visage garde son cadre. Figma suit.
- **L'anneau de focus du repliable** suit les coins de la carte (`--radius`), même là où le repliable n'a pas de cadre (dans les formulaires), comme dans Figma.
- Test : la note sans jauge, le visage cadré au plus près.

## Vérifié (1.6.5)

- Avant / après : seules changent les Offres, la fiche d'une offre, Préparer, et la note de l'offre du jour sur Aujourd'hui (le visage). Dans la liste, les métadonnées passent de 13,6 à 14 px : sur certaines offres, le lieu passe à la ligne et la ligne grandit un peu ; rien n'est ajouté ni déplacé.
- Tests de l'interface, lint, vue-tsc ; les 3 tests de l'audit ; les trois audits à zéro sur la démo et un compte neuf, l'accessibilité aussi en sombre.

## Écarts (1.6.6)

- **Le Suivi à l'échelle** : 50 valeurs. Le périmètre est maintenant calculé : les composants de la page (sa vue et ce qu'elle importe), moins ceux qu'une autre vue importe aussi ; une règle n'est arrondie que si sa classe de tête n'appartient qu'à la page. Les composants partagés (contacts, entraînement à l'entretien, menu « ⋯ », chargement, confirmation…) attendent la passe prévue en 1.6.11.
- **La jauge d'affinité revient** partout (liste, fiche, offre du jour), décision du 23 octobre : elle donne la nuance à l'intérieur d'un niveau. Règle §4 : « visage + un mot, avec une jauge discrète pour la nuance ». Sa piste passe de `--muted` mêlé à 22 % (une valeur calculée, sans variable) à `--border`, comme dans Figma : indiscernable en clair, à peine plus sombre en sombre. Figma suit.
- **Le visage du 1 cadré au plus près partout** (écrans vides, carte de réussite, tuiles, la note) : il remplit sa taille. Le logo garde son cadre.

## Vérifié (1.6.6)
- Avant / après : changent le Suivi (cases du calendrier un peu plus basses, la colonne de droite suit), la note avec sa jauge (Offres, fiche, Préparer, Aujourd'hui) et, sur un compte neuf, les écrans vides dont le visage remplit maintenant son cadre (Bilan, Actualités, Rendez-vous, Compte).
- 456 tests de l'interface (la jauge et le visage), lint, vue-tsc ; les 3 tests de l'audit ; les trois audits à zéro sur la démo et un compte neuf, l'accessibilité aussi en sombre.

## Écarts (1.6.7)

- **Le Bilan à l'échelle** : 52 valeurs (tuiles, « Mois précédents », la conclusion, les vues du détail : parcours, par mois, ce qui marche, semaines). Les cartes `.dash-card` servent aussi à Aujourd'hui (le rythme) : elles attendent la passe des composants partagés (1.6.11), avec leur rayon de 20 à 24 px.
- **Décisions du 23 octobre** : la piste de la jauge reste sur `--border` ; la fin de la migration se sépare en 1.6.11 (pages publiques et composants partagés) et 1.6.12 (le garde-fou, seul).

## Vérifié (1.6.7)
- Avant / après : seul le Bilan change (24 captures de la démo ; sur un compte neuf, le Bilan est vide et ne change pas) : tuiles un peu plus hautes, lignes du parcours plus serrées.
- 456 tests de l'interface, lint, vue-tsc ; les 3 tests de l'audit ; les trois audits à zéro sur la démo et un compte neuf, l'accessibilité aussi en sombre.

## Écarts (1.6.8)

- **Le Rendez-vous à l'échelle** : 19 valeurs (le bloc « Préparer », le mois, le résultat du rendez-vous, le carnet). La feuille ORP imprimable reste hors échelle ; les contacts et le menu « ⋯ », partagés, attendent la 1.6.11.

## Vérifié (1.6.8)
- Avant / après : seul le Rendez-vous change (8 captures de la démo, 4 d'un compte neuf), de quelques pixels (questions, feuille, mois).
- 456 tests de l'interface, lint, vue-tsc ; les 3 tests de l'audit ; les trois audits à zéro sur la démo et un compte neuf, l'accessibilité aussi en sombre.

## Écarts (1.6.9)

- **Alertes, Profil et Réglages à l'échelle** : 146 valeurs propres à ces trois pages (alertes et assistant de création, e-mails des sites, critères et « Effet des critères », blocs et certificats du Profil, rubriques des Réglages, extension, plateforme). Les composants que d'autres pages importent aussi attendent la 1.6.11.

## Vérifié (1.6.9)
- Avant / après : seules changent les Alertes, le Profil (trois onglets) et les Réglages (toutes les rubriques), sur la démo comme sur un compte neuf. Les lignes des sites suivis et des documents prennent un peu plus d'air ; le sommaire des Réglages se resserre.
- 456 tests de l'interface, lint, vue-tsc ; les 3 tests de l'audit ; les trois audits à zéro sur la démo et un compte neuf, l'accessibilité aussi en sombre.

## Écarts (1.6.10)

- **Formations, Actualités et l'assistant à l'échelle** : 114 valeurs (tuiles et fiches de formation, filtres, une des actualités et lignes, panneau de l'assistant). L'assistant est importé par le cadre de l'application, pas par une page : son panneau compte comme une racine du périmètre. **Il n'apparaît pas sans clé d'IA** (ni dans la démo ni sur un compte de test) : ses valeurs sont arrondies comme les autres, mais aucune capture ne le montre ; à vérifier sur une instance avec l'IA.

## Vérifié (1.6.10)
- Avant / après : changent Formations et Actualités (démo et compte neuf), de quelques pixels (tuiles, filtres, une des actualités). Une capture des Réglages › Outils d'un compte neuf diffère aussi : l'en-tête collant photographié en cours de défilement, le contenu identique ; artefact de capture, pas de changement.
- 456 tests de l'interface, lint, vue-tsc ; les 3 tests de l'audit ; les trois audits à zéro sur la démo et un compte neuf, l'accessibilité aussi en sombre.

## Écarts (1.6.11)

- **Le reste du site à l'échelle** : les pages publiques (connexion, inscription, « La plateforme », accueil, conditions, à propos, page introuvable) et les composants partagés entre plusieurs pages (encadrés, contacts, entraînement à l'entretien, menu « ⋯ », chargement, cartes du tableau de bord, confirmation, assistant de recherche…). Plus aucune règle n'attend sa page : ce qui reste hors échelle est listé au §1 et ci-dessous.
- **Hors échelle, en plus des exceptions du §1** : la maquette de l'application dessinée sur « La plateforme » (`.dmock-*`, une illustration en miniature) et les confettis de la réussite : comme les dessins en SVG, leurs tailles font partie du dessin.
- **`captures.py`** photographie aussi les pages publiques et la page introuvable.
- **Code mort repéré** : les règles `.preview-*` (l'ancien aperçu du menu Progresser) ne servent plus à aucun gabarit ; arrondies avec le reste, à supprimer avec le garde-fou (1.6.12).

## Vérifié (1.6.11)
- Avant / après : toutes les pages changent (196 captures de la démo, 156 d'un compte neuf), comme attendu : les composants partagés sont partout. Le plus visible : les cartes du tableau de bord (Aujourd'hui, Bilan) passent au rayon commun de 12 px au lieu de 20 à 24 px, comme prévu au §3 ; « La plateforme » élargit un peu son texte d'introduction.
- **Non vérifiable par les captures** : la connexion et l'inscription renvoient vers Aujourd'hui une fois connecté (démo et compte de test sans connexion) ; leurs valeurs sont arrondies comme les autres, à regarder déconnecté.
- 456 tests de l'interface, lint, vue-tsc ; les 3 tests de l'audit ; les trois audits à zéro sur la démo et un compte neuf, l'accessibilité aussi en sombre.

## Écarts (1.6.12)

- **Le garde-fou** est un test de l'interface (`frontend/src/scales.test.ts`), lancé par `npm test` et `make test` : dans `style.css` et les styles des composants, un espacement, une taille de texte, un rayon, une graisse ou un interligne doit passer par une variable des échelles. Admis partout : les variables, 0, les bordures d'un pixel (±1 px), les unités relatives (`em`, `%`, `vw`, `vh`, `lh`), les calculs (`calc`, `max`, `min`, `clamp`, `env`) et les mots-clés. Admis par règle, chacun avec sa raison dans le test : la lettre, le CV et la feuille ORP (et son impression en millimètres), les illustrations (maquette de « La plateforme », confettis), les marges du bouton d'aide, les champs à 16 px (sous 16 px, l'iPhone zoome), la place réservée au bouton d'une carte, les marges de la carte de réussite autour de son dessin. Un second test vérifie que le garde-fou trouve bien une valeur en dur.
- **Dernière valeur arrondie** : la marge intérieure de la carte de réussite (3,5 rem → `--space-12`, 48 px), oubliée par la table d'arrondi.
- **Code mort supprimé** : les règles `.preview-*` (l'ancien aperçu du menu Progresser), qu'aucun gabarit n'utilise.

## Vérifié (1.6.12)
- Le garde-fou passe sur le code (aucune valeur en dur hors des exceptions) et son second test prouve qu'il trouve une valeur en dur. Avant d'ajouter l'impression de la feuille ORP aux exceptions, il avait relevé six valeurs : cinq de l'impression (millimètres, points) et la carte de réussite.
- Avant / après : aucune capture ne change (196 de la démo, 156 d'un compte neuf) ; la carte de réussite n'apparaît pas dans les captures et le code supprimé ne servait plus.
- 458 tests de l'interface (dont les 2 du garde-fou ; la machine chargée, la suite tourne avec 2 processus), lint, vue-tsc ; les 3 tests de l'audit ; les trois audits à zéro sur la démo et un compte neuf, l'accessibilité aussi en sombre.

## Écarts (1.6.13)

- **Un fichier de test qui ne démarre pas fait échouer la suite** : un rapporteur de vitest (`frontend/vitest.total.ts`) compare, sur la suite complète (`npm test`, `make test`), le nombre de fichiers lancés au nombre de fichiers `*.test.ts` de `src/`, et fait aussi échouer la suite sur toute erreur hors d'un test. Lancer un seul fichier (`npx vitest run src/x.test.ts`) n'est pas contrôlé, exprès. Deux processus par défaut (`maxWorkers: 2`) : sous charge, davantage ne démarraient pas tous. Vérifié : un fichier laissé de côté exprès fait échouer la suite (« 110 fichiers de tests lancés sur 111 attendus », code de sortie 1).
- **Le garde-fou contrôle aussi l'intérieur des calculs** (`calc`, `max`, `min`, `clamp`) : une longueur y passe aussi par une variable, sauf ±1 px. Il a trouvé deux cas, corrigés :
  - la place de la barre « Postuler » du téléphone (5,5 rem, quatre fois) devient `--dock-h`, une taille comme `--tabbar-h`, ajoutée à Figma ;
  - le centrage du bouton « ⋯ » d'une candidature comptait encore 2,25 rem, sa taille d'avant : il compte `--control-h`, sa taille réelle ; le bouton remonte de 2 px, aligné sur la ligne du titre.

## Vérifié (1.6.13)

- 111 fichiers de tests sur 111, 458 tests ; le rapporteur fait échouer une suite incomplète ; lint, vue-tsc.

## Écarts (1.6.15)

Décisions du 24 octobre, prises en revoyant le premier lot de composants Figma (carte, initiales, progression ORP, semaine, visage du 1). Le numéro 1.6.14 était déjà pris par la CI.

- **L'anneau d'aujourd'hui** passe de `--accent-soft` (1,2:1) à `--accent` : c'est le seul repère du jour dans la semaine.
- **Les jours vides et les cases ORP à faire** passent en `--faint` (3,3:1 au moins) ; la case vide mêlait `--muted` à 22 % (une valeur calculée, sans variable). La bordure des cartes reste telle quelle : elle est décorative, le contenu délimite la carte.
- **Le visage de la tuile du mois ORP** passe de 40 à 32 px (la règle §4 : 16 à 32 px dans l'usage courant) ; la tuile garde sa taille.
- **Les initiales sur menthe et ciel** n'ont plus de couleur en dur : `--text` en clair, `--on-accent` en sombre (tous deux foncés, 10 à 11:1).
- Figma suit : Case ORP, Jour (et donc Semaine), Visage du 1 (taille 32 au lieu de 40), Initiales.
- **Relevé au passage, non traité** : les fonds de la tuile du visage (`.face-tile`) sont des couleurs en dur, sans variable (vert, lavande, beige, gris, et un orange pour « à agir »).

## Vérifié (1.6.15)
- Avant / après : changent Aujourd'hui (la semaine, les cases du mois ORP), et en sombre les pages avec des initiales menthe ou ciel (encre #11111f → #0f0f1a, imperceptible).
- 458 tests de l'interface (111 fichiers sur 111), lint, vue-tsc ; les 3 tests de l'audit ; les trois audits à zéro sur la démo et un compte neuf, l'accessibilité aussi en sombre.

## Écarts (1.6.16)

Décisions du 24 octobre sur le second lot de composants Figma.

- **Les points « à faire » des premiers pas** passent en `--faint` (le bord était à 1,2:1).
- **La tuile du visage** (`.face-tile`, le mois ORP et les premiers pas) n'a plus de couleur en dur : ravi `--mint-soft` (nouvelle variable : #a8e6d2 en clair, la valeur d'avant ; #253f49 en sombre), content `--accent-soft`, attentif et neutre `--border` (le beige est retiré ; `--band` aurait rendu la tuile presque invisible sur une carte blanche, 1,07:1), à agir `--orange-soft` (l'orange de l'action, règles §4). Le visage passe à `--text` : **en sombre, la tuile devient foncée et le visage clair** (avant, elle restait pastel). Un test vérifie le visage sur chaque fond (3:1 au moins ; de 9,9 à 17:1).
- **L'étiquette en majuscules** : l'espacement de 7 % servait à « Premiers pas · 2 sur 5 » et à « Cette semaine » ; il devient la variable `--letter-label`, et le style de texte `jobA1/etiquette` dans Figma. D'autres étiquettes en majuscules du même rôle gardent 4 à 8 % (`.points h3`, `.facts dt`, `.wizard-step`, `.contacts-block h3`, `.assistant-label`, `.news-group-title`, `.page-head-eyebrow`, `.welcome-label`…) : à unifier si tu le décides.
- **L'ombre du toast** devient le style d'effet `jobA1/ombre-toast` dans Figma (0 8 24, #11111f à 10 %), appliqué à l'Annulation.
- Figma : la variable `mint-soft`, la Tuile du visage (cinq humeurs × deux thèmes) utilisée dans les Premiers pas, leurs points à faire en `--faint`, leur compte au style `jobA1/etiquette`.

## Vérifié (1.6.16)

- Captures avant/après (horloge figée) : seules changent Aujourd'hui (la tuile du visage, les
  points et le compte des premiers pas), et connexion et inscription, qui y redirigent une fois
  connecté. Réglages › Compte (1440, clair) différait dans la série : l'en-tête collant pris au
  milieu de l'image ; prise seule, la page est identique à l'avant.
- 459 tests (111 fichiers), dont le contraste du visage sur chaque fond de tuile en clair et en
  sombre ; lint, types et test de l'audit propres.
- Trois audits à zéro sur la démo et sur un compte neuf, l'accessibilité aussi en sombre.

## Écarts (1.6.17)

Retours sur l'écran de référence Aujourd'hui dans Figma (24 octobre).

- **La date au-dessus du titre reste**, en style étiquette (`--letter-label` au lieu de 0,06 em) : ce n'est pas
  un sous-titre. L'exception est écrite à la §3 des règles et dans `docs/interface.md`.
- **L'action d'un écran vide est un bouton principal plein** (règles §3.3 et §4) : Aujourd'hui (« Voir les offres
  quand même », désormais dans l'écran vide, avant le mois ORP, comme dans Figma), Candidatures, Bilan,
  rendez-vous ORP, Offres (« Créer mes alertes » ; « Effacer les filtres » quand rien ne correspond),
  Actualités (« Gérer les sources »). Une seconde action reste en contour (« Ajouter une offre »).
- **La devise « Less searching. More living. » quitte l'interface** (anglais, règles §5) : Aujourd'hui,
  connexion et inscription (la phrase d'accroche reste, aussi sur téléphone), À propos, Découvrir (le titre
  reprend la phrase guide des règles §1) et la description de l'application installée. Le README et le
  paquet Python la gardent : ce n'est pas l'interface.
- **Figma** : la date en style etiquette sur l'écran Aujourd'hui ; l'Écran vide prend le Bouton principal.

## Vérifié (1.6.17)

- Captures avant/après (horloge figée) : changent Aujourd'hui (l'étiquette, l'écran vide), À propos,
  Découvrir, connexion et inscription (qui redirigent vers Aujourd'hui une fois connecté), et, sur un compte
  neuf, les écrans vides de Bilan, Offres, Suivi et rendez-vous ORP (le bouton plein). Profil (1440, sombre)
  différait d'une ligne de 3 px dans un champ : un artefact de capture.
- 459 tests, dont l'action en bouton plein de l'écran vide d'Aujourd'hui et d'Offres, et l'absence de la
  devise ; lint, types et test de l'audit propres.
- Trois audits sans défaut grave, sur la démo et sur un compte neuf, l'accessibilité aussi en sombre. Les
  deux défauts mineurs de la démo (ordre des titres dans Bilan › Entretiens) précèdent cette version.

## Écarts (1.6.18)

Retours sur l'écran de référence Candidatures dans Figma (24 octobre).

- **Offres, la conclusion en une phrase** (règles §3.2) : « 4 offres à examiner. », en haut de la page, le
  compte en accent comme sur Aujourd'hui ; la fin suit le statut regardé (« 1 offre écartée. », « Aucune
  offre à examiner. »). Elle remplace « 4 offres » au-dessus de la liste.
- **Au plus une action principale** (règles §3) : aucune quand l'écran se parcourt, comme la liste des offres.
- **Liste vide d'un compte neuf** : « Ajouter une offre » seulement dans l'écran vide, plus au-dessus de la liste.
- **Blocs de chargement** sous le voile, pour la liste des offres (trois de 4,5 rem), comme Aujourd'hui.
- **La pastille de la cloche en orange** (règles §4, annexe de l'audit) : fond `--orange`, chiffre `--text`
  (6,98:1), `--on-accent` en sombre (7,11:1) ; plus de rouge. Les comptes des onglets restent en `--accent`.
- **Une offre sélectionnée** : le voile passe de 7 à 5 % d'accent ; `--muted` y fait 4,58:1 en clair (4,46
  avant, sous le seuil de 4,5:1). Le filet de 3 px marque toujours la sélection.
- **Figma** : Cloche et Pastille orange à chiffre foncé, comptes des onglets en accent, Carte d'offre
  sélectionnée à 5 %, l'écran Candidatures sans « Ajouter une offre » au-dessus d'une liste vide.

## Vérifié (1.6.18)

- Captures avant/après (horloge figée) : sur la démo, 192 captures changent, toutes à la seule pastille de la
  cloche (en orange sur chaque page), sauf Offres et le détail d'une offre (la phrase de conclusion, la sélection).
  Sur un compte neuf, seule Offres change (la phrase, « Ajouter une offre » dans l'écran vide seulement ; sur
  téléphone, « Candidature spontanée » prend toute la largeur, vérifié à part).
- 462 tests, dont la phrase selon le statut, « Ajouter une offre » seul dans l'écran vide, le contraste de la
  pastille et de l'offre sélectionnée ; lint, types et test de l'audit propres.
- Trois audits sans défaut grave, démo et compte neuf, l'accessibilité aussi en sombre (les deux défauts
  mineurs de Bilan › Entretiens précèdent cette version).

## Écarts (1.6.19)

Retours sur l'écran de référence Bilan dans Figma (24 octobre) ; l'annexe de l'audit (« Suivi et Bilan trop
chargés ») pour Bilan.

- **La conclusion en haut** (règles §3.2) : la phrase de ce qui marche passe avant le choix de la période.
- **Le détail replié** (règles §3.4) : une ligne repliable par vue (Parcours, Par mois ou Par semaine, Ce qui
  marche, Semaines, Entretiens, Pour l'ORP), toutes fermées, à la place du sélecteur, qui faisait un troisième
  niveau d'onglets (§2). La vue n'est plus retenue sur l'appareil ; dans une ligne, elle perd son cadre et son
  titre, que la ligne porte.
- **Les tuiles, jamais de libellé coupé** : deux tuiles par ligne sur téléphone ; trop long, le nom passe sous
  la bulle, et la précision sur plusieurs lignes. Le chiffre reste en 700 (style Figma jobA1/font-page-bold).
- **L'audit des règles** ne compte plus un texte rogné par un conteneur qui défile : sur téléphone, la suite
  du détail d'une offre (une fiche fixée) passait pour « collée » à une ligne de la liste dessous, depuis la
  1.6.18 (la phrase de conclusion avait décalé la liste). Deux tests de plus dans `test_regles.py`.

## Vérifié (1.6.19)

- Captures avant/après (horloge figée) : seule Bilan change sur la démo (24 captures), rien sur un compte neuf.
- Bilan, Figma et code côte à côte en 390 et 1440 px : `docs/captures/1.6.19/`. Écart restant : le titre d'une
  ligne repliable fermée est en 400 dans le code (DisclosureRow, partout), en 600 dans Figma ; à trancher.
- 463 tests, lint, types ; 5 tests de l'audit (dont les 2 nouveaux) ; trois audits sans défaut, démo et compte
  neuf, l'accessibilité aussi en sombre (plus aucun défaut mineur).

## Écarts (1.6.20)

Retours du 24 octobre sur l'écran de référence Suivi dans Figma ; l'annexe de l'audit (« Suivi et Bilan trop
chargés ») pour le Suivi.

- **La conclusion en haut** (règles §3.2) : « 6 relances à faire et 4 candidatures à déclarer. », les nombres
  en accent ; « Rien à relancer ni à déclarer. » quand tout est fait.
- **Une ligne pour le mois** : le mois, l'objectif en cases (une par candidature, règles §4, comme sur
  Aujourd'hui ; au-delà de 15, une barre continue), « Ajouter » et le « ⋯ ». Sur téléphone, trois lignes.
- **« À faire » d'abord**, aussi sur téléphone : une carte avec les onglets À relancer et À déclarer, trois
  lignes au plus, « Tout voir » pour le reste (§3). Sur téléphone, l'action passe sous le texte : le nom de
  l'entreprise n'est jamais coupé.
- **Le détail replié** (règles §3.4) : « Calendrier d'octobre » et « Toutes les candidatures d'octobre », deux
  lignes repliables à la place du sélecteur « Calendrier · Liste » (§2). Le jour choisi s'affiche sous le
  calendrier ; un lien vers un jour (« fais le point », assistant) ouvre le calendrier. L'affichage n'est plus
  retenu sur l'appareil, et la colonne défilante à côté du calendrier disparaît.
- **La liste du mois sur téléphone** : la date, l'entreprise (sur deux lignes au besoin) et le statut ; le poste,
  le mode et le « ⋯ » sont dans le panneau qu'ouvre le nom. La colonne d'actions a un nom pour les lecteurs
  d'écran (axe : en-tête de tableau vide).
- **Le titre des repliables en 600**, ouvert ou fermé, partout (comme le composant Repliable de Figma).
- **Les statuts** : « Refus » passe en gris `--muted` (un refus n'est pas une erreur, §4) ; « Sans réponse » en
  `--faint` au lieu de `#c4c8d2` en dur, toujours avec son mot. Figma suit (Point de statut).


## Vérifié (1.6.20)

- Captures avant/après (horloge figée) : le Suivi change ; ailleurs, seul le titre des repliables fermés passe
  en 600 (Bilan, Alertes, Rendez-vous ORP, Profil, Réglages).
- Suivi, Figma et code côte à côte en 1440 px et en 390 px (calendrier ouvert) : `docs/captures/1.6.20/`.
  Écart restant : la légende du code a « à compléter », pas Figma. (Le nom coupé de « À faire » sur
  téléphone est corrigé dans Figma le 25/10 : Ligne de liste, format Téléphone.)
- 468 tests, lint, types ; 5 tests de l'audit ; trois audits sans défaut, démo et compte neuf, l'accessibilité
  aussi en sombre (plus aucun défaut mineur).

## Écarts (1.6.21)

Retours du 24 octobre sur l'écran de référence Détail d'une offre dans Figma.

- **« ← Offres » en haut à gauche** (règles §2), au-dessus du logo et du titre, sur téléphone ; il était en
  haut à droite, à côté du « ⋯ ». Sur ordinateur, rien ne change (la croix sur écran moyen).
- **L'entreprise et l'annonce repliées** (règles §3.4) : deux lignes repliables, moins utiles pour décider ; le
  résumé donne le nom de l'entreprise et le site de l'annonce. Le « ⋯ » de chaque partie passe sur la ligne
  ouverte (comme en docs/119), à la marge du texte.

## Vérifié (1.6.21)

- Captures avant/après (horloge figée) : seul le détail d'une offre change sur la démo (10 captures), rien
  sur un compte neuf.
- Figma et code côte à côte en 1440 et 390 px : `docs/captures/1.6.21/`. Le titre des lignes est en 400
  ici ; il passe en 600 avec la 1.6.20. Écarts déjà là avant cette version : au-dessus de la liste, le code
  montre « Ajouter une offre », « Candidature spontanée » et le filtre Note, que Figma n'a pas.
- 463 tests, lint, types ; 5 tests de l'audit ; trois audits sans défaut, démo et compte neuf, l'accessibilité
  aussi en sombre.

## Écarts (1.6.22)

Retours du 25 octobre sur l'écran de référence Alertes dans Figma.

- **La conclusion en haut** (règles §3.2) : « 2 recherches suivies, la dernière alerte reçue le 22 octobre. »,
  le nombre en accent ; « aucune alerte reçue pour l'instant » tant que rien n'est arrivé. La carte prend le
  titre « Les alertes », avec « Gérer mes alertes » ; l'assistant d'un compte neuf garde son titre et son
  illustration.
- **Le détail** : un titre au-dessus des lignes repliables (les e-mails des sites, le journal), serrées comme
  sur Suivi et Bilan.
- **Des blocs de chargement** (règles §6) : la page n'affichait rien tant qu'elle chargeait.
- **« Rien reçu depuis 24 heures »** : le point en `--orange` au lieu de `#e08a2e` en dur.
- **La doc de la 1.6.20** (ligne du README, écarts et vérifications ci-dessus) est rétablie : elle s'était
  perdue dans la fusion de la 1.6.21.


## Vérifié (1.6.22)

- Captures avant/après (horloge figée) : seule la page Alertes change, démo et compte neuf (12 captures chacun).
- Figma et code côte à côte : `docs/captures/1.6.22/` (démo en 1440 et 390 px, premiers pas en 1440 px).
  Écart restant : sur téléphone, le résumé « aucun code en attente » de la ligne repliable est coupé dans le
  code (points de suspension), sur deux lignes dans Figma ; il l'était déjà avant.
- 471 tests, lint, types ; 5 tests de l'audit ; trois audits sans défaut, démo et compte neuf, l'accessibilité
  aussi en sombre.

## Écarts (1.6.23)

Retours du 25 octobre sur l'écran de référence Rendez-vous dans Figma.

- **La conclusion en haut** (règles §3.2) : « Prochain rendez-vous mardi 27 octobre à 09:30, ORP de Lausanne. »,
  la date et l'heure en accent ; « Préparer » en lien à droite (dessous sur téléphone), qui descend à la
  préparation, et le « ⋯ » du rendez-vous à côté. Elle remplace la carte « Le prochain rendez-vous » ; la carte
  reste pour saisir la date, la modifier, ou noter ce qui a été convenu après le rendez-vous.
- **Une obligation en retard** (échéance passée, pas faite) rejoint la phrase, en `--orange-text` : « En retard :
  preuves de septembre, à remettre au plus tard le 5 octobre. » ; « Obligations et échéances » la compte.
- **La feuille sur une colonne** : le nom, puis « Télécharger la feuille (PDF) » en bouton plein et « Rédiger avec
  l'IA » en contour ; le message rédigé dessous.
- **Le mois replié** (règles §3.4) : une ligne repliable par partie, avec son résumé (en bref, ce qui bloque, les
  compétences qui manquent, les obligations, le carnet) ; « Le mois en bref » ouvert.
- **Premier rendez-vous** : « Enregistrer » en bouton plein (§3.3) ; « Voir les offres » devient un lien dans
  l'écran vide.
- **L'interrupteur** : la piste non cochée en `--faint` (3,6:1 sur la carte) au lieu de `--border` (1,2:1),
  partout dans l'application (WCAG 1.4.11).
- **Sans candidature**, une échéance passée (les preuves d'un mois vide) n'est pas une alerte : rien en orange.

## Vérifié (1.6.23)

- Captures avant/après (horloge figée) : la page Rendez-vous change ; ailleurs, seule la piste des interrupteurs
  non cochés (Réglages, Profil, Bilan, Suivi).
- Figma et code côte à côte : `docs/captures/1.6.23/` (démo en 1440 et 390 px, compte neuf en 1440 px).
  Écarts restants : le compte neuf garde le titre « Préparer » au-dessus du formulaire ; « Ce qui bloque » n'a pas
  de résumé quand il n'y a que « ce qui marche » ; le champ du nom est plus étroit (28 rem) que dans Figma.
- 476 tests, lint, types ; 5 tests de l'audit ; trois audits sans défaut, démo et compte neuf, l'accessibilité
  aussi en sombre.

## Écarts (1.6.24)

Le nettoyage de fin de série (25 octobre).

- **L'historique des versions** quitte le README pour `CHANGELOG.md` : chaque PR ajoutait sa ligne au même endroit
  du README, d'où un conflit à chaque fusion. Le README garde un lien ; la ligne « Version en cours » ne porte plus
  de numéro.
- **Le résumé d'une ligne repliable n'est plus jamais coupé** : trop long, il passe à la ligne, aligné à droite
  (« aucun code en attente » dans Alertes sur téléphone ; toutes les lignes repliables de l'application).
- **Rendez-vous, compte neuf** : plus de titre « Préparer » au-dessus du seul formulaire du rendez-vous.
- **« Ce qui bloque »** compte aussi « ce qui marche » dans son résumé (« 1 piste »).
- **La feuille** : le champ du nom sur toute la largeur de la carte, comme dans Figma.
- **Le bilan du cadrage** (§9) : ce qui est fait, les composants, les exceptions voulues, ce qui reste.

## Vérifié (1.6.24)

- Captures avant/après (horloge figée) : changent seulement Alertes, le détail d'une offre, Rendez-vous et Profil ›
  Coordonnées, là où un résumé de ligne repliable était coupé ; il passe à la ligne entre deux mots (un premier
  essai coupait « facultatif » au milieu du mot : corrigé, avec un garde-fou).
- 478 tests, lint, types ; 5 tests de l'audit ; trois audits sans défaut, démo et compte neuf, l'accessibilité
  aussi en sombre.

## Écarts (1.6.25)

Décision du 25 octobre : les Actualités quittent l'interface ; le code serveur reste, en attendant ta décision.

- **Bilan** : deux onglets, Résultats et Formations ; plus d'onglet Actualités ni de pastille des nouveautés (le
  compteur n'interroge plus le serveur). Figma suit : l'onglet est retiré des 16 cadres de l'écran Bilan.
- **Réglages** : la rubrique « Actualités » (mots-clés et sources) est retirée ; « Mon domaine » reste modifiable
  dans Bilan › Formations, qui s'en sert aussi.
- **Les liens** : `/actualites`, `/bilan/actualites`, `/progresser` et `/progresser/actualites` mènent au Bilan ;
  l'assistant ne transforme plus ces adresses en liens.
- **Les textes** : « La plateforme » et l'accueil ne promettent plus que les formations du domaine (la maquette de
  « La plateforme » montre Bilan › Formations) ; un profil d'essai ne règle plus que les Formations.
- **Retirés de l'interface** : `NewsView`, `NewsStory`, `NewsCatalog`, `NewsSourcesPanel`, `useNewsCount` et leurs
  tests ; les audits ne visitent plus la page ni la rubrique. Les styles des Actualités restent dans `style.css` :
  une partie (`news-filters`, `news-status`, `news-group-title`) sert aussi Formations.
- **Les onglets sur téléphone** se partagent la largeur, comme dans Figma : à deux, ceux du Bilan restaient serrés à
  gauche. Candidatures en profite aussi (quatre onglets de même largeur).

### Inutilisé côté serveur, à décider

- **L'API** `/api/news` : 11 routes sur 13 n'ont plus d'appelant (`listNews`, `refreshNews`, `markNewsSeen`,
  `getNewsImage`, `listNewsSources`, `addNewsSource`, `getNewsCatalog`, `addNewsCatalogSource`, `addNewsSearch`,
  `updateNewsSource`, `deleteNewsSource`). Restent utilisées : `getNewsPreferences` et `saveNewsPreferences`
  (« Mon domaine », lu et écrit par Formations).
- **Le relevé** : la tâche `news` du worker (`worker/tasks/news.py`, `news/service.fetch_news`) continue de relever
  les sources et d'écrire `news_items` (et les images dans le stockage, dossier `news/`) sans que personne ne les
  lise.
- **Les tables** `news_sources` et `news_items` (migrations 0023 à 0025, 0027, 0054, 0064), leurs politiques
  d'accès (`db/policies.py`) et leurs données de démonstration (`demo/seed.py`).
- **L'accueil** (`welcome.py`) crée encore les sources de la famille de métiers choisie (docs/116 §4) ; les profils
  d'essai (`profiles/service.py`) aussi, depuis le catalogue (`news/catalog.json`).
- **L'assistant** : l'outil `actualites` (`assistant/tools.py`) et la partie « Bilan › Actualités » de son texte
  (`llm/prompts/assistant-v20.md`, qui cite encore `/bilan/actualites`).
- **À garder** si Formations reste : `news/domain` (les mots du domaine, lus par `trainings/service.py`) et
  `news/trades` (les familles de métiers, lues par l'accueil).

## Vérifié (1.6.25)

- Captures avant/après (horloge figée) : la page Actualités et la rubrique des Réglages disparaissent (12 captures
  de moins) ; changent le Bilan et Formations (les onglets), Candidatures sur téléphone (les onglets), les Réglages
  (le sommaire), l'accueil et « La plateforme » (les textes et la maquette).
- Bilan, Figma et code côte à côte en 1440 et 390 px : `docs/captures/1.6.25/`.
- 463 tests (les tests de la vue retirée en moins, celui des onglets du Bilan en plus), lint, types ; 5 tests de
  l'audit ; trois audits sans défaut, démo et compte neuf, l'accessibilité aussi en sombre.

## Écarts (1.6.26)

Une version de clarté, sans changer la structure (25 octobre).

- **Aujourd'hui, jour de repos** : une seule phrase en haut, qui dit quoi faire si l'on veut avancer (« Jour de
  repos. Si tu veux avancer : 7 relances en attente. », sinon les offres à examiner). La carte « Offres du jour »
  disparaît ce jour-là et la semaine du mois ORP ne le répète plus. Figma : un état « Jour de repos ».
- **Sans jargon** :
  - « Jour sans recherche » → « Jour de repos » (la phrase du jour, la semaine, le nom d'un jour pour les lecteurs
    d'écran) ;
  - « On rattrape » → « En retard de N candidatures », N l'écart avec le rythme attendu du mois ;
  - « Note de l'IA » → « Proximité avec ton profil » (le nom de la note d'une offre pour les lecteurs d'écran, le
    titre de la comparaison dans Bilan › Ce qui marche, côté serveur).
- **Les tuiles du Bilan** : le chiffre d'abord, puis sa précision en une phrase (« 26 · candidatures, sur 33 offres
  gardées », « 12 j · délai de réponse, d'habitude ») ; le nom ne flotte plus à côté de la bulle. Figma : la Tuile de
  chiffre perd sa propriété « Libellé », la précision porte la phrase (44 instances mises à jour).
- **« Filtrer »** en toutes lettres à côté de l'entonnoir (Offres et Formations sur téléphone), le nombre de filtres
  actifs en pastille. Figma : une Pilule « Filtrer » à la place du bouton icône.
- **Non changé** : le texte de l'assistant (`llm/prompts/assistant-v20.md`) parle encore de « jour sans
  recherche » ; il change avec la prochaine version du texte de l'assistant.

## Vérifié (1.6.26)

- Captures avant/après (horloge figée) : changent le Bilan (les tuiles), Offres et Formations sur téléphone
  (« Filtrer »). Le jour de repos et le retard sur le mois n'apparaissent pas dans la démo (un jeudi de recherche,
  dans les temps) : ils sont couverts par les tests (Aujourd'hui, la semaine, le mois ORP) et par l'état Figma.
- Bilan, Figma et code côte à côte en 1440 et 390 px : `docs/captures/1.6.26/`.
- 463 tests, lint, types ; 5 tests de l'audit ; trois audits sans défaut, démo et compte neuf, l'accessibilité
  aussi en sombre.

## Écarts (1.6.27)

Revue de l'interface sur ordinateur (25 octobre). Réglages n'avait pas d'écran Figma : il est créé d'abord (2 états,
« Recherche d'emploi » et « Agenda et extension », en vue exploitant, 1440 et 390 px, clair et sombre), avec le lot 9
(Entrée de sommaire, Marqueur de rubrique ; icônes spark, shield, plug, activity).

1. **Suivi** : « Sans réponse depuis N jours » dit le vrai nombre de jours depuis l'envoi (c'était toujours 10), sur la
   ligne et dans le panneau d'une candidature.
2. **Le bouton « Assistant »** ne cache plus rien : sur ordinateur, le pied de page réserve sa place en bas de chaque
   page (vérifié en simulant le bouton, absent de la démo : plus rien dessous en bas de page).
3. **Suivi** : plus de sélecteur « À relancer / À déclarer » (un troisième niveau d'onglets, §2) ; deux listes l'une
   sous l'autre, trois lignes chacune et « Tout voir ». Figma suit.
4. **Bilan › Semaines** : « en dessous » en gris neutre (`--band`, `--muted`) ; l'orange est pour ce qui demande d'agir (§4).
5. **Réglages sans jargon** (§5), décision du 25/10 : « Outils » → « Agenda et extension », « Plateforme » →
   « Administration », « Diagnostic » → « État du service » (la page et son lien) ; le nom du modèle d'IA disparaît
   (« Active : elle note les offres. »).
6. **Offres** : la pastille de l'onglet compte les offres à examiner ; dans une autre vue, la phrase le redit
   (« 27 offres en cours · 4 à examiner. »).
7. **Mineur** : « Postuler chez l'employeur » (un lien en bouton) prend le bord `--faint` des autres boutons
   secondaires (il avait `--border`, très pâle) ; « Semaine faite » et « Ta semaine est faite » se taisent quand le mois
   ORP est en retard.

- **Relevé en passant, corrigé** : la 1.6.26 avait renommé le titre de la comparaison du Bilan en « Proximité avec ton
  profil » ; un titre ne porte pas de pronom (règles des titres, audit) et l'audit de la 1.6.26 tournait sur l'ancienne
  API de démo, qui n'avait pas été redémarrée. Le titre devient « Proximité avec le profil » ; « Proximité avec ton
  profil » reste le nom de la note d'une offre pour les lecteurs d'écran.
- **À trancher** : « Chercher l'annonce chez l'employeur à partir de » est dans « Agenda et extension » sans en être ;
  proposition : le déplacer dans « Recherche d'emploi ».

## Vérifié (1.6.27)

- Captures avant/après (horloge figée) : changent le Suivi (deux listes, les jours), le Bilan (les semaines), les
  Réglages (les noms), et les liens en bouton (Offres d'un compte neuf, page introuvable, détail d'une offre : le bord).
  Les états du sélecteur du Suivi disparaissent des captures (8 de moins).
- Figma et code côte à côte en 1440 px : `docs/captures/1.6.27/` (Suivi ; Réglages, la démo n'a pas les rubriques de
  l'exploitant). Petits écarts : les lignes repliables de la rubrique sont encadrées dans Figma, et les étapes de
  l'extension y sont rédigées en une phrase.
- 465 tests, lint, types ; 5 tests de l'audit ; tests serveur du Bilan ; trois audits sans défaut, démo (API redémarrée)
  et compte neuf, l'accessibilité aussi en sombre.

## Écarts (1.6.28)

- **« Chercher l'annonce chez l'employeur à partir de »** revient dans « Recherche d'emploi », après les sites suivis
  (décision du 25/10) ; il était dans « Agenda et extension » sans en être. Il en était parti en docs/131 §C.13, comme
  réglage d'expert ; la rubrique s'appelait alors « Outils ». Il s'enregistre toujours au changement. Figma suit.

## Vérifié (1.6.28)

- Captures avant/après (horloge figée) : seules les pages des Réglages changent (sur téléphone, toutes les rubriques
  sont sur la même page).
- Réglages, Figma et code côte à côte en 1440 px : `docs/captures/1.6.28/`.
- 466 tests (un de plus : l'emplacement du réglage), lint, types ; 5 tests de l'audit ; trois audits sans défaut, démo et
  compte neuf, l'accessibilité aussi en sombre.


## Écarts (1.6.29)

Revue de la largeur sur ordinateur (25 octobre). Ordre suivi : les règles (`docs/regles-ui-ergonomie.md` §3, « Largeurs,
sur ordinateur »), puis Figma (validé le 25/10), puis le code. Le téléphone ne change pas : tout ce qui touche la mise
en page est sous `@media (min-width: 821px)`, au-dessus du point de rupture déjà utilisé (820 px).

Références : GOV.UK Layout (page de 1 020 px, colonne des deux tiers, 75 caractères par ligne) ; GOV.UK Text input
(champs à la taille du contenu prévu, en caractères) ; NHS Design System (boutons pleine largeur seulement sur
téléphone) ; WCAG 2.2, 1.4.8 (AAA visé : 80 caractères au plus) ; Laws of UX, lois de proximité et de Fitts.

> Revu en 1.6.32 (`docs/regles-ui-ergonomie.md` §3 et §9) : GOV.UK et NHS ne sont plus des références. La colonne
> des deux tiers et les boutons pleine largeur sur téléphone sont supprimés ; un seul conteneur de 1 020 px, chaque
> bloc sur toute sa largeur (choix de jobA1, compatible avec la largeur large de Polaris) ; boutons à la largeur de
> leur texte partout (Material Design 3), 44 px de haut sur téléphone. Restent : 75 caractères et champs à la taille
> du contenu (Baymard). Planches : `docs/captures/1.6.32/`.

1. **Les variables** (`style.css`, `:root`) : `--page-max` 1 020 px, `--page-wide` 80 rem (1 280 px, remplace
   `--page-width`), `--column-two-thirds` 680 px, `--measure` 31 em, `--field-20` 13 rem, `--field-30` 18 rem,
   `--field-5` 5,5 rem, `--header-max` 84 rem (le bandeau du haut, inchangé). Les mêmes dans Figma (collection Tailles).
2. **La page à 1 020 px** (GOV.UK Layout) : `.container`, l'en-tête et le corps de Candidatures, les Réglages.
   **Exception, Candidatures › Offres à 1 280 px** : trois colonnes (filtres, liste, détail) ; à 1 020 px, la liste
   et le détail n'auraient que 338 px chacun. L'en-tête de Candidatures suit l'onglet (`.jobs-head.wide`).
3. **75 caractères par ligne** (GOV.UK, WCAG 1.4.8) : `p`, `dd` et trois listes de phrases (questions au conseiller,
   étapes de l'agenda, sites proposés) ont `max-width: var(--measure)` ; les phrases de conclusion aussi (elles
   avaient 40 rem). La mesure vaut 31 em : avec 75 ch ou 37,5 em, des lignes de petit texte gardaient 76 à 89
   caractères (un « ch » est plus large que la lettre moyenne). Figma suit (496 px au lieu de 600). Un encadré garde
   sa largeur : le bandeau du Bilan (seule sa phrase suit la mesure), les avis, le pied d'une carte des Réglages (sa
   marge de droite limite le texte, son filet reste entier).
4. **Les boutons à la largeur de leur texte** (NHS, Fitts) : « Écarter » et « Garder » de l'offre du jour ; « J'attends
   un code » dans les e-mails des sites. Toute la largeur reste sur téléphone.
5. **Les champs à la taille du contenu** (GOV.UK Text input) : Rendez-vous, le nom sur la feuille à 20 caractères ; le
   premier rendez-vous, date et heure à leur taille naturelle, lieu à 30, conseiller à 20 ; les nombres (objectif, jour
   du mois, note sur 100) à 5. La question au conseiller reste fluide (une phrase libre).
6. **Le statut et l'action près du nom** (loi de proximité) : à relancer et à déclarer (Suivi), les alertes (Alertes)
   dans la colonne des deux tiers ; Bilan › Semaines, la plage, le compte et l'état groupés à gauche et alignés d'une
   ligne à l'autre (sous-grille) ; Aujourd'hui › Mois ORP, les 7 jours groupés sous « Cette semaine ».

- **Relevé en passant, corrigé** : la page plus étroite fait passer les étiquettes d'une formation sur deux lignes ; le
  marque-page se centrait alors 6 px plus bas que ses voisins (audit d'alignement). Il reste en haut de la tuile.
- **Outil** : `captures.py` prend aussi d'autres largeurs (`CAPTURES_WIDTHS=1440,1920,390`).

## Vérifié (1.6.29)

- Captures avant/après (horloge figée) en **1440, 1920 et 390 px, clair et sombre** : 496 captures, démo et compte neuf.
  Changent : 156 captures de la démo, 112 du compte neuf, toutes en 1440 et 1920. **En 390 px, aucune capture ne
  change** (192 sur 192 identiques).
- **75 caractères** : chaque ligne de chaque paragraphe comptée sur toutes les pages, en 1440 et 1920, démo et compte
  neuf : avant, 12 paragraphes allaient jusqu'à 121 caractères ; après, aucun ne dépasse 75.
- Figma et code côte à côte en 1440 px, avant/après en 1920 px clair et en 1440 px sombre : `docs/captures/1.6.29/`.
- 468 tests (deux de plus : le garde-fou des largeurs, l'en-tête de Candidatures), lint, types ; 5 tests de l'audit ;
  trois audits sans défaut, démo et compte neuf, l'accessibilité aussi en sombre.

## Écarts (1.6.30)

Correction de la 1.6.29 (revue du 25/10) : la colonne des deux tiers ne tenait que les listes, sous un mois et un
bandeau pleine largeur ; deux largeurs l'une sous l'autre. Une proposition « deux tiers et un tiers » (le mois dans le
tiers de droite) n'a pas été retenue : l'objectif ORP et les preuves sont du contenu principal (§1), et GOV.UK Layout
réserve le tiers de droite au contenu secondaire. Règle retenue (`docs/regles-ui-ergonomie.md` §3), Figma d'abord.

1. **Une seule colonne des deux tiers** (GOV.UK Layout ; Nielsen Norman Group, lecture par la gauche) : Suivi, Alertes
   (le résumé) et Rendez-vous ont tout leur contenu dans `--column-two-thirds`, alignée à gauche avec le titre et les
   onglets, de haut en bas ; le tiers de droite reste vide. `--column-two-thirds` vaut 648 px : les deux tiers du
   contenu (972 px). Classe `.two-thirds` sur la page, sur ordinateur seulement.
2. **Suivi, dans l'ordre (§1)** : la conclusion, le mois (navigation, objectif, « Ajouter », ⋯, sur une ligne), les
   preuves, à relancer, à déclarer, le détail. **Exception** : le calendrier ouvert prend la largeur de la page (une
   grille de 7 colonnes).
3. **Alertes** : la conclusion, les alertes, le détail. Premiers pas (l'assistant) et « Gérer mes alertes » gardent la
   pleine largeur.
4. **Rendez-vous** : tout dans la colonne ; les champs du premier rendez-vous passent à la ligne (date, lieu ; puis
   conseiller), à leurs largeurs de la 1.6.29. Dans la phrase, « à » et l'heure ne se séparent plus (espace insécable).
5. **Jamais de « … »** dans une ligne de liste sur ordinateur (« … · envo… ») : le nom et les lignes passent à la ligne
   (Suivi, Aujourd'hui, à relancer). Figma suit : le composant Ligne de liste, variantes Ordinateur.
6. **Bilan, Figma** : la phrase du bandeau s'arrête à la mesure et passe sur deux lignes, comme dans le code (composant
   Conclusion mise en avant, largeur max 496 px : Figma ne lie pas une largeur max de texte à une variable).

- **Reste sur téléphone** : les lignes de liste y gardent leur « … » (le 390 px ne devait pas changer). À trancher.

## Vérifié (1.6.30)

- Captures avant/après (horloge figée) en **1440, 1920 et 390 px, clair et sombre** : changent le Suivi, les Alertes et
  le Rendez-vous (et leurs états), en 1440 et 1920 seulement ; **en 390 px, aucune capture ne change**. Deux écarts
  en 1920 sans rapport (une capture « avant » prise pendant un défilement, un pixel d'animation de « La plateforme »).
- 75 caractères : aucune ligne au-delà, sur toutes les pages, en 1440 et 1920, démo et compte neuf.
- Figma et code côte à côte en 1440 px, avant/après en 1920 et en sombre : `docs/captures/1.6.30/`. La démo n'a pas de
  ligne à compléter : le bandeau des preuves n'y paraît pas (il garde sa place, sous le mois, quand il paraît).
- 468 tests, lint, types ; 5 tests de l'audit ; trois audits sans défaut, démo et compte neuf, l'accessibilité aussi en
  sombre. **Relevé en passant, corrigé** : deux tests comptaient « hier » comme « maintenant moins 24 h » et ont échoué
  le soir du changement d'heure (25 octobre, en local et sur la CI en UTC) : celui des jours d'Offres fige maintenant
  son horloge en milieu de journée ; celui du rendez-vous tenu (serveur) prend la veille à 10 h, heure locale.

## Écarts (1.6.35)

Suite de la revue des références (25/10) : ce que les 1.6.31 et 1.6.32 n'avaient pas encore repris de Material
Design 3 et de Polaris (`docs/regles-ui-ergonomie.md` §3). Figma d'abord (planches 1440 et 1920), puis le code. Le
téléphone ne change pas.

1. **Réglages, modèle de Polaris** (« App settings layout », grille 2fr / 5fr) : pour chaque réglage, le titre et la
   description à gauche, les contrôles dans une carte à droite ; plus de filets entre les réglages ; la note de démo et
   le récapitulatif de l'IA dans la colonne des cartes. En CSS seulement (le titre et la description flottent à
   gauche, la carte est dessinée derrière les contrôles) : toutes les rubriques en profitent sans changer leur
   balisage. Le sommaire des rubriques reste à gauche.
2. **60 caractères par ligne** sur ordinateur (Material, typographie : 40 à 60) : `--measure` passe de 31 à 24 em
   au-dessus de 820 px ; sur téléphone, 31 em, rien ne change. La mesure s'étend aux lignes de liste, au mois en bref,
   à la page des données personnelles et aux avis (leur cadre garde sa largeur, une marge droite limite le texte).
3. **L'audit des règles** mesure le texte des Réglages par rapport à la carte de chaque réglage : la grande carte n'a
   plus de cadre.
4. **Figma** : Réglages recomposés (Recherche d'emploi, Agenda et extension, clair et sombre) ; les variables de
   mesure de la 1.6.34 suivent les 24 em du code sur ordinateur (`measure` 384 px, `measure-small` 336 px,
   `measure-figure` 624 px) et restent à 31 em sur téléphone (496, 434, 682) ; les 8 écrans en 1920 sur la page
   « Planche · 1920 ».

- **Écart avec Polaris** : le titre et la description restent dans la rangée de leur carte ; quand ils sont plus hauts
  que les contrôles (« Date limite de remise des preuves »), la carte s'allonge d'autant.
- **Doublon évité** : la PR 344 refaisait d'abord ce que les 1.6.31 à 1.6.33 avaient déjà livré (références,
  conteneur unique, tableau) ; remise à jour sur main, elle ne garde que la nouveauté (1.6.34 étant pris par une
  autre PR, elle devient la 1.6.35).

## Vérifié (1.6.35)

- Captures avant/après (horloge figée) en **1440, 1920 et 390 px, clair et sombre** (496 captures, démo et compte
  neuf) : changent en 1440 et 1920 les Réglages (le modèle Polaris) et les pages où la mesure resserre le texte ;
  **en 390 px, aucune capture ne change**.
- 60 caractères : aucune ligne au-delà, sur toutes les pages, en 1440 et 1920, démo et compte neuf (hors lignes de
  liste, où la mesure compte l'initiale et l'action avec le texte : le texte seul y fait moins de 60 caractères).
- Figma et code côte à côte en 1440 et 1920, planches Figma, avant/après en sombre : `docs/captures/1.6.35/`.
- 476 tests (deux de plus : le modèle des Réglages, la mesure), lint, types ; 5 tests de l'audit ; trois audits sans
  défaut, démo et compte neuf, l'accessibilité aussi en sombre.
