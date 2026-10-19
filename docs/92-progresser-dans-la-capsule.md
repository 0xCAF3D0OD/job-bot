# 92 — Progresser dans la capsule (version 0.70.5)

> Statut : **validé** le 2026-10-19.
> Origine : ta proposition du 2026-10-19, « mettre Formation à côté de la cloche, pour la logique d'ouverture plus large, et augmenter le focus sur les deux majeurs », puis la maquette animée du même jour.

## Le principe

- **Le menu principal ne garde que le travail** : **Aujourd'hui** et **Candidatures**.
- **Progresser rejoint la capsule.** Il devient une zone entre la cloche et l'initiale, avec une étincelle et un point violet quand il y a du nouveau. Il se déroule en large et montre un **aperçu** : on lit les nouveautés sans quitter sa page.
- **La page Progresser reste.** Ses adresses et ses onglets ne changent pas. On y arrive par les liens au bas de l'aperçu.

## La capsule (ordinateur)

**Trois zones** séparées par des filets :
- **la cloche**, avec son chiffre rouge : ce qui attend une action ;
- **l'étincelle**, avec un point violet : du nouveau à lire ;
- **l'initiale ▾**.

Ce sont deux icônes et deux signaux différents, pour ne pas les confondre. Les noms pour les lecteurs d'écran sont « Alertes, 2 non lues », « Progresser, du nouveau à lire » et « Compte : kevin ».

**L'étincelle déroule la capsule à 26 rem** et montre :
1. **Actualités** : les 3 dernières de ton domaine, avec leur vignette, leur source et leur date. À défaut, les 3 dernières sur l'emploi, comme la carte d'Aujourd'hui. Un clic ouvre l'article, comme dans les Actualités.
2. **Formations en cours** : jusqu'à 3, avec leur barre d'avancement. Un clic ouvre la formation dans Progresser › Formations. Sans formation en cours, la section disparaît.
3. **En bas, après un filet** : « Toutes les actualités » et « Toutes les formations ».

**Le point disparaît** une fois l'aperçu ouvert : les nouveautés sont marquées comme vues, comme en ouvrant les Actualités. Dans la démo, le point disparaît sans rien enregistrer.

**La zone est active** quand une page de Progresser est ouverte. L'étincelle prend alors la couleur du menu, comme l'initiale pour Réglages.

## Sur téléphone (sous 820 px)

- **La capsule perd ☰** : elle garde la cloche, l'étincelle et l'initiale. L'étincelle déroule l'aperçu sur toute la largeur, comme le compte.
- **Les deux pages passent dans une barre d'onglets en bas de l'écran**, avec une icône et un nom :
  - Aujourd'hui ;
  - Candidatures, avec le nombre d'offres à examiner, comme sur l'onglet Offres.

  L'onglet de la page en cours est violet.
- **Ce qui est déjà fixé en bas monte au-dessus de la barre** :
  - le bouton de l'assistant ;
  - la barre d'action des fiches (« Postuler », « Marquer comme envoyée »).
- **Les écrans de travail cachent la barre**, comme ils prennent déjà tout l'écran (docs/75) :
  - Préparer ma candidature ;
  - l'entraînement à l'entretien ;
  - l'accueil.
- **La barre suit la zone sûre de l'écran** (`env(safe-area-inset-bottom)`). Elle mesure 3,5 rem plus cette zone.

## Ce qui ne change pas

- La page Progresser, ses onglets, ses rubriques et ses anciennes adresses (docs/90).
- Les cartes « Progresser » et « Comprendre le marché » d'Aujourd'hui.
- La cloche et le menu du compte (docs/91).

## L'assistant

**`assistant-v12`** connaît :
- les deux entrées du menu ;
- l'étincelle et son aperçu ;
- la barre d'onglets du téléphone.

## Vérifié avant la PR

- **Tests** :
  - le menu a deux entrées ;
  - l'étincelle ouvre l'aperçu (actualités, formations en cours, liens) ;
  - le point s'efface et les nouveautés sont marquées comme vues ;
  - la section des formations est absente sans formation en cours ;
  - la zone est active sur Progresser ;
  - sur téléphone, la barre d'onglets s'affiche, est absente des écrans de travail, et le bouton de l'assistant et la barre d'action ne la chevauchent pas.
- **Captures** sur ordinateur et téléphone, en clair et en sombre :
  - l'aperçu ouvert ;
  - la barre d'onglets ;
  - une fiche avec « Postuler » au-dessus de la barre ;
  - Préparer, sans la barre.

## À trancher en essayant

- **Si la barre du bas ne te plaît pas sur téléphone**, ☰ revient dans la capsule, avec les deux pages.

## Écarts

- **Pas de barre d'avancement** pour les formations : l'avancement est un texte libre (« Module 3 sur 6 »), pas un pourcentage. L'aperçu l'écrit tel quel, comme la carte d'Aujourd'hui.
- **Une formation de l'aperçu s'ouvre directement** dans Progresser › Formations : `?onglet=miennes&formation=ID` ouvre son panneau (nouveau).
- **☰ et son menu disparaissent** (`MobileMenu`), avec leurs styles : la barre d'onglets les remplace.
- **Icônes de la barre** : un calendrier pour Aujourd'hui, la boîte de réception pour Candidatures (celles des cartes d'Aujourd'hui).
- **La barre reste sous les panneaux et les écrans plein écran** (fiche d'offre, entraînement) : elle passe sous eux plutôt que d'être cachée une à une.
- **Dans la démo**, le point revient au rechargement : « vu » n'y est pas enregistré.
- **Vérifié** :
  - 324 tests de l'interface (nouveaux : l'aperçu, le point qui s'efface, la démo, la section des formations, la zone active, la barre d'onglets et Préparer qui la cache ; ceux de ☰ retirés) et 8 tests de l'assistant, lint et typecheck ;
  - captures sur la démo, sur ordinateur et téléphone, en clair et en sombre : capsule fermée, aperçu ouvert, barre d'onglets, Suivi en bas de page, Préparer sans la barre avec son bouton ; sans débordement.
