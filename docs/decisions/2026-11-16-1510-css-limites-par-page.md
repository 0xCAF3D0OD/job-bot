## Limites de CSS par page (Kevin, 16.11.2026, 15 h 10)

- Voie 1 de l'issue #797 : le CSS a une limite par page. On ne charge pas tout le CSS d'un coup, seulement celui de la page ouverte ; une limite par page mesure ce qui ralentit vraiment (web.dev, budgets de performance).
- Chaque page de l'application est mesurée (gzip) : le socle, plus sa vue et sa page parente. Limite = CSS de la page sur main le 16.11, + 3 %, arrondi à la centaine d'octets inférieure. Une vue sans limite fait échouer le budget.
- css-total est refixé une seule fois, dans la même PR, de la même façon : 119 450 → 123 100 (119 581 sur main + 3 %). Ce n'est pas un relèvement de plus : il devient un garde-fou, les pages font foi. css-premier disparaît (même mesure que css-accueil).
- Écartées : la voie 3 (couper du contenu utile pour 380 o, 0,3 % du CSS) et la voie 2 seule (un relèvement qui ne règle rien).
- Pas de coupe de contenu pour gagner du poids. Les #792, #794 et #798 attendent cette PR. Le JS garde ses limites actuelles.
