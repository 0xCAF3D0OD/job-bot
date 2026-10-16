# 63 — Des blocs à leur taille, de l'information plutôt que du vide, une transition qu'on voit (version 0.48.2)

> Statut : **validé** le 2026-10-16, livré.
> Question du 2026-10-16, captures à l'appui (Aujourd'hui, Suivi, Profil, Réglages › IA et Compte) : « on voit des éléments qui prennent une grande place pour rien ; est-il préférable d'avoir une illustration, ou on gère d'une autre façon ? » Et : « l'animation qui arrive avant l'accès à la page devrait être plus lente, on ne voit pas vraiment ce qu'il y a ».

## 1. La réponse : pas d'illustration, deux autres moyens

D'après la règle posée en docs/62 (`docs/interface.md`) : une image ne remplit pas un vide, elle concurrence le contenu. Un bloc trop grand se règle de deux façons, dans cet ordre :

1. **Le ramener à sa taille** : un formulaire ou une liste courte n'a pas besoin de toute la largeur. Une largeur de lecture (environ 44 rem) suffit ; l'espace libre à côté reste blanc, et c'est voulu (Cheatsheet n° 8 : l'air rend une interface plus soignée).
2. **Le remplir d'une information utile** quand la plateforme en a une qui répond à la question qu'on se pose sur cette page.

## 2. Page par page

| Capture | Ce qui prend de la place pour rien | Après |
|---|---|---|
| **Aujourd'hui › Comment ça marche** (ouvert) | cinq lignes à gauche, toute la largeur vide à droite | les cinq étapes **en une frise horizontale** sur ordinateur : un rond coché ou vide par étape, relié par un trait, le titre et « où » dessous ; l'étape à faire en violet, toute la case cliquable. Sur téléphone, la liste actuelle |
| **Aujourd'hui › Progresser / Comprendre le marché** | les deux cartes prennent la hauteur de la plus haute : Progresser garde un grand vide en bas | chaque carte à sa hauteur ; Progresser montre jusqu'à **trois** formations (en cours, puis suggestions) pour équilibrer quand il y en a |
| **Suivi › calendrier** | les semaines sans candidature ont la même hauteur que les autres | une semaine **vide** est plus basse (les cases gardent le numéro du jour et les repères « relancer ») |
| **Suivi › Mes enseignements** (vide) | une phrase sur toute la largeur | la phrase limitée à la largeur de lecture |
| **Profil › Ce que je cherche** | le tableau des prérequis sur toute la largeur, valeurs courtes | le tableau à la largeur de lecture ; **à droite, ce que ces critères donnent** : « Ces 3 derniers mois : 412 offres reçues, 96 passent tes critères (23 %) », et les trois raisons d'écart les plus fréquentes (« lieu : 180 · taux : 74 · langue : 31 ») |
| **Réglages › toutes les rubriques** | des cartes étirées sur toute la largeur pour un ou deux champs ; dans Compte, « utilisé ✓ » perdu au milieu | les rubriques à la **largeur de lecture** (44 rem) |
| **Réglages › IA** | un seul champ | à droite du champ, **la dépense du mois** : « Octobre : 3,20 CHF sur 20 » avec une barre, et « IA configurée · modèle … » |

Les informations du Profil et des Réglages existent déjà dans la base : les raisons d'écart sont celles du filtre, la dépense du mois celle qu'affiche déjà le Diagnostic.

## 3. La transition des pages, plus lente

| | 0.48.0 | Après |
|---|---|---|
| Apparition du voile et de l'image | 250 ms | **400 ms** |
| Temps minimal à l'écran, une fois affichée | 0,5 s | **1,2 s** (l'animation de l'illustration a le temps de jouer) |
| Disparition | 250 ms | **400 ms** |
| Rien si la page arrive en moins de | 0,15 s | 0,15 s (inchangé) |

Une page lente reste donc au plus 1,2 s de plus derrière son voile ; une page rapide n'en a toujours pas.

## 4. Livraison

Une PR (**0.48.2**). La seule partie qui touche l'API : les raisons d'écart des 3 derniers mois pour le Profil (une route de lecture, calculée sur la base). Captures avant / après de chaque ligne du §2.

## Points à valider

1. **Pas d'illustration pour combler** : ramener à la largeur de lecture, ou remplir d'information utile (§1).
2. **Les changements page par page** : frise des étapes, cartes à leur hauteur, semaines vides plus basses, Profil avec « ce que donnent tes critères », Réglages à la largeur de lecture, dépense du mois à côté de l'IA (§2).
3. **Transition plus lente** : 400 ms d'entrée et de sortie, 1,2 s au moins (§3).
4. **Une PR** (§4).

## Écarts avec la livraison

- **Frise** : sur ordinateur, chaque étape est une case entière cliquable (fond gris au survol, violet pâle pour l'étape à faire) ; le trait vers une étape est vert quand la précédente est faite. « Pour bien démarrer » reste une liste.
- **Progresser** : les formations en cours d'abord, puis des suggestions vérifiées, trois en tout ; les cartes du bas ne sont plus étirées à la même hauteur.
- **Calendrier** : une semaine sans candidature passe à 3,4 rem de haut (au lieu de 5,2).
- **Profil** : « Ce que donnent tes critères » s'affiche à droite du résumé (pas pendant la modification) ; route `GET /api/insights/filter` (mois en cours et deux précédents, comme le Bilan). Une offre écartée pour deux raisons compte dans les deux ; les trois raisons les plus fréquentes, en barres. Les raisons viennent du dernier passage du filtre : après un changement de critères, elles suivent quand les offres sont refiltrées.
- **Réglages** : 46 rem ; la rubrique IA s'élargit pour la carte de la dépense (mois, « 3,20 CHF sur 20 », barre orange si le plafond est atteint, modèle ou « IA non configurée »), lue sur `GET /api/scoring`.
- **Transition** : 1,2 s au moins, entrée et sortie en 400 ms, l'image monte légèrement en apparaissant.
- **Vérifié** sur ordinateur : Réglages › IA et Compte, Profil avec critères, Suivi d'octobre, la frise ouverte.
