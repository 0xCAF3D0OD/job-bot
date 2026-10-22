# Règles de l'interface

Ce qui vaut pour toute la plateforme, quelle que soit la page. Chaque règle renvoie au document qui l'a posée.

## Titres et textes (docs/88)

1. Le titre d'une page reprend mot pour mot son entrée du menu, sans sous-titre ; une petite précision peut se mettre au-dessus, en capitales (la date d'Aujourd'hui). Les pages de présentation (connexion, Découvrir, accueil) gardent leurs phrases.
2. Titres de cartes, d'onglets, de sections et légendes : un nom, sans « ton », « ta », « tes », « mon », « ma », « mes ».
3. Boutons et liens d'action : un verbe à l'infinitif (« Demander un certificat intermédiaire »).
4. Le tutoiement reste dans les phrases : messages, erreurs, états vides.
5. Un texte d'aide reste affiché pour une erreur (avec quoi faire), un avertissement avant une action irréversible, ou ce qui part à l'IA, en une ligne. Ce qui explique passe en description au survol (`HoverNote`, docs/53) ou disparaît : l'assistant répond au reste.
6. Pas de prix dans le libellé d'un bouton : le coût d'une action IA est dans sa description au survol (« Environ 0,10 $. »).
7. Un test (`frontend/src/titles.test.ts`) vérifie les règles 1, 2 et 6.

## La barre du haut (docs/89)

Deux pages dans le menu principal (docs/92) : Aujourd'hui et Candidatures ; sur téléphone, une barre d'onglets en bas de l'écran, cachée sur les écrans de travail (Préparer, l'accueil). À droite, une capsule : la cloche (un chiffre rouge, ce qui attend une action), l'étincelle de Progresser (un point violet, du nouveau à lire ; elle déroule un aperçu des actualités et des formations en cours), puis l'initiale du compte, qui ouvre le menu du compte (Profil, Réglages, Données personnelles, Diagnostic, « Collecter maintenant », la déconnexion). Du nouveau à lire : un point, pas un chiffre ; un chiffre dit ce qui attend une action. Dans la capsule, des zones sans cadre ni fond, séparées par des filets ; ouvrir l'une déroule le cadre vers le bas, et son contenu apparaît dedans (docs/91). Les menus « ⋯ » ont le même style : bordure fine, coins de 10 px, presque pas d'ombre, un déroulé court.

## Aéré (docs/93)

1. Une carte a au moins 1,25 rem de marge intérieure (1,5 rem pour une carte de catalogue).
2. Le texte courant a un interligne d'au moins 1,5 ; au moins 0,75 rem entre un texte et ce qui suit.
3. Si une carte se serre, on retire un élément plutôt que de réduire les marges.
4. Les logos d'entreprise sont des carrés aux coins arrondis (0,6 rem) ; restent ronds la note, l'initiale du compte et les pastilles.

## La structure (docs/32, 43, 63, 84, 88, 93, 95, 106, 110 ; reprises en docs/119)

Des règles validées au fil des versions, réunies ici en 0.89.1 : elles n'étaient écrites que dans leur document d'origine.

