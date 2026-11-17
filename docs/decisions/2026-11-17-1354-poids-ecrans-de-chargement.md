## Poids des premiers pas pour les écrans de chargement (Kevin, 17.11.2026, 13 h 54)

- Exception écrite à la règle des limites de poids (issue #797) : la limite `js-bienvenue-etapes` (premiers pas, toutes
  étapes) passe de 119 200 à 119 400 octets (gzip). Montant exact : +200 o, pas plus.
- Raison : les écrans de chargement du §53, validés par Kevin. À la réponse, la barre et les étapes finissent tout de
  suite (0,3 s) et le bloc est retiré à 0,4 s ; au-delà du temps prévu + 50 %, une phrase remplace la barre. L'écart
  restait après compensation dans la PR (marques en CSS, « : fait » en CSS, lancement sans JavaScript).
- Pour la suite : tout autre dépassement de cette limite, ou de n'importe quelle autre, demande une nouvelle décision
  écrite de Kevin. Pas de nouvelle hausse silencieuse.

Précision du 17.11, 16 h : l'exception n'a pas servi. Entre-temps, l'allègement des premiers pas fusionné sur main
(un fichier par étape, page téléphone à part) a ramené la page à environ 108 Ko : avec les écrans de chargement, elle
reste sous 119 200 o. La limite n'a donc pas été relevée et reste à 119 200 o. La règle pour la suite s'applique
toujours.
