## Ligne « Pourquoi » du CV, partie serveur et IA (Kevin, 16.11.2026, 13 h 37)

- Le prompt cv-v2 (une raison par changement) ne sert qu'à `make mesure-pourquoi` ; cv-v1 reste en service. La bascule se fera dans une petite PR après la mesure de Kevin.
- La vérification des citations compare des mots ou expressions entiers (frontières de mot), sans accents ni majuscules, pas des sous-chaînes : « Go » ne valide pas « Google », « Java » ne valide pas « JavaScript ».
- Les mots cités restent dans la langue de l'annonce, entre guillemets, même si la raison est en français.
- Un changement demandé par l'utilisateur via « Demander une modification du CV » n'a pas de raison de l'IA : l'API renvoie `origin: "user"` et l'interface affiche « Demandé par toi ».
- `make mesure-pourquoi` utilise 5 CV fictifs (aucune donnée de compte réel) et n'affiche que des chiffres : jetons et prix par CV, total, différence v1/v2.