1. **Une largeur, un en-tête** : le contenu des pages sur une seule largeur (80 rem) sous un seul en-tête ; une carte seule prend toute cette largeur (docs/43). Un formulaire ou une liste courte peut se limiter à la largeur de lecture (44 à 46 rem, docs/63).
2. **Les écarts** : 1,25 rem entre deux cartes ; 2 rem entre les grands blocs d'une page (la phrase du jour, les bandeaux, les cartes, les guides) ; 0,75 rem entre un titre et son contenu, et entre deux repliables (docs/93, 95, 106).
3. **Dans une carte** : 1,5 rem de marge intérieure, sur ordinateur comme sur téléphone (docs/106 complément 0.77.6), jamais moins de 1,25 rem ; 1 rem entre étiquettes, titre et faits, 0,5 rem entre deux faits, 1,25 rem avant le bas (docs/93). Les repliables suivent la même marge que les cartes.
4. **Une rangée, une hauteur** : les cartes côte à côte ont la même hauteur ; la plus courte s'étire, son contenu reste en haut (docs/32, 43, 93). Un vide qui reste se remplit d'une information utile, jamais d'une image (docs/63).
5. **Les grilles** : 3 colonnes au plus (18 rem au moins par carte), 2 sur tablette, 1 sur téléphone ; deux cartes côte à côte en 3 / 2 (docs/93, 95). Une liste courte dans une carte de toute la largeur passe en deux colonnes plutôt que de laisser la moitié vide (docs/119).
6. **Les filets** : 1,75 rem de chaque côté sur ordinateur, 1,5 rem sur téléphone (docs/106).
7. **Les interlignes** : 1,5 pour le texte, 1,6 pour les aides, 1,3 pour un titre (docs/93, 106).
8. **Les titres** (docs/110) : page en 2,4 rem, section en 1,5 rem au-dessus de sa carte, réglage en gras ; pas de point final ; un titre de partie n'est pas souligné.
9. **Les repliables** : le résumé en gris à droite de la ligne ; une seule ligne ouverte par groupe ; le contenu long et secondaire dans un panneau latéral (docs/32). Une action sur un repliable ouvert (« Masquer ») se met sur sa ligne de titre, jamais sur une ligne à elle (docs/119).
10. **Une partie à une seule action** devient une ligne : le nom à gauche, l'action à droite (docs/106).
11. **Consulter ou modifier** : une carte ne mélange pas les deux (docs/110).
12. **Enregistrer** : 1,5 rem dessous, jamais de filet juste au-dessus ; un bouton ou une pilule ne passe jamais à la ligne (docs/32, 106, 110).
13. **Le texte** : un état vide en une phrase, plus l'action qui le remplit (docs/88) ; pas de texte de plus de deux lignes, une liste pour le contenu long (docs/84).
14. **L'essentiel sans défiler** (docs/32) ; sur téléphone, 10 éléments puis « Voir plus » (docs/43).
15. **Les listes** : colonnes d'action de largeur fixe ; pendant le chargement, des blocs gris à la forme du contenu (docs/43).
16. **Une seule chose en orange** sur une page : ce qui demande d'agir (docs/43, 54).
17. **Aujourd'hui** (docs/95) : une seule action sous la phrase du jour, trois bandeaux au plus, des cartes neutres (la couleur pour les nombres à traiter), les guides disparaissent une fois finis.
18. **L'audit des règles** (`frontend/scripts/regles.py`) vérifie les points 3 et 4 : un texte à moins de 1,25 rem du bord de sa carte, deux cartes d'une rangée de hauteurs différentes.

## Les contrôles (docs/94)

1. Une seule hauteur, `--control-h` : 2,5 rem sur ordinateur, 2,75 rem sur téléphone, pour les boutons, liens en bouton, listes de choix, champs d'une ligne, sélecteurs, ⋯ et boutons ronds (cercles de la même hauteur).
2. Dans une rangée, tout est centré ; l'écart vient de la rangée, jamais d'une marge propre à un élément.
3. Gardent leur forme : zones de texte, cases, curseurs, étiquettes, la capsule.
4. Avant une PR d'interface, l'audit des rangées (`frontend/scripts/alignement.py`) est vide.
5. Et l'audit d'accessibilité (`frontend/scripts/accessibilite.py`, docs/117) : aucun défaut, parcours au clavier sans blocage.
6. Et l'audit des règles (`frontend/scripts/regles.py`, docs/118, docs/119) : pas d'aide de plus de 20 mots, pas de titre avec un pronom (« je, tu, te, ton, ta, tes, me, mon, ma, mes ») ou en question, pas de barre verticale ni de cadre dans un cadre, pas de texte à moins de 1,25 rem du bord d'une carte, pas de rangée de hauteurs différentes.

## Iconographie (docs/101)

