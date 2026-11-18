## « Faire le point » en page entière sur téléphone (Kevin, 18.11.2026, 14 h 38)

- La planche FairePoint (et FairePointSombre) devient une page : `/entretien/<candidature>/faire-le-point`, avec une nouvelle route serveur et une migration (0093).
- Trois réponses, liées à l'entretien : « Comment ça s'est passé ? » (Bien, Moyen, Pas bien, obligatoire), « La suite » (J'attends une réponse, Un 2e entretien est prévu, On m'a dit non) et « Tes notes ».
- La date de relance est calculée, pas saisie : le jour de l'entretien plus 7 jours (planche : entretien le 12 nov., relance le 19). Elle ne s'affiche qu'avec « J'attends une réponse » et va dans l'agenda comme les autres suites.
- Données privées : rangées dans `interviews`, cloisonnées par compte, comprises dans l'export et effacées avec le compte.
- La note sur 5 du formulaire complet devient facultative : on n'en invente pas une à partir du ressenti. Le formulaire complet reste pour « Voir le retour » et « Ajouter un autre entretien », et sur ordinateur, qui n'a pas de planche.
