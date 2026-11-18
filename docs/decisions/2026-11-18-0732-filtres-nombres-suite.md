## Nombres des filtres : graisse, ordinateur, choix à 0, Contrat et Distance (Kevin, 18.11.2026, 8 h 32)

Réponses aux trois questions de #851 :

- Le nombre sous un choix est en 12 px, graisse 500, #596070. Figtree est chargée en variable, donc le 500 existe
  (jeton `--weight-medium`). Si ce n'était pas le cas, il faudrait prendre 400. On n'ajoute pas de fichier de police.
- Le panneau Filtres de l'ordinateur montre aussi les nombres, avec le même calcul que le téléphone : les autres
  filtres actifs sont pris en compte, et le choix actif égale « Afficher n offres ». Au-delà de 99 999 : « 100 k+ ».
- Un choix à 0 offre reste visible et sélectionnable. Il est grisé (#596070, fond inchangé), jamais masqué.
- Contrat (plusieurs choix) s'affichera « CDI · 120 », comme Statut. Distance (un seul choix) aura son nombre sous le
  choix, comme Note et Taux.

Ordre choisi le 18.11 à 8 h 42 (issue #468) : le serveur de Contrat d'abord, puis celui de Distance, dans deux PR
séparées.

Précision de Kevin (18.11.2026, 9 h 31, choix a) : sur téléphone, les nombres sous les choix excluent les offres
« Loin » tant que la liste les cache, comme « Afficher n offres ». Règle : le nombre du choix actif égale toujours
celui de « Afficher n offres ». Un test compare les deux, avec et sans offres « Loin ».

Contrôle avec la planche (règle de Kevin du 18.11.2026, 9 h 25 : planche à gauche, app à droite, écarts entourés) :
la feuille Filtres du téléphone s'écartait de la planche sans décision écrite. Elle la reprend dans cette PR : titres
de groupe en capitales 13 px gris (docs/design/regles.md §4), aide en pastille et plus courte (« À quel point l'offre
correspond à ton profil », « Provisoire : notée sur l'extrait de l'alerte »), contour des puces à 1,5 px
`--button-outline`. Le panneau de l'ordinateur garde l'aide longue, comme sa planche.
