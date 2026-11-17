## « Ta recherche » des Alertes : l'écran de la planche, une seule source, les critères du Profil (Kevin, 17.11.2026, 13 h 39 à 13 h 43)

- Option A (13 h 39) : sur ordinateur, Alertes vides avec au moins une recherche = l'écran des planches AlertesOrdinateurVide et AlertesOrdinateurSite. Carte « Ta recherche » (postes · lieux), puis « À créer » avec une ligne par site (jobup, LinkedIn, jobs.ch, Indeed, Job-Room), chaque ligne ouvre le volet du site.
- Texte de la carte : les 3 premiers postes puis « +n », les 2 premiers lieux puis « +n », « Toute la Suisse » sans lieu ; le texte complet pour les lecteurs d'écran. La ligne « Recherche : … » du volet d'un site reprend exactement ce texte.
- « Modifier » ouvre un volet à droite, « Ta recherche » : postes (pastilles à choix multiple, 3 au plus, « + Autre poste »), lieux (champ « Ville ou région » et pastilles), taux (pastilles, choix unique), « Enregistrer » et « Annuler ».
- Une seule source (13 h 41) : les critères du Profil (postes, lieux, taux). Enregistrer met à jour les critères, puis recalcule les recherches : chaque poste × lieu qui manque est créé, chaque recherche dont le poste ou le lieu a été retiré est supprimée. Aucun lieu = une recherche par poste, sans lieu.
- Plus de 8 recherches : « Enregistrer » désactivé, message « 8 recherches au maximum. Retire un poste ou un lieu. » relié par aria-describedby. Encadré d'information (style §62) : « Ces critères servent aussi à trier tes offres. »
- Recherche supprimée alors qu'elle était créée sur un site : toast « Pense à supprimer aussi l'alerte sur {site}, sinon il continuera de t'écrire » avec « Ouvrir {site} ». Ignorer les e-mails d'une recherche supprimée : PR serveur séparée, juste après.
- Réponses du 13 h 43 : pastilles cochées = postes recherchés ; cantons comptés comme lieux, écrits en entier (« Vaud ») ; « + Ajouter une recherche » ajoute son poste et son lieu aux critères ; taux = 7 valeurs (Tous, Dès 50 %, Dès 60 %, Dès 70 %, Dès 80 %, Dès 90 %, 100 %), mêmes pastilles dans premiers pas, Profil et volet, le filtre de liste garde ses 4 valeurs ; volet construit avec les éléments des premiers pas en attendant sa planche ; téléphone inchangé.
- Profil (ligne « Postes » en tête de « Ce que je cherche », recalcul à l'enregistrement avec la même limite) et libellés « Dès … % » des premiers pas : PR séparée, ouverte quand la planche Profil arrive.

### Réponses aux écarts de la PR (Kevin, 17.11.2026, 14 h 27)

- « Ne plus suivre » ne touche pas au Profil : l'exclusion de la combinaison poste × lieu est enregistrée (la recherche reste en base, en pause) et un recalcul ne la recrée pas. Les critères du Profil ne changent pas. Toast « Tu ne suis plus {poste}. Tes critères du Profil ne changent pas. » avec « Annuler » (le même que dans Envoyées). Retirer un poste ou un lieu partout passe par « Ta recherche ».
- Démo réduite à 3 postes × 2 lieux = 6 recherches. Aucun volet ne s'ouvre avec « Enregistrer » désactivé sans que la personne ait agi.
- Au-delà de 8 : pastille orange (fond #FDF0E2, texte #8A4A16) « {n} recherches · 8 au maximum : retire un poste ou un lieu », bouton désactivé.
- Calcul : une ville comprise dans un canton coché ne compte pas en plus (Lausanne avec Vaud = 1 lieu) ; « Toute la Suisse » remplace tous les autres lieux.
