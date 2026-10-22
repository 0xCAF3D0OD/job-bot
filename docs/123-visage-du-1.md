# 123 — Le visage du 1, notre langage (version 0.94.0)

> Statut : **validé** le 2026-10-22 (« oui pour tout ») : la direction, les quatre décisions (les illustrations, le visage et l'assistant, le mouvement, jamais de visage déçu) et l'ordre des écrans.
> Origine : tes maquettes du 2026-10-22 (Q : l'objectif ORP du mois ; R : un moment de victoire ; S : un jour sans rien à faire ; T : écran vide et collecte en cours ; U : tout ensemble, en compact), après la note en mots (docs/121 §C.5).
> Se construit sur docs/103 (le logo, le visage du 1), docs/99 (la mascotte de l'assistant), docs/61 (la carte d'une réussite), docs/86 (le bon rythme), docs/95 (Aujourd'hui).

## L'idée

Un seul visage, celui du logo, qui dit **où en est la personne** avec quatre humeurs. Les mêmes partout : la note d'une offre (docs/121 §C.5), le mois ORP, les moments, les attentes, les écrans vides. On apprend le langage une fois.

## 1. Les quatre humeurs

| Humeur | Le visage | La couleur | Où |
|---|---|---|---|
| **Ravi** | grand sourire, un clin d'œil possible | vert menthe | note « Très proche », objectif atteint, réponse reçue |
| **Content** | sourire | bleu lavande de l'accent | note « Proche », mois « Dans les temps », écran vide, chargement |
| **Attentif** | bouche droite | orange **seulement** quand il faut agir (« On rattrape ») ; gris chaud sinon (note « À creuser ») | mois en retard, note à creuser |
| **Neutre** | bouche droite plus courte | gris | note « Loin », rien à dire |

- **Jamais déçu** : pas de bouche qui tombe ni de moue. La marque n'a jamais l'air déçue de la personne. *(Correction du docs/121 §C.5, qui prévoyait une bouche qui tombe pour « Loin » : c'est le visage neutre.)*
- **Les yeux** gardent le logo : un œil bleu, une bille pêche (docs/103), sur fond clair ou sombre ; sur une tuile de couleur, les yeux et le trait passent en noir, comme sur les maquettes.
- **Les dessins** : des tracés de l'iconographie (grille de 24 px, trait arrondi), déclinés en trois tailles : 20 px (dans une ligne), 56 px (une tuile de carte), 120 px (un moment, un écran vide). Pas d'image : des SVG qui suivent le mode sombre.

## 2. Les écrans, dans l'ordre

1. **Q, le mois ORP** (la carte « Mois ORP » d'Aujourd'hui et du Bilan) : la tuile du visage à droite du titre, le compte en grand (« 6 / 10 candidatures »), **une barre en segments**, un par candidature de l'objectif (au-delà de 15, une barre continue), et une phrase avec son mot en couleur : « **Dans les temps.** Encore 4 d'ici le 31 octobre. », « **On rattrape.** Il reste 7 candidatures en 6 jours ouvrables. », « **Objectif atteint.** Le 24 octobre. Le reste du mois est à toi. »
2. **T, le chargement et les écrans vides** : le visage de 120 px au centre, le titre, une ligne. Il remplace les dessins unDraw des pages qui chargent (docs/67) et des collectes ; il remplace l'illustration des états vides **de jobA1** (Suivi sans relance, Offres sans offre, journal vide…).
3. **S, « Rien d'urgent aujourd'hui »** : un jour sans offre à examiner, sans relance ni échéance, Aujourd'hui montre le visage ravi, « Rien d'urgent aujourd'hui. », une ligne qui dit pourquoi, la devise, la carte du mois ORP en compact, et « Voir les offres quand même ».
4. **R, les moments de victoire** : seulement **une réponse positive** (entretien proposé) et **l'objectif du mois atteint**. La carte d'une réussite (docs/61) garde son entrée (420 ms, léger rebond) et ses boutons ; le visage ravi remplace l'illustration ; de petites bulles aux couleurs de l'humeur.
5. **U, Aujourd'hui en compact** : la carte du mois ORP en une ligne (tuile, « Mois ORP · 6 / 10 », segments, « Dans les temps »), les meilleures offres avec la note en mots (docs/121 §C.5, pas en pilules), l'état vide d'une partie en une ligne avec le petit visage. Les bandeaux restent ceux d'Aujourd'hui (docs/95), pas un aplat de couleur.

## 3. Les règles qui changent

- **Illustrations** : le visage pour les états de jobA1 (vide, chargement, moments) ; les scènes de personnes générées restent pour l'accueil, la connexion, La plateforme et les pages d'erreur. Deux familles, chacune à sa place, jamais côte à côte sur un écran.
- **Le visage et l'assistant** : la mascotte ronde, avec sa pointe de bulle, reste **seulement pour l'assistant** (docs/99) : quand l'IA parle. Le visage du 1 donne l'état de la plateforme. Ils ne se montrent pas ensemble au même endroit.
- **Le mouvement** (docs/59, docs/99) : changer d'humeur, un fondu de 150 ms, sans déformer le dessin. En plus, trois gestes, chacun lié à un événement : un **clin d'œil** quand l'objectif est atteint ; un **petit rebond** à l'entrée d'une victoire ; les **points qui pulsent** pendant une vraie attente (chargement, collecte). Rien d'autre ne bouge ; « réduire les animations » : aucun geste, le visage final directement.
- **La note** : la règle de docs/121 §C.5 (le mot, le visage, le filet dans les listes ; le cercle dans la fiche).
- `docs/interface.md` reçoit une section « Le visage du 1 » avec ces quatre points.

## Garde-fous

- **Le texte dit tout** : le visage est décoratif pour les lecteurs d'écran ; le mot et la phrase portent le sens.
- **Pas de visage partout** : au plus un grand visage par écran ; les petits visages seulement à côté d'une note ou d'un état.
- Les couleurs passent le contrôle des contrastes (4,5:1 pour le mot coloré), en clair et en sombre.

## Livraison proposée

Après C (docs/121), qui pose le visage de la note :

- **0.94.0** : les dessins des quatre humeurs, Q (le mois ORP), T (chargement, écrans vides).
- **0.95.0** : S (rien d'urgent), R (les victoires), U (Aujourd'hui en compact).

## Écarts (0.94.0 : les humeurs, Q, T)

- **Règles relues avant de construire** (`docs/interface.md`), vérifiées sur captures à 1440 et 390 px : la carte Mois ORP d'Aujourd'hui, l'Objectif ORP du Bilan, la liste vide des Offres, le chargement d'une page.
- **Les dessins** : le visage existant (`FaceMark`, docs/121 §C.5) gagne les gestes ; une tuile de 56 px (`FaceTile`, fond pastel de l'humeur, visage noir, la bille aussi en noir pour rester visible sur l'orange) ; un état de 120 px (`FaceState` : le visage, le titre, une ligne). Le clin d'œil n'est pas un dessin à part : l'œil se ferme et se rouvre (450 ms).
- **Q, le rythme** : « Dans les temps » tant que le compte atteint la part de l'objectif due aux jours ouvrables (lundi à vendredi) **passés** avant aujourd'hui ; le 1er du mois, personne n'est en retard. Sinon « On rattrape. Il reste 7 candidatures en 6 jours ouvrables. » (aujourd'hui compris). Les jours fériés ne sont pas comptés à part.
- **« Objectif atteint. »** sans la date (« Le 24 octobre ») : jobA1 ne garde pas le jour où l'objectif a été atteint ; la phrase dit « Le reste du mois est à toi. ». À ajouter si tu y tiens (une requête de plus).
- **Sans objectif** : le compte seul, sans tuile ni barre (le guide d'Aujourd'hui demande déjà l'objectif).
- **Le Bilan** : la jauge en demi-cercle (du rouge au vert) est remplacée par le même bloc qu'Aujourd'hui, avec le mois sous le titre. Les trois mois précédents restent, **sans cadre** (ils formaient des cartes dans la carte) : trois colonnes sous un filet, « atteint » en vert ; « manqué » n'est plus en orange (une seule chose en orange, et jamais l'air déçu).
- **T, le chargement** : le voile d'une page qui charge montre le visage, l'œil et la bille qui pulsent, et le nom de la page. Les sept dessins unDraw des transitions passent en réserve (`frontend/reserve/illustrations-undraw/`) ; **la maintenance garde son dessin** (docs/80, le cadrage n'en parlait pas).
- **T, les listes vides** : Offres (« Aucune offre »), Suivi en liste (« Aucune candidature en décembre »), Bilan (« Pas encore de candidature »), Actualités (« Rien à lire » ; « Premier relevé » avec le visage qui pulse pendant le premier relevé). La page introuvable garde sa scène (page d'erreur), l'assistant des alertes aussi (un parcours, pas un état).
- **Deux scènes sans emploi** : « aucune-offre » et « actualites-video » ne servent plus ; gardées dans les illustrations, à retirer si on ne les reprend pas ailleurs.
- **Pas d'écran de collecte** : lancer une collecte affiche une phrase (« Collecte lancée… ») au-dessus du titre d'Aujourd'hui, sans dessin ; rien à remplacer. Le premier relevé des Actualités, lui, est une vraie attente : le visage y pulse.
- **Le mouvement** : la bouche en fondu (150 ms) quand l'humeur change ; le clin d'œil une fois par visite quand l'objectif est atteint ; « réduire les animations » : aucun geste.

## Vérifié (0.94.0)

- Tests de l'interface : le rythme (dans les temps, à rattraper avec les jours ouvrables qui restent, atteint, le 1er du mois, sans objectif) ; les segments (un par candidature, une barre continue au-delà de 15) ; la tuile orange seulement pour « On rattrape » ; l'état vide (visage décoratif, titre, ligne, attente). 422 tests, lint, vue-tsc.
- Les trois audits sur la démo à zéro (règles, alignement, accessibilité).
