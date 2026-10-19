# 93 — Les formations en cartes, les logos en carrés arrondis (version 0.70.6)

> Statut : **validé** le 2026-10-19.
> Origine : ta remarque du 2026-10-19, « les formations sont quasiment la même chose que les offres sur Sphere, est-ce que tu pourrais recopier la manière ; les logos des entreprises sont carrés avec bords arrondis », puis la maquette du même jour. Avec ta consigne : « les cartes toujours bien aérées, le texte toujours bien aéré ».

## 1. Les formations en cartes (Progresser › Formations)

### Une carte

| De haut en bas | Contenu |
|---|---|
| Étiquettes | Le type (Certification, Cours, Formation) en pastille sombre ; à côté, l'état s'il y en a un (« En cours », « Intéressé », « Terminée »), « à vérifier » pour une suggestion de l'IA, ou l'état du financement ORP |
| Titre | En grand (1,15 rem, gras moyen), sur trois lignes au plus, avec les mots de ton domaine surlignés comme aujourd'hui |
| Trois faits, chacun sur sa ligne avec une icône | l'organisme ; le format et la langue (« En ligne · anglais »), ou l'avancement si la formation est en cours (« Module 3 sur 6 ») ; le prix, avec « accord ORP possible » quand c'est le cas |
| En bas | un **cœur**, à droite |

- **La carte entière s'ouvre** au clic et ouvre le panneau de la formation, comme « Suivre » ou « Gérer » aujourd'hui. Il n'y a ni bouton « Voir » ni « › » (règle du clic direct, docs/57). Le lien vers la page officielle reste dans le panneau.
- **Le cœur** :
  - vide : un clic marque la formation « Intéressé » ;
  - plein : la formation est suivie ;
  - si elle est seulement « Intéressé », un nouveau clic retire la marque ;
  - si elle est en cours ou terminée, le clic ouvre le panneau, pour ne rien effacer par erreur.

  Son nom pour les lecteurs d'écran est « Marquer comme intéressé » ou « Formation suivie ».
- **Une suggestion de l'IA à vérifier** garde « Garder » et « Écarter » en bas de la carte, à la place du cœur.
- **La description quitte la carte** : elle est dans le panneau. La carte ne garde que ce qui sert à choisir.

### Aérée (ta consigne)

- **Les marges** :
  - intérieur de la carte : 1,5 rem (1,25 rem sur téléphone) ;
  - 1 rem entre les étiquettes et le titre ;
  - 1 rem entre le titre et les faits ;
  - 1,25 rem entre les faits et le bas de la carte ;
  - 0,5 rem entre deux faits.
- **L'interligne** est de 1,5 pour les faits et de 1,3 pour le titre. Les faits sont en 0,88 rem, en gris lisible et non en petit gris pâle.
- **Entre les cartes**, 1,25 rem.
- **La grille** a 3 colonnes sur ordinateur (au moins 18 rem par carte), 2 sur tablette et 1 sur téléphone. **Sur téléphone, les cartes remplacent les lignes** d'aujourd'hui.
- **Toutes les cartes d'une rangée ont la même hauteur**, et le cœur reste aligné en bas.

## 2. Les logos des entreprises en carrés arrondis

- **Le logo**, ou la lettre de secours, passe d'un rond à un carré aux coins arrondis :
  - 2,4 rem, avec des coins de 0,6 rem ;
  - 3 rem dans le détail d'une offre, avec des coins de 0,75 rem.
- **Partout où il paraît** : les Offres, le détail d'une offre, Meilleures offres et les candidatures en préparation sur Aujourd'hui.
- **Un logo image** garde son fond blanc et sa bordure fine, dans la même forme.
- **Restent ronds**, parce que ce ne sont pas des logos : le cercle de la note, l'initiale du compte et les pastilles de comptage.

## 3. Le texte aéré, en règle

Ajouté à `docs/interface.md`, pour toutes les pages à venir :
- **Une carte** a au moins 1,25 rem de marge intérieure.
- **Le texte courant** a un interligne d'au moins 1,5.
- **Entre un texte et ce qui suit**, il faut au moins 0,75 rem.
- **Si une carte se serre, on retire un élément** plutôt que de réduire les marges.

## Ce qui ne change pas

- Le panneau d'une formation (suivi, financement ORP, profil).
- Les rubriques Catalogue / Suivies, les filtres et le bouton « Domaine ».
- Les cartes de l'aperçu dans la capsule.

## Vérifié avant la PR

- **Tests** :
  - la carte : étiquettes, trois faits, avancement à la place du format ;
  - le cœur : marquer, retirer, ouvrir le panneau quand la formation est en cours ;
  - « Garder » et « Écarter » pour une suggestion ;
  - la carte entière qui ouvre le panneau.
- **Captures**, sur ordinateur, tablette et téléphone, en clair et en sombre :
  - le catalogue et les formations suivies ;
  - les Offres et le détail d'une offre, avec les logos.
- **Mesures** sur les captures : marges et écarts conformes au §1 ; pas de débordement à 390 px.

## Écarts

- **Pas de « accord ORP possible » sur le prix** : une formation ne porte pas cette information (seul l'encadré du haut parle du financement ORP). Le prix et la durée, s'il y en a une.
- **Les icônes « organisme » et « prix »** (un immeuble, une étiquette) sont ajoutées aux icônes de jobA1 ; le format garde le globe, l'avancement l'horloge.
- **Le format court** reste sur la carte, le format complet dans l'infobulle (docs/43 n° 22).
- **La grille** est limitée à 3 colonnes sur un grand écran (elle en donnait 4 à 1 440 px).
- **La carte du panneau** (`TrainingCardBody`) garde sa présentation « carte » d'avant, qui n'est plus utilisée : à retirer lors d'un ménage.
- **Vérifié** :
  - 325 tests de l'interface (nouveau : le cœur, intéressé puis retiré, et le panneau pour une formation en cours ; mis à jour : trois faits, état en étiquette, avancement, la carte entière qui ouvre le panneau, les cartes sur téléphone), lint et typecheck ;
  - captures sur la démo, sur ordinateur, tablette et téléphone, en clair et en sombre : le catalogue, les Offres avec les logos carrés ;
  - mesures : 24 px de marge intérieure (20 px sur téléphone), 16 px entre les étiquettes et le titre puis entre le titre et les faits, interligne de 1,5 ; 3, 2 et 1 colonnes ; pas de débordement à 390 px.
