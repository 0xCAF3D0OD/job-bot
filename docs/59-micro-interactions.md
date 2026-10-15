# 59 — Donner vie par les micro-interactions, plutôt que par de grandes illustrations (version 0.47.0)

> Statut : **validé** le 2026-10-15 ; 0.47.0 livrée (0.47.1 à suivre).
> Retour du 2026-10-15 sur 0.46.0 : « je ne suis pas satisfait du rendu », avec deux lectures : l'article *How to design micro-interactions* (UX Design Institute) et *The UI & UX Cheatsheet* (Marc Andrew, 21 conseils). Ce document remplace la suite prévue en docs/58 (0.46.1).

## 1. Ce qui ne va pas dans 0.46.0

Relu à la lumière des deux lectures :

| Constat | Ce que disent les lectures |
|---|---|
| **Des illustrations qui bougent en boucle** (boîte aux lettres, engrenage…) alors que personne n'a rien fait : le mouvement ne répond à rien. | Une micro-interaction part d'un **déclencheur** (un clic, un état qui change) et donne un **retour** ; elle est « simple et rapide ». |
| **Deux styles mêlés** : des personnages unDraw en aplats à côté de pictogrammes au trait fin. En sombre, la recoloration rend certaines illustrations délavées. | Cheatsheet n° 16 : des icônes du **même style** partout, ne pas mélanger. |
| **Le chargement lent** remplace les blocs gris (qui ont la forme de la page) par un dessin centré : quand le contenu arrive, tout saute. | Garder la forme du contenu ; un retour discret. |
| **La bulle « Je prépare ton fichier… »** : grande, au milieu de l'écran sur téléphone, et elle ne dit ni quoi ni combien. | Cheatsheet n° 21 : pour un téléchargement, être **informatif** (quel fichier, où on en est, fini). |
| **La prise en main** : une grande carte illustrée dans une ligne repliable, elle-même dans une carte : lourd, et l'étape est déjà dans la liste en dessous. | Cheatsheet n° 8 et n° 15 : de l'air, et mettre en avant l'essentiel seulement. |
| **Peu de vie là où l'on agit vraiment** : trier une offre, cocher une étape, copier un texte, envoyer une candidature ne réagissent presque pas. | C'est là que l'article place les micro-interactions : les points de friction, les confirmations. |

## 2. Le principe

