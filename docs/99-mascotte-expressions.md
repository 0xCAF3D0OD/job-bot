# 99 — Les trois visages de l'assistant (version 0.71.5)

> Statut : **validé** le 2026-10-19.
> **Remplacé par docs/103** (0.74.0) pour le logo : le visage du 1 ; la mascotte reste.
> Origine : ta demande du 2026-10-19, planche « La mascotte de l'Assistant » à l'appui : « modifie l'assistant, je veux que tu suives ce que dit l'image ».
> Se construit sur la 0.71.2 (docs/97). Indépendante de la 0.71.4 (PR #217).

## Ce que dit la planche

- **Le visage, seulement pour l'IA** : la mascotte ne sert qu'à l'assistant ; la marque garde le diamant au trait (docs/98).
- **L'étincelle à 4 branches ne vit que dans l'IA** : on ne la met nulle part ailleurs.
- **Trois expressions** :

| Expression | Les yeux | La bouche |
|---|---|---|
| **À l'écoute** | un œil fermé en arc, une étincelle pêche | le sourire (celui d'aujourd'hui) |
| **Réfléchit** | deux points blancs | un petit « o » au trait |
| **A trouvé** | deux étincelles pêche | un grand sourire ouvert, plein blanc |

- **Le bouton « Assistant »** : une pilule au contour bleu, la mascotte, puis « Assistant » en bleu et en gras.

## Le dessin

- **Le visage** devient **un rond**, avec **une petite pointe à droite**, au milieu, comme une bulle de dialogue. Aujourd'hui, le visage est un peu ovale et la pointe ressemble à un nez.
- **Le bleu** reste `#2340C8` (en sombre `#9DB0FF`), l'étincelle `#F4A261`, les traits blancs (en sombre `#12121F`).
- **Les épaisseurs** suivent toujours la taille, aux paliers de docs/97. Les points des yeux et le « o » grossissent aussi aux petites tailles.

## Quand chaque visage apparaît

| Endroit | À l'écoute | Réfléchit | A trouvé |
|---|---|---|---|
| **Bouton « Assistant »** (en bas à droite) | toujours | — | — |
| **En-tête du panneau** | au repos | pendant que l'assistant prépare sa réponse | 2 s après l'arrivée de la réponse, puis retour à l'écoute |
| **Ligne d'attente** (« Je consulte… ») | — | la mascotte s'ajoute devant le texte | — |
| **Devant chaque réponse** | les réponses précédentes | — | la dernière réponse, si elle vient d'arriver ; elle repasse à l'écoute à la question suivante |
| **Réponse en erreur** | oui (pas de « a trouvé » sur une erreur) | — | — |

- **Le changement de visage** se fait sans animation de forme : un fondu de 150 ms. Si « réduire les animations » est activé, il est immédiat.
- **La mascotte reste décorative** (`aria-hidden`). L'état « en train de répondre » reste annoncé par le texte de la ligne d'attente.

## Le bouton « Assistant »

- **Le contour et le texte passent au bleu de la mascotte** (`#2340C8`, en sombre `#9DB0FF`), au lieu du violet du menu. Le contour fait 2 px, le texte est en gras.
- **Le survol** : fond bleu très pâle.
- **La taille** ne change pas (`--control-h` n'est pas concerné : le bouton flotte hors des rangées).
- **Sur téléphone**, il reste un rond avec la mascotte seule.

## Ne change pas

- Le logo du site, le favicon et les icônes de l'application.
- Le violet de l'interface.
- L'icône de l'extension.

## Comment

- **`AssistantMascot`** prend une propriété `mood` : `listening` (par défaut), `thinking`, `found`.
- **Les tracés** de la planche s'ajoutent dans `brandPaths.ts` : le nouveau visage, les points, le « o », la grande bouche ; l'étincelle est réutilisée pour les deux yeux.
- **`AssistantPanel`** choisit le visage selon `busy` et la dernière réponse.

## Vérifié avant la PR

- **Tests** :
  - les trois visages (ce que chacun dessine) ;
  - le panneau : « réfléchit » pendant l'attente, « a trouvé » sur la dernière réponse, « à l'écoute » sur les précédentes et sur une erreur ;
  - toujours décorative.
- **L'audit des rangées** (docs/94) est vide.
- **Captures**, sur la démo avec l'assistant simulé, en clair et en sombre, ordinateur et téléphone :
  - les trois visages côte à côte (planche) ;
  - le bouton ;
  - le panneau au repos, pendant l'attente, après la réponse.

## Écarts

- **Le visage « réfléchit » de la ligne d'attente** n'apparaît que tant que la réponse n'a pas commencé. Dès que le texte arrive, c'est la mascotte de la réponse qui réfléchit, pour ne pas montrer deux visages à la fois. Une réponse encore vide n'a pas de mascotte.
- **Les traits sont plus épais** qu'en 0.71.2 (6,5 au lieu de 4,4 en grand), et **les étincelles plus dodues**, pour suivre la planche. Les paliers des petites tailles restent.
- **Les tracés** : l'étincelle est une fonction (`mascotSparkle`), posée sur l'un ou les deux yeux ; les points et le « o » sont des cercles.
- **Vérifié** :
  - 327 tests de l'interface (nouveaux : les trois visages ; le panneau qui réfléchit, a trouvé, puis revient à l'écoute ; l'erreur à l'écoute), lint et typecheck ;
  - audit des rangées vide ;
  - captures sur la démo (assistant simulé) : les trois visages en grand et à 24 px ; le bouton en clair, en sombre et sur téléphone ; le panneau au repos, pendant l'attente et après la réponse.
