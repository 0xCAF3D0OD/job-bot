# 89 — La capsule à droite (version 0.70.2)

> Statut : **validé** le 2026-10-19.
> Origine : ta question du 2026-10-19 sur le menu de Sphere (« j'aime bien sa simplicité »), puis la maquette validée le même jour, « on essaie ».

## Le principe

- **Le menu principal ne garde que la recherche** : Aujourd'hui, Candidatures, Actualités, Formations, Profil.
- **Le reste va dans une capsule, à droite** : un seul cadre arrondi qui contient la cloche, puis ton initiale.
- **Ton initiale ouvre le menu du compte.** Ce menu existe déjà (`AccountMenu`) : aujourd'hui, il ne sert qu'aux profils d'essai et à la déconnexion.

## Ce qui change

### Sur ordinateur

| Avant | Après |
|---|---|
| 6 entrées (avec Réglages) | 5 entrées |
| La cloche, « Collecter » et l'icône du compte, séparés | Une capsule : la cloche, un filet, l'initiale ▾ |
| Le menu du compte : profil affiché, « Se déconnecter » | « Connecté : kevin », profil affiché (s'il y en a plusieurs), **Réglages**, **Données personnelles**, **Diagnostic**, **Collecter maintenant**, un filet, « Se déconnecter » |

### Sur téléphone (sous 820 px)

- **La même capsule**, avec en plus ☰ : la cloche, l'initiale et ☰.
- **☰ ne montre plus que les cinq pages.** Le compte, la collecte et Réglages passent sous l'initiale, comme sur ordinateur.

## Les détails

1. **Le menu du compte est toujours là.** Avant, il disparaissait quand il n'avait rien à proposer (un seul profil, connexion désactivée). Il porte maintenant Réglages, il reste donc visible. Sans connexion, l'initiale devient une icône de personne.
2. **« Collecter »** passe dans le menu du compte. La collecte tourne seule toutes les heures, et ce bouton est rarement utile. Il n'apparaît pas dans la démo, comme avant.
3. **Diagnostic**, aujourd'hui en bas des Réglages, est aussi dans le menu du compte. Il reste dans les Réglages.
4. **Réglages garde son adresse** (`/reglages`) et son titre « Réglages » (docs/88). Quand une page des Réglages est ouverte, l'initiale est marquée comme active : souligné à la couleur du menu.
5. **La pastille de la cloche** ne change pas. Elle reste sur la cloche, dans la capsule.
6. **Au clavier** :
   - Tab passe par la cloche, puis l'initiale ;
   - Entrée ouvre le menu, les flèches parcourent ses lignes, Échap le ferme et rend le focus à l'initiale.

   Le menu s'appelle « Compte » pour les lecteurs d'écran.
7. **Aspect** :
   - la capsule fait 2,4 rem de haut, avec une bordure fine, comme les autres boutons ronds ;
   - un filet sépare la cloche de l'initiale ;
   - l'initiale est un rond violet clair, la première lettre de l'identifiant.
8. **L'assistant** (`assistant-v10`) sait que Réglages, Données personnelles et Diagnostic s'ouvrent depuis le menu du compte, en haut à droite.

## Ce qui ne change pas

- Les pages, leurs adresses et leurs titres.
- La barre du haut sans connexion : la présentation et « Se connecter ».
- La démo, sauf « Collecter », qui reste absent.

## Vérifié avant la PR

- **Tests** :
  - le menu principal a cinq entrées ;
  - le menu du compte mène à Réglages, Données personnelles et Diagnostic ;
  - « Collecter » est dans le menu, pas dans la démo ;
  - le clavier (Échap, flèches) fonctionne ;
  - le titre de la page Réglages reste « Réglages ».
- **Captures** :
  - sur ordinateur et téléphone, en clair et en sombre ;
  - le menu du compte ouvert ;
  - une page des Réglages ouverte (l'initiale active).

## À trancher en essayant

- **Si Réglages te manque dans le menu principal**, on revient en arrière en une ligne : la capsule reste, Réglages retrouve sa place.

## Écarts

- **Page active** : quand Réglages, Données personnelles ou Diagnostic est ouvert, l'initiale est cernée à la couleur du menu, au lieu d'être soulignée. Sans initiale (la démo), l'icône de personne prend cette couleur.
- **À l'ouverture**, le premier choix (Réglages) prend le focus, pour que les flèches marchent tout de suite.
- **Le ▾** tourne quand le menu est ouvert (150 ms) ; rien si « réduire les animations » est demandé.
- **Vérifié** :
  - 319 tests de l'interface (nouveaux : le menu du compte, le clavier, la démo, les cinq entrées du menu) et 530 tests serveur, lint et typecheck ;
  - captures sur la démo, sur ordinateur en clair et en sombre et sur téléphone : capsule fermée, menu ouvert, Réglages ouvert, sans débordement.
