# 115 — La page Alertes resserrée, les pastilles, les guides retrouvables (version 0.84.2)

> Origine : tes retours du 2026-10-21 sur la page Alertes (ordinateur et téléphone), la pastille des onglets et « Comment ça marche » masqué par erreur.

## Ce qui change

### La page Alertes

- **Le code dans sa carte** : il n'est plus en bandeau sur toute la largeur, en haut de la page. Il prend la place de « J'attends un code », en tête de la carte « Les e-mails des sites » : le site et l'heure, le code en grand, « Copier le code ». Sur téléphone, un code arrivé fait passer cette carte avant « Les alertes », le temps de le recopier.
- **Moins de texte** : le paragraphe sur la boîte de jobA1 devient une ligne en pied de carte (« Reçus en Suisse chez Infomaniak, effacés de la boîte une fois rangés. ») ; « Code de vérification » dit seulement « Il s'affiche ici dès qu'il arrive. » ; « Messages des sites », « Hors alertes, gardés 30 jours. ». La phrase d'introduction en haut de la page n'existe plus.
- **Même hauteur** : sur ordinateur, la carte des alertes et celle des e-mails des sites commencent et finissent à la même hauteur (la plus courte s'étire, son contenu reste en haut). « Alertes reçues » passe dessous, sur toute la largeur.
- **Aéré** : 1,5 rem au-dessus et au-dessous de chaque filet de la carte.

### Les pastilles de nombre (règle, docs/interface.md)

- **Une seule pastille** : pleine, couleur principale, chiffre blanc, partout la même (avant, celle des onglets de Candidatures était plus pâle).
- **Sur le coin haut droit de l'icône** quand l'icône est au-dessus du nom (barre du bas, onglets de Candidatures sur téléphone), bordée de la couleur du fond pour se détacher de l'icône. **Après le nom** quand l'icône est à côté du nom (onglets sur ordinateur).
- **Elle ne remplace pas l'icône**, même sur l'onglet actif : l'icône dit où l'on va, la pastille combien il reste à voir. C'est la règle des systèmes de téléphone (iOS, Material).

### « Comment ça marche » et « Pour bien démarrer »

- **Masquer** les fait partir tout de suite, avec **« Annuler »** pendant 6 secondes (docs/108).
- **Les retrouver** : **« Comment ça marche »** dans le menu du compte les réaffiche tous les deux et ouvre Aujourd'hui. Ils restent cachés une fois toutes leurs étapes faites.

## Vérifié

- Tests de l'interface : le code à la place de « J'attends un code », la ligne d'Infomaniak, masquer puis enregistrer au bout de 6 secondes, « Comment ça marche » dans le menu du compte. 405 tests, lint, vue-tsc.
- Captures Playwright à 1440 et 414 px : les deux cartes de même hauteur (98 → 487 px sans code, 98 → 547 avec), le code en premier sur téléphone, les pastilles sur l'icône ; pas de défilement horizontal.

## Complément 0.84.3

Tes retours du 2026-10-21 après la fusion de la 0.84.2 :

- **Le résumé des alertes** a une structure : en tête « 2 recherches suivies », la date de la dernière alerte dessous, « Gérer mes alertes » à droite ; puis une recherche par ligne, séparée par un filet, les mots en gras et le lieu dessous, l'état dans une pastille douce à droite (« Reçue · jobup », « En attente du premier envoi », « Rien reçu depuis 3 jours », « À créer ») ; « Ajouter des alertes avec l'assistant » en bas. Sur téléphone, l'état passe sous la recherche.
- **L'image de l'assistant** : à l'étape 2, « emails-tries » (une image en longueur, 800 × 245) devenait une bande de 60 px dans la colonne ; elle est remplacée par « messager » (la boîte aux lettres, une image haute). La colonne de l'image passe de 200 à 240 px.
- **La page de maintenance sans carte** : une page d'état n'est pas un élément parmi d'autres ; le dessin, le titre et le message sont posés sur le fond, centrés. Seule la ligne d'attente (« Nouvel essai… », « Réessayer maintenant ») garde un cadre, parce qu'elle se lit et se touche.

Vérifié : 405 tests, lint, vue-tsc ; captures Playwright à 1440 et 414 px (résumé, étape 2, maintenance), pas de défilement horizontal.

## Complément 0.84.4

- **Les titres collés au bord des cartes** (Rendez-vous ORP et toutes les cartes `form-card` qui commencent par un titre) : la carte avait 0,5 rem en haut, prévu pour les cartes qui commencent par un groupe de champs (déjà 1,5 rem au-dessus de leur légende). Désormais 1,75 rem en haut (1,5 rem sur téléphone, avec 1,25 rem sur les côtés au lieu de 1,1) ; 0,5 rem seulement devant un groupe de champs. Mesuré : le titre à 29 px du bord sur ordinateur (8 px avant), 25 px sur téléphone, 33 px pour une légende.
