## Limites de poids par page (Kevin, 16.11.2026, 15 h 10 et 15 h 18, issue #797)

- Règle : le JS et le CSS ont des limites **par page**, fixées une seule fois et jamais relevées. Une PR qui dépasse compense sur sa propre page ou attend. Seule exception : une décision écrite dans docs/decisions/ avec l'accord de Kevin.
- Valeur : pour chaque page, la plus basse entre (a) une référence publique de budget pour un téléphone moyen en 4G et (b) la mesure de main du 16.11 + 5 %, arrondie à la centaine d'octets inférieure.
- Référence (a) : Alex Russell, « The Performance Inequality Gap, 2024 » (https://infrequently.org/2024/01/performance-inequality-gap-2024/). Pour un téléphone de milieu de gamme (Galaxy A51, Pixel 4a) sur un réseau P75 (7,2 Mbit/s, 94 ms), interactif en 3 secondes : environ 730 Kio compressés par page, dont 365 Kio de JS au plus, soit 373 760 o de JS et 373 760 o pour le reste (HTML, CSS, images, polices). Aujourd'hui (b) est plus basse partout : la page la plus lourde, Candidatures › Suivi, charge 168 Ko de JS et 70 Ko de CSS.
- Pages : les 30 vues de router.ts (avec leur page parente). Une vue sans limite fait échouer le budget : une nouvelle page reçoit ses limites dans la PR qui la crée.
- js-total et css-total sont affichés dans chaque PR mais ne bloquent plus. css-premier et js-premier disparaissent : c'est la page Aujourd'hui (accueil).
- Chaque PR affiche le poids avant/après des pages qu'elle touche : résumé de l'exécution de la CI et note sur la PR (scripts/poids-ci.sh).
- Voie 1 retenue : la voie 3 (couper du contenu utile pour gagner du poids) est exclue, la voie 2 seule (relever css-total) ne réglait rien.
- Suite, une PR chacun, captures identiques au pixel près, gain mesuré par page : (a) sortir de style.css le CSS propre aux pages ; (b) premiers pas, une étape par fichier chargée à son tour ; (c) Préparer, panneaux secondaires à la demande.