- **La vie vient de ce que tu fais** : chaque action a un retour court et visible, toujours le même pour la même action (article : cohérence).
- **Rien ne bouge tout seul** en boucle, sauf ce qui attend vraiment (une rédaction de l'IA).
- **Trois durées seulement** : 150 ms (survol, appui), 250 ms (un état qui change), 500 ms (une entrée à l'écran) ; départ rapide, fin douce.
- **« Réduire les animations »** (réglage du système) : tous les retours restent (couleur, coche, texte), sans mouvement.

## 3. Les micro-interactions

| Déclencheur | Retour | Durée |
|---|---|---|
| **Appui sur un bouton** | le bouton s'enfonce légèrement (97 %) ; au survol, il s'éclaircit | 150 ms |
| **Survol d'une carte ou d'une ligne cliquable** | elle se soulève de 2 px avec une ombre douce, venue du haut comme toutes les ombres (Cheatsheet n° 5) | 150 ms |
| **Choix dans un sélecteur** (Offres reçues / Candidatures, 3 derniers mois / Un mois…) | la pastille violette **glisse** vers le choix | 250 ms |
| **Interrupteur** (sites suivis, sources) | le rond glisse, la couleur suit | 250 ms |
| **Trier une offre** (Plus tard, Ignorer) | la carte s'efface vers la droite, les suivantes remontent ; bulle « Passée en Plus tard · Annuler » | 250 ms |
| **Cocher une étape** (prise en main, liste de préparation) | la coche **se dessine** dans le rond, qui passe au vert | 250 ms |
| **Copier** (résumé ORP, champs à recopier, texte de l'assistant) | « Copier » devient « ✓ Copié » 1,5 s | 250 ms |
| **Marquer comme envoyée** | le bouton devient « ✓ Envoyée », la coche se dessine ; le compteur du mois monte de 1 | 250 ms |
| **Statut Engagement** | la seule petite fête : quelques confettis violets et menthe autour de la carte, une fois | 1 s |
| **Erreur dans un formulaire** | le champ fautif tremble une fois, le message apparaît **juste sous lui** (Cheatsheet n° 18) | 250 ms |
| **Première ouverture d'Aujourd'hui et du Bilan** | les chiffres des tuiles **comptent** jusqu'à leur valeur, les barres **montent**, la jauge se remplit, les courbes se tracent ; une fois par visite | 500 ms |
| **Nouvelle carte qui arrive** (offres après « Collecter », alertes) | elle apparaît en fondu et glisse de 8 px | 500 ms |

## 4. Les attentes, informatives plutôt que décoratives

- **Chargement d'une page** : retour aux **blocs gris à la forme de la page**, parcourus d'un léger reflet qui passe (au lieu de l'illustration). Le contenu prend leur place sans saut.
- **Fichier** (PDF, Word, export ORP) : le retour est **sur le bouton lui-même** (Cheatsheet n° 21) : « PDF » devient un petit cercle qui tourne et « Préparation… », puis « ✓ PDF · 84 Ko » 2 s. En cas d'échec : « Réessayer ». Plus de bulle.
- **Rédaction par l'IA** (10 à 30 s, la seule vraie attente) : une **barre d'étapes** sous le titre : ① Lire l'offre · ② Choisir tes expériences · ③ Rédiger · ④ Relire, l'étape en cours en violet, les faites cochées. Les lignes de la lettre apparaissent ensuite une à une en fondu (500 ms en tout).

## 5. Les illustrations : moins, plus petites, immobiles

- **Gardées seulement** pour les pages **vides** (aucune offre, Suivi vide, Bilan sans données, Actualités, assistant sans discussion) et la **page introuvable** : là, il n'y a rien d'autre à montrer.
- **Plus petites** (120 px, 96 px sur téléphone), en **teintes douces** : violet de la plateforme et gris, sans l'encre noire (elles ne s'opposent plus aux pictogrammes au trait).
- **Immobiles** : l'animation ne joue **qu'une fois** à l'apparition (moins d'une seconde), puis l'image reste fixe.
- **Prise en main** : plus de grande carte illustrée. La liste reste la liste, avec l'étape à faire **mise en avant** (fond violet pâle, sa phrase en gras, toute la ligne cliquable) et la coche qui se dessine quand une étape est faite. Un lien « Masquer » reste, à portée (Cheatsheet n° 4).
- **Assistant des alertes** : sans illustration ; une barre de progression en trois points en haut, qui avance.

## 6. Ce qu'on retire de 0.46.0

L'illustration de chargement, la bulle de fichier, la carte illustrée de la prise en main, les illustrations de l'assistant des alertes, et les animations en boucle. Les fichiers inutiles quittent le dépôt. Le composant `Illustration` et le script de préparation restent, pour les pages vides.

## 7. Livraison

| PR | Contenu |
|---|---|
| **0.47.0** | §4, §5, §6 et les micro-interactions de base : appui, survol, sélecteurs, interrupteurs, coches, copier, erreurs |
| **0.47.1** | Les retours d'actions (trier, envoyer, Engagement), l'entrée des chiffres et des barres, les nouvelles cartes |

Chaque PR avec une courte vidéo des interactions (ordinateur et téléphone, clair et sombre), et la vérification « réduire les animations ».

## Points à valider

1. **Le diagnostic** de 0.46.0 (§1).
2. **Le principe** : la vie vient des actions, rien ne bouge en boucle, trois durées (§2).
3. **Le tableau des micro-interactions** (§3).
4. **Des attentes informatives** : blocs gris avec reflet, retour sur le bouton du fichier, barre d'étapes de l'IA (§4).
5. **Illustrations réduites** aux pages vides et à la page introuvable, plus petites, sans encre noire, jouées une fois (§5) ; ce qu'on retire (§6).
6. **Deux PR** (§7).

## Écarts avec la livraison (0.47.0)

- **Retiré de 0.46.0** : l'illustration de chargement (`useLoadingGate`), la bulle de fichier, la grande carte de la prise en main, les illustrations de l'assistant des alertes et 12 fichiers d'illustration. Les blocs gris avaient déjà leur reflet qui passe : ils reviennent tels quels.
- **Illustrations gardées** (6) : mobile-inbox (Offres sans résultat), date-picker (Suivi en liste, mois vide), stepping-up (Bilan sans candidature), newsfeed (Actualités vides), chat-bot (assistant, discussion vide), page-eaten (page introuvable). 120 px (96 sur téléphone) ; l'encre noire devient un gris doux dans les deux thèmes ; le script transforme les boucles en un seul passage, qui finit sur l'image d'origine.
- **Page introuvable** : une adresse inconnue menait sans un mot à Aujourd'hui ; elle affiche maintenant « Page introuvable » et « Revenir à Aujourd'hui ».
- **Appui et survol** : boutons et liens-boutons s'enfoncent à 97 % ; les cartes cliquables (offres, blocs, tuiles, jauge, candidatures) se soulèvent de 2 px avec une ombre douce, seulement sur les écrans à souris.
- **Sélecteurs** : la pastille glisse pour les sélecteurs de deux ou trois choix sur une ligne (ceux de quatre, en grille, gardent le fond qui change). Les interrupteurs passent à 250 ms.
- **Prise en main** : l'étape à faire a un fond violet pâle, son intitulé en gras, et toute la ligne est cliquable ; la coche se dessine quand une étape est faite.
- **Alertes** : trois traits de progression au-dessus de « Étape N sur 3 ».
- **Copier** : un même composant `CopyLabel` sur les dix boutons Copier, « ✓ Copié » en vert.
- **Erreurs** : les champs signalés en erreur tremblent une fois ; les formulaires concernés (coordonnées, candidature, sites suivis) affichaient déjà le message sous le champ.
- **Fichiers** : l'état est sur le lien : « ⟳ PDF · Préparation… », puis « ✓ PDF · 84 Ko » 2 s, ou « · Réessayer ». Vérifié avec l'export CSV sur un serveur ralenti.
- **Rédaction par l'IA** : la barre d'étapes (lettre : Lire l'offre, Choisir tes expériences, Rédiger, Relire ; CV et pistes d'entretien : leurs propres étapes), l'étape en cours parcourue d'un reflet ; puis le document apparaît ligne à ligne. Couverte par un test (pas d'IA sur l'instance de test).
- **Réduire les animations** : appui, survol, glissements, coche, tremblement, reflet et apparitions sont coupés ; couleurs, coches et textes restent.