1. **Le style** : grille de 24 px, trait de 1,8 px arrondi, coins doux, couleur du texte. Les icônes sont dans `frontend/src/icons.ts` et s'affichent avec `AppIcon` ; aucun caractère (× ← → ↗ ＋ ✓ …) ni émoji ne sert d'icône (un test le vérifie).
2. **Icône et texte** là où on se repère : menus, onglets, boutons principaux, lignes des menus ⋯.
3. **L'icône remplace l'étiquette** dans les métadonnées (lieu, entreprise, date, taux, télétravail, source…) ; l'étiquette reste pour les lecteurs d'écran.
4. **Icône seule** pour les actions secondaires (copier, supprimer, modifier, garder, fermer, flèches, ajouter, ouvrir ailleurs, filtrer, actualiser), avec `IconButton` : son nom annoncé et montré en infobulle au survol et au focus. Gardent leur texte : les choix qui engagent, « Annuler », les formats de fichier.
5. **Le point pêche** (l'icône `ai`) marque uniquement les actions qui lancent l'IA. L'étincelle à 4 branches est réservée à l'IA (la rubrique IA des Réglages, la mascotte).
6. **Ne sont pas des icônes de l'iconographie** : le logo, la mascotte, les logos d'entreprises et de connexion, les graphiques.

## Illustrations (docs/62, docs/67)

1. Une illustration seulement si l'écran n'a rien d'autre à montrer (vide, erreur, première fois) ou pour marquer un moment (réussite). Les états de jobA1 (une liste vide, une page qui charge) montrent le visage du 1 (voir « Le visage du 1 », docs/123).
2. Jamais dans un formulaire, une liste ou un tableau ; jamais dans une carte (posée à côté, ou au-dessus pour la carte d'une réussite).
3. Une seule famille : les images générées pour jobA1 (des personnes dans des scènes calmes), en version transparente, sans cadre ni fond. 300 px au plus, 200 sur téléphone ; dans l'accueil, 260 px (200 sur téléphone), le personnage qui parle 320 px (240) ; la présentation de la plateforme, 440 px en tête (320 sur téléphone) et 250 par étape (190). Exceptions : la carte d'une réussite (220 px, 170 sur téléphone) et l'Engagement (440 px, 260 sur téléphone) ; la page de connexion, coupée en deux, où la scène remplit toute la moitié gauche (élargie à 57 %), et un bandeau sur téléphone.
4. En sombre, la série sombre quand elle existe ; sinon l'image claire assombrie (luminosité 85 %). Décorative pour les lecteurs d'écran : le texte à côté dit tout.
5. Une entrée une fois chargée (fondu et légère montée, 500 ms), rien si « réduire les animations » est demandé. Préparées par `frontend/scripts/illustrations.mjs` (480 et 800 px ; 480, 800 et 1264 pour la connexion). Exception : la page de maintenance montre le dessin unDraw de la maintenance, au même endroit qu'une illustration (300 px, 200 sur téléphone), et en boucle (docs/80) ; les autres dessins unDraw restent en réserve (`frontend/reserve/`), non chargés.

## Mouvement (docs/59)

1. Le mouvement répond à une action (appui, survol, choix, envoi) ; rien ne bouge tout seul en boucle, sauf une vraie attente (rédaction par l'IA, page qui charge et premier relevé : l'œil et la bille du visage pulsent, docs/123 ; page de maintenance : son dessin unDraw bouge tant que l'attente dure, docs/80).
2. Trois durées : 150 ms (survol, appui), 250 ms (un état qui change), 500 ms (une entrée). Exceptions écrites : la carte d'une réussite monte en 420 ms avec un léger rebond (docs/61 §1) ; la transition d'une page qui charge entre et sort en 400 ms et reste au moins 1,2 s, rien si la page arrive en moins de 0,15 s (docs/63 §3) ; en sombre, la connexion joue une fois la vidéo du soir qui tombe (9 s), puis reste sur l'image du soir (docs/67, complément 0.55.3) ; sur la connexion, le ciel suit la vidéo (9 s) et la phrase change de couleur en 1,2 s à 5,5 s de la vidéo (docs/67, compléments 0.55.3 à 0.55.5) ; le chemin de La plateforme suit le défilement (120 ms), entier d'emblée si « réduire les animations » (docs/67) ; la capsule se déroule en 350 ms et un menu « ⋯ » en 250 ms, sur la courbe `cubic-bezier(0.72, 0.01, 0, 1)` prise à Sphere, leur contenu en fondu (docs/91).
3. « Réduire les animations » : les retours restent (couleurs, coches, textes), sans mouvement.

## Accès à un contenu (docs/57)

L'élément entier est cliquable, avec un survol ; pas de « › » ni de « Continuer › ». Les vraies actions gardent leur verbe.

## Le visage du 1 (docs/123)

1. **Quatre humeurs**, les mêmes partout : ravi (grand sourire, vert menthe), content (sourire, bleu lavande), attentif (bouche droite ; orange seulement quand il faut agir, « On rattrape », gris chaud sinon), neutre (bouche plus courte, gris). Jamais déçu.
2. **Trois tailles** : 20 px dans une ligne (la note), 56 px en tuile à droite du titre d'une carte (le mois ORP ; sur la tuile, le visage en noir), 120 px au centre d'un état (liste vide, page qui charge : le visage, le titre, une ligne). Au plus un grand visage par écran ; décoratif, le texte dit tout.
3. **Les illustrations** : le visage pour les états de jobA1 et les deux victoires (un entretien proposé, l'objectif du mois atteint : le visage ravi au-dessus de la carte d'une réussite, six bulles, une fois) ; les scènes de personnes pour l'accueil, la connexion, La plateforme, les pages d'erreur et les autres réussites (candidature envoyée, preuves remises). Jamais les deux côte à côte. La mascotte ronde reste à l'assistant (quand l'IA parle).
4. **Le mouvement** : changer d'humeur, la bouche en fondu (150 ms) ; un clin d'œil quand l'objectif du mois est atteint (une fois par visite) ; l'œil et la bille qui pulsent pendant une vraie attente. Rien avec « réduire les animations ».

## La note (docs/73, docs/76, docs/121 §C.5)

- **Dans les listes** (Offres, Aujourd'hui) : un mot et le visage du 1, à la couleur de la note : « Très proche » (85 et plus, ravi), « Proche » (70, content), « À creuser » (50, attentif, gris chaud), « Loin » (neutre, gris). Le chiffre au survol (« Proche : 82 sur 100 »). Un filet en bas de la ligne, rempli comme la note.
- **Dans la fiche** : un cercle dont le contour se remplit comme la note (plein à 100), à la couleur de la note ; la part manquante reste visible en gris clair. Sous lui, une phrase : pourquoi.
- Une offre pas encore notée : « Pas encore notée », qui dit pourquoi au survol ; dans la fiche, un cercle vide en pointillés avec « – ».
- Jamais une pastille ni un visage déçu.

## Les actions (docs/74, docs/76)

1. Dans chaque partie (ou ligne d'un tableau), le contenu reste visible, avec au plus une action importante ; le reste va dans « ⋯ », en haut à droite de la partie ou au bout de la ligne.
2. Les suppressions toujours dans « ⋯ », en dernier, en rouge, après un filet, avec leur confirmation.
3. Pas de « ⋯ » pour une seule action ordinaire : elle s'affiche directement.
4. Chaque « ⋯ » a un nom pour les lecteurs d'écran : « Actions sur … ». 2,75 rem au doigt ; le menu ne sort jamais de l'écran, ni sous une barre fixe.
5. Restent visibles sans menu : les « Copier » à côté des champs, les téléchargements qui sont le but d'une carte (PDF, Word), les listes de liens qui sont le contenu, les étapes d'un parcours, les boutons d'un formulaire.

## Les listes (docs/73)

Une ligne par élément, séparées par un filet ; une ligne par jour quand la liste suit les jours. Au moins 0,75 rem au-dessus et au-dessous d'une ligne, et entre un texte et la carte qui suit.

## Un seul cadre par bloc (docs/74, docs/76)

Dans une carte ou un volet, un tableau, une liste ou un repliable perd son propre cadre : des lignes séparées par un filet, alignées sur le texte de la carte. Jamais deux cadres l'un dans l'autre.

## Écrans de travail sur téléphone (docs/75)

Sous 820 px, un écran où l'on travaille un moment (l'entraînement à l'entretien) prend tout l'écran ; sa barre du haut garde le titre sur une ligne et ses actions.

## Les Réglages (docs/106)

1. Une rubrique, une carte ; ses parties séparées par leur titre et un filet fin (0.77.3), jamais une carte dans la carte.
2. Pas de barre verticale : un contenu replié s'ouvre sous son titre, au même retrait, dans une carte ou ailleurs (`DisclosureRow`, docs/118 §2).
3. Pas de filet orphelin : un filet sépare deux choses, jamais la dernière du bord.
4. Un réglage d'un seul champ s'enregistre au changement (« Enregistré » une seconde à côté) ; un formulaire de plusieurs champs a un seul « Enregistrer » plein, à la fin.
5. Les nombres sans flèches haut / bas, partout ; quelques valeurs sensées : des pastilles.
6. La pastille de nombre (0.84.2, docs/115) : pleine, couleur principale, la même partout ; sur le coin haut droit de l'icône quand l'icône est au-dessus du nom, bordée de la couleur du fond ; après le nom quand l'icône est à côté. Elle ne remplace jamais l'icône.

## La couleur d'accent (docs/107)

Une seule couleur d'accent, le bleu du logo (`--accent`). Le texte posé dessus passe par `--on-accent` (blanc en clair, foncé en sombre), jamais `#fff` écrit en dur. La pêche reste la seule touche du logo et des actions IA.

## Annuler plutôt que confirmer (docs/108)

1. Ce qui se rattrape se fait tout de suite, avec le bandeau « … · Annuler » pendant 6 secondes (`offerUndo`).
2. Ce qui ne se rattrape pas, ou touche quelqu'un d'autre, se confirme dans la page, à l'endroit du bouton (`InlineConfirm`), le focus sur « Garder ».
3. Jamais de `window.confirm` ni de `window.prompt` (un test le vérifie) : on modifie sur place, le champ à la place du texte.

## L'aide au doigt (docs/108)

Une description au survol (`HoverNote`) a, sur téléphone, un « i » à droite du titre qui l'ouvre en une ligne grise sous lui. Pas de « i » dans un bouton ni un lien.

## Comme les CFF (docs/110)

1. Un titre de section au-dessus de sa carte ; dans la carte, le titre d'un réglage en gras et sa description grise, toujours visible, **en une ligne** (12 mots environ) : ce que fait le réglage. Le pourquoi, le coût, les exceptions passent au survol (`HoverNote`) (docs/118 §1).
2. L'interrupteur à droite, centré sur le titre et sa description ; sous un choix, la description alignée sur le libellé ; l'étiquette d'une date dans le champ.
3. Ce qu'on modifie dans une carte blanche bordée ; ce qu'on consulte sur fond gris (`setting-info`) ; les actions en pilules (`pill`), pleine largeur sur téléphone ; un état vide en cadre pointillé.
4. Une longue page sur téléphone a des marqueurs collés en haut, qui suivent la lecture.

