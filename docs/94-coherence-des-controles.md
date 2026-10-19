# 94 — Une seule hauteur pour les contrôles (version 0.70.7)

> Statut : **validé** le 2026-10-19.
> Origine : ta remarque du 2026-10-19, capture de Progresser › Formations à l'appui : « certains éléments n'étaient pas alignés, comme "Chercher d'autres formations" ; il faut à tout prix avoir une cohérence entre chaque composant ».

## Le constat

Un audit des 20 pages (ordinateur 1 440 px, téléphone 390 px) a mesuré les contrôles qui se trouvent sur une même rangée. Il n'y a pas de hauteur commune :

| Contrôle | Hauteur aujourd'hui |
|---|---|
| Liste de choix (« Tous les types ») | 31 px |
| Menu « ⋯ » | 36 px |
| Bouton « ＋ » du Suivi | 38 px |
| Bouton (« Ajouter », « Candidature spontanée ») | 40 px |
| Sélecteur (« Domaine / Tout », « Calendrier / Liste ») | 41 px |
| Champ de saisie (recherche, mots-clés) | 44 à 46 px |

**Rangées en défaut** :
- **Progresser › Formations** : le sélecteur (41), trois listes (31), et « Chercher d'autres formations », décalé par une marge de 1,5 rem au-dessus.
- **Candidatures › Offres** : la recherche (44) à côté de « Candidature spontanée » (40), centres décalés de 14 px.
- **Candidatures › Suivi** : ← → (40), Calendrier / Liste (41), ＋ (38), ⋯ (36).
- **Réglages › Actualités** : le champ des mots-clés (46) et « Ajouter » (40) ; « Parcourir les suggestions » (40) et ⋯ (36).
- **Sur téléphone**, les mêmes, plus le champ et « Ajouter » du Domaine dans chaque rubrique des Réglages.

## La règle (ajoutée à `docs/interface.md`)

1. **Une seule hauteur pour tous les contrôles** : `--control-h`, soit **2,5 rem (40 px) sur ordinateur** et **2,75 rem (44 px) sur téléphone**, la taille au doigt. Elle s'applique :
   - aux boutons, petits ou grands ;
   - aux liens en bouton ;
   - aux listes de choix et aux champs de saisie d'une ligne ;
   - aux sélecteurs (le cadre extérieur) ;
   - au ⋯ ;
   - aux boutons ronds (＋, ← →).
2. **Dans une rangée, tout est centré verticalement**, sans marge propre en haut ou en bas. L'écart vient de la rangée (`gap`), pas des éléments.
3. **Les boutons ronds** (＋, ⋯, ← →, le cœur) sont des cercles de la même hauteur.
4. **Ne bougent pas** :
   - les grandes zones de texte ;
   - les cases à cocher ;
   - les curseurs ;
   - les étiquettes et pastilles (ce ne sont pas des contrôles) ;
   - la capsule (docs/91) ;
   - les boutons pleine largeur des formulaires de connexion.

## Ce qui change

- **`style.css`** :
  - un jeton `--control-h` ;
  - `button`, `.button-link`, `select`, `input` (texte, date, nombre, recherche), `.segmented`, `.more-button` et les boutons ronds en prennent la hauteur, avec un remplissage horizontal inchangé et le texte centré ;
  - les marges propres qui décalaient un contrôle dans une rangée sont retirées. C'est le cas de « Chercher d'autres formations », enveloppé dans `.news-status` avec 1,5 rem au-dessus.
- **Les rangées listées plus haut** sont vérifiées une à une, en clair et en sombre, sur ordinateur et téléphone.
- **L'état qu'on ne voit pas dans la démo** (« Chercher d'autres formations », visible quand l'IA est active) est vérifié avec une capture où l'IA est simulée.

## Vérifier dans la durée

- **Un audit des rangées**, script Playwright, sur les 20 pages, sur ordinateur et téléphone. Il signale toute rangée où deux contrôles diffèrent de plus de 2 px en hauteur ou en centre.
- **Avant la PR, le résultat doit être vide.** Le script n'entre pas dans les tests automatiques : jsdom ne mesure pas la mise en page. Il est rangé dans `frontend/scripts/alignement.mjs` et documenté dans `docs/exploitation.md`, pour le relancer à chaque PR d'interface.

## Vérifié avant la PR

- L'audit est vide sur les 20 pages, sur ordinateur et téléphone.
- Captures avant / après :
  - Formations, IA active et inactive ;
  - Offres ;
  - Suivi ;
  - Réglages › Actualités ;
  - un formulaire (Profil › Coordonnées) ;
  - en clair et en sombre.
- Tests de l'interface, lint et typecheck.

## Écarts

- **Le script est en Python**, pas en JavaScript : Playwright n'est pas une dépendance de l'interface, et `uv run --with playwright` le fournit sans rien installer. Il est rangé dans `frontend/scripts/alignement.py` ; la commande est dans `docs/exploitation.md`.
- **Offres** : la recherche de la colonne de gauche et « Candidature spontanée » n'étaient pas alignées (12 px). La liste démarre maintenant à la hauteur de la recherche, sous le même retrait que le trait vertical des filtres.
- **Un sélecteur de 4 choix ou plus**, qui passe sur deux rangées, garde sa hauteur naturelle.
- **Vérifié** :
  - l'audit est vide sur les 20 pages, ordinateur et téléphone, IA simulée pour Formations (avant : 5 rangées sur ordinateur, 14 sur téléphone) ;
  - captures de Formations (IA active), Offres, Suivi, Réglages › Actualités et Profil › Coordonnées, en clair, en sombre et sur téléphone ;
  - 325 tests de l'interface, lint et typecheck.
