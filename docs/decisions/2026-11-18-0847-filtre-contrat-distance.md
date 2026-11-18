## Filtres Contrat et Distance : les règles (Kevin, 18.11.2026, 8 h 47)

Issue #468, choix A : Contrat d'abord, puis Distance, une PR chacun. La limite de 4 PR ouvertes s'applique.

Contrat :
- Une catégorie par offre : CDI, CDD, Stage, Temporaire ou Non précisé. Ni Apprentissage ni Autre.
- Pas de devinette : si l'annonce ne le dit pas clairement, l'offre est « Non précisé ».
- Une migration ajoute la catégorie et classe les offres existantes.
- Une facette donne les nombres, comme Statut : « CDI · 120 ». « Non précisé » apparaît aussi, avec son nombre.
- Un choix à 0 reste visible, grisé et sélectionnable.

Distance :
- Une table des communes tirée de la liste officielle des localités de swisstopo (open data, avec coordonnées). On
  l'importe une seule fois, sans appel à un service externe.
- La distance se mesure à vol d'oiseau depuis la commune de Kevin (Renens), avec `max_km`. Libellé : « Distance
  depuis Renens », comme la maquette.
- Une offre sans lieu reconnu va dans le choix « Lieu non précisé », avec son nombre. Elle n'est jamais exclue en
  silence.
- Un nombre sous chaque choix, comme Note et Taux.

Tests : un filtre sur une valeur inconnue ne doit jamais faire disparaître d'offres sans le dire.
