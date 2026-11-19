## Ligne d'état ORP à trois états dans le détail d'une envoyée (Kevin, 18.11.2026, 10 h 48)

Le bandeau « Il manque … / Compléter » quitte le détail d'une envoyée. La ligne ORP de la carte du haut (la ligne d'état de l'en-tête) a trois états :

- « ✓ Déclarée à l'ORP » en vert, si la déclaration est faite et complète ;
- « À déclarer à l'ORP › » en bleu, avec un lien vers la fiche ORP de la candidature ;
- « À compléter pour l'ORP › » en orange, si la déclaration manque d'informations, avec un lien vers la même fiche.

L'orange est celui de la maquette : #B4631F en clair, #F2B98E en sombre, le même orange partout (Kevin, 18.11.2026, 14 h 38, après qu'on lui a proposé #8A4A16). En clair, #B4631F n'atteint que 4,43:1 sur la carte blanche (mesuré par le script de contrôle), sous le minimum de 4,5:1 de la règle e du test d'affichage : c'est un écart connu et voulu, noté dans frontend/e2e/ecarts-connus.json avec cette décision comme raison.

Même correction sur ordinateur : la carte « Pour l'ORP » disparaît, et la ligne d'état ORP va dans l'en-tête du détail.
