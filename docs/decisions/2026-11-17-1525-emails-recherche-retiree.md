## E-mails d'une recherche retirée : garder une trace et filtrer (Kevin, 17.11.2026, 15 h 25)

- Une recherche d'alerte supprimée garde sa ligne, marquée retirée (`alert_searches.removed_at`, migration 0091), en pause et cachée de la page. Recréer la même recherche (mêmes mots, même lieu) reprend la ligne.
- À la collecte, une alerte dont le libellé ou l'objet contient les mots d'une recherche retirée ou en pause (« Ne plus suivre »), et ceux d'aucune recherche suivie, reste au journal mais ne donne aucune offre ; elle ne compte ni comme alerte reçue ni comme preuve ORP.
- Un e-mail qu'on ne peut rattacher à aucune recherche est gardé, par prudence.
- Option écartée : ignorer tout e-mail qui ne correspond à aucune recherche active, sans migration (risque d'ignorer à tort un libellé flou).
