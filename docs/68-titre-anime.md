# 68 — Le titre animé : un personnage à la place du « 1 », qui change chaque heure (version 0.56.0)

> Statut : **validé** le 2026-10-17 (sur aperçu des 11 personnages dans la barre, en clair et en sombre), livré.
> Demande du 2026-10-17 : « customiser le titre quand on est connecté sur la plateforme : remplacer le 1 par un personnage animé qui change chaque heure ». Les 11 personnages animés sont fournis par Kevin (`Desktop/title/animees/`, dessins unDraw animés sans forme ajoutée).

## Ce qui est livré

- **Une fois connecté**, le titre de la barre du haut devient « jobA » suivi du personnage de l'heure, à la place du « 1 ». Sans connexion (connexion, « La plateforme », liens d'accès), il reste « jobA1 ».
- **Un personnage par heure**, dans l'ordre alphabétique des 11 (dancing, deep-work, learning, mindfulness, newsletter-subscriber, online-survey, publish-post, sharing-knowledge, touching-grass, visionary-technology, you-re-here) : l'heure de 0 à 23, modulo 11. Le même pour tout le monde à la même heure ; il change à l'heure pile, même si la page reste ouverte.
- **Taille** : 44 px de haut sur ordinateur, 36 px sur téléphone, assis sur la ligne du texte. Le plus large (*touching-grass*) tient sur téléphone sans déborder.
- **Couleurs du thème** : le dessin est inséré dans la page et reprend les tokens (`.drawing`), comme les dessins des pages qui chargent ; les noirs passent au gris en sombre.
- **Animation** : celle préparée par Kevin, discrète, en boucle. C'est une exception écrite à la règle « rien ne bouge tout seul en boucle » (`docs/interface.md`) ; « réduire les animations » : immobile.
- **Lecteurs d'écran** : le personnage est décoratif ; le lien du titre s'annonce toujours « jobA1, accueil ».

## Côté technique

- `frontend/scripts/personnages.mjs` prépare les fichiers de Kevin dans `src/assets/personnages/` : sans largeur ni hauteur, couleurs en minuscules, classes et animations préfixées par le nom, le « réduire les animations » limité au personnage ; il s'arrête si une forme diffère.
- Composant `BrandFigure` (choix de l'heure, minuterie jusqu'à l'heure pile, dessin chargé seulement quand il s'affiche, 5 à 14 Ko).
