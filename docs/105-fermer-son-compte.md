# 105 — Fermer son compte (version 0.75.1)

> Statut : **validé** le 2026-10-20.
> Origine : ta demande du 2026-10-20, « il faudrait que l'utilisateur puisse fermer son compte ». La suppression existait déjà (docs/65 §6), au fond de Réglages › Compte ; ton choix : **« Fermer mon compte »** et **une entrée dans le menu du compte**.

## Ce qui change

1. **Les mots** : « Supprimer mon compte » devient **« Fermer mon compte »**, et « Supprimer définitivement » devient « Fermer définitivement ». La phrase de confirmation commence par « Fermer ton compte efface tout ». La page Données personnelles dit « Fermer ton compte ».
2. **Le menu du compte** (l'initiale, en haut à droite) : une ligne **« Fermer mon compte »**, juste avant « Se déconnecter ». Elle ouvre Réglages › Compte (`/reglages?rubrique=compte&fermer=1`) avec **la confirmation déjà ouverte** et le focus sur le mot de passe.

## Ne change pas

- **La fermeture elle-même** : mot de passe demandé, export proposé avant, tout effacé, fichiers compris (`POST /api/account/delete`).
- **Qui peut fermer** : un compte invité seulement. Ni l'exploitant, ni la démo, ni une installation sans connexion. Pour eux, la ligne du menu n'apparaît pas, et le lien direct n'ouvre rien.

## Vérifié

- Tests : la ligne du menu pour un compte invité (et son adresse), absente pour l'exploitant et en démo ; « Fermer mon compte » et « Fermer définitivement » ; venu du menu, la confirmation ouverte et le focus sur le mot de passe ; l'exploitant venu par le lien direct ne voit rien.
- 346 tests de l'interface, lint et typecheck.

## Complément 0.77.4 : sur téléphone

Ta capture du 2026-10-20 (compte « eliot », 414 px, ouvert depuis le menu) : la confirmation dépassait de l'écran, et toute la page défilait sur le côté.

- **La cause** : le champ du mot de passe, « Fermer définitivement » et « Annuler » sur une seule ligne qui ne passait pas à la ligne, plus large que l'écran ; l'ouverture depuis le menu faisait en plus défiler la page vers ce champ.
- **Après** : la même confirmation dans la page que partout (docs/108 §1) : la phrase, « Ton mot de passe pour confirmer » et le champ sur toute la largeur, puis « Fermer définitivement » (grisé tant que le champ est vide) et « Garder ». Entrée dans le champ ferme aussi le compte.
- **Le champ du mot de passe** prend enfin le style des autres champs (il avait l'aspect brut du navigateur, gris foncé en sombre). Le style vaut pour tous les champs `password` et `url` de l'interface.
- **Vérifié** : un test (grisé sans mot de passe, puis la fermeture) ; capture à 414 px en clair et en sombre, largeur de la page mesurée à 414 px (rien ne dépasse) ; tests complets, lint, typecheck.

