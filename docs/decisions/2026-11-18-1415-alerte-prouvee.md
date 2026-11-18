## Alertes : « J'ai créé l'alerte » ne suffit plus, il faut un e-mail du site (Kevin, 18.11.2026, 15 h 13)

- Constat de Kevin (compte factice d'infirmier, 18.11) : l'alerte jobup s'affichait « Active · en attente du premier envoi » et l'étape « Ta première alerte est créée » était cochée, alors que l'alerte n'avait jamais été créée sur jobup. Le bouton « J'ai créé l'alerte » suffisait à tout cocher.
- Règle : une alerte n'est active qu'avec un e-mail du site arrivé dans la boîte jobA1 du compte (code de vérification, message ou alerte), au plus un jour avant la déclaration. Sinon, elle est « À confirmer », dans la famille « À confirmer » de la planche AlertesTel (et AlertesOrdinateur), avec « Coller le code » pour jobup, qui ouvre le panneau du site où le code s'affiche.
- Premiers pas : l'étape 3 n'est faite qu'avec cette preuve, ou une alerte reçue. Remplace la règle du 14.11 (« J'ai créé l'alerte » ou reçue). La fonction de l'exploitant `first_steps_progress` suit (migration 0094).
- Rappel : 24 h après la déclaration sans alerte reçue, « Vérifier 1 alerte » sur Aujourd'hui, que l'alerte soit à confirmer ou non.
- Le reste du plan de Kevin du 18.11 (bouton unique « Créer ma première alerte », parcours en 3 étapes hors des premiers pas, valeurs à copier, une action par état, bandeau au premier e-mail, rappel « Vérifier mon filtre Gmail ») vient dans une PR à part.
