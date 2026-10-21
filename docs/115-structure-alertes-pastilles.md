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
