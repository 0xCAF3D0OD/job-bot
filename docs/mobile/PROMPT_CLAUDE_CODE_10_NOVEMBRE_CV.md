Historique. En cas de désaccord, le LISEZMOI du 13 novembre fait foi.

# Prompt Claude Code : CV jamais lu, coordonnées reprises du CV, CV redéposé (10 novembre 2026, soir)

À ajouter par-dessus `docs/mobile/` (ce paquet ne contient que les fichiers nouveaux ou modifiés).
Captures : `captures/` (état par défaut) et `captures/etats/` (un fichier par état, téléphone 390 et 360, ordinateur 1440, clair et sombre).

## Maquettes

| Fichier | Rôle |
|---|---|
| `ProfilOrdinateurCV` (+ `Sombre`) | Profil ordinateur, carte « Mon CV » avec tous les états (variable `cv`) |
| `ProfilTel` (+ `Sombre`) | Profil téléphone, **page unique** (en-tête, Mon CV, Compétences trouvées, Ce que je cherche, Mon parcours), mêmes états |
| `CoordonneesOrdinateur` (+ `Sombre`), `CoordonneesTel` (+ `Sombre`) | Profil › Coordonnées avec champs repris du CV |
| `AujourdhuiOrdinateurTravailD` | Ligne « Relire ton CV » en tête de « À faire » (variable `cvNonLu`) |
| `AccueilSmile` | Même ligne dans « À faire » sur téléphone (variable `cvNonLu`) |

## PR 21. Signal « CV jamais lu » et relecture

Où : dans la carte « Mon CV » du Profil (ordinateur et téléphone), pas dans l’en-tête de page. La carte garde la ligne du fichier ; un bloc d’état s’ajoute sous un filet, dans la même carte (pas de carte dans la carte).

États (`cv`) :
1. `relire` : CV déposé et lisible, aucun élément repris. Sous-titre du fichier « Déposé le … · pas encore lu » (orange #8A4A16). Bloc fond #FBF4EE : « Ton CV n’a pas encore été lu » + « jobA1 n’en a rien repris. Sans tes expériences ni tes compétences, les offres ne peuvent pas être notées. » + bouton plein « Relire mon CV » + « Environ 30 secondes ».
2. `cours` : « Lecture de ton CV… » + « Environ 30 secondes. Tu peux quitter cette page : on te prévient quand c’est prêt. » + barre de progression (`role="progressbar"`). Pas de bouton.
3. `lu` : fond #EAF4EE, « n éléments trouvés » + détail (expériences, compétences, formations) + bouton plein « Choisir les éléments » qui ouvre la liste existante des éléments proposés.
4. `indispo` : lecture indisponible côté serveur. « La lecture est indisponible pour le moment » + « Ce n’est pas ton fichier. Réessaie dans quelques minutes. » + bouton contour « Réessayer ».
5. `illisible` : texte illisible. « Le texte de ce CV n’est pas lisible » + « C’est sans doute une image scannée. Dépose un PDF exporté depuis Word, ou remplis ton profil à la main. » + bouton tonal « Déposer un autre fichier » + lien « Remplir à la main » (ouvre l’étape « Complétons ton profil », PR 17).

Règles :
- Le bloc d’état est en `role="status"` `aria-live="polite"` : chaque changement d’état est annoncé.
- Un seul bouton plein par état.
- Quand l’état n’est pas `lu`, « Compétences trouvées » affiche « Rien pour l’instant. Relis ton CV ou ajoute-les à la main. » + lien « Ajouter une compétence » (cible 44 px).
- La lecture continue si la personne quitte la page ; à la fin, notification « Ton CV est lu : 12 éléments à choisir ».
- Le bouton « Proposer à partir du CV » de Documents et certificats déclenche la même lecture et les mêmes états.

## PR 22. Rappel dans Aujourd’hui

Tant qu’un CV lisible n’a jamais été lu : ligne en tête de « À faire » (ordinateur et téléphone) : « Relire ton CV » + « Sans lui, tes offres ne sont pas notées · 30 secondes » (orange), icône document avec point d’exclamation, lien vers Profil. La ligne disparaît dès que l’état passe à `lu`.

## PR 23. Coordonnées reprises du CV

- En haut du formulaire, bloc info (fond #E8ECFB, `role="status"`) : « n champs repris de ton CV » + « Vérifie-les puis enregistre. Rien n’est enregistré avant. » (n = nombre réel de champs pré-remplis).
- Sur chaque champ pré-rempli depuis le CV : marque « Du CV » à côté du libellé (12 px, fond #E8ECFB, texte #1A3496). L’e-mail du compte n’a pas de marque.
- Après « Enregistrer », les marques et le bloc disparaissent. « Annuler » vide les valeurs pré-remplies non enregistrées.
- Phrase sous les champs : « Tes coordonnées servent seulement à l’en-tête de tes lettres. Elles ne sont jamais envoyées à l’IA. » (vrai aujourd’hui : extraction sans IA, PR #623 ; ne pas changer ce comportement).
- `autocomplete` : name, email, street-address, postal-code, address-level2, tel.
- Téléphone : boutons pleine largeur, « Enregistrer » au-dessus de « Annuler ».

## PR 24. CV redéposé

Remplacer « CV déposé. » par un message dans la carte « Mon CV » (même bloc d’état, avec bouton « Fermer » en croix 44 px, jamais un message qui disparaît tout seul) :
- `jamais` (même fichier, jamais lu) : « Ce CV était déjà déposé, mais il n’a jamais été lu » + « Relis-le pour reprendre tes expériences et faire noter tes offres. » + bouton plein « Relire mon CV ».
- `deja` (même fichier, déjà lu) : « Ce CV est déjà dans ton profil » + « C’est le même fichier, déjà lu le … Rien n’a changé. » Pas d’action.
- `nouveau` (fichier différent) : « Nouveau CV déposé » + « Relis-le pour mettre à jour ton profil. Tu choisiras ce que tu gardes. » + bouton plein « Relire mon CV » + lien « Plus tard ».
« Relire mon CV » enchaîne sur l’état `cours` puis `lu` (PR 21).

## Profil téléphone

`ProfilTel` est la maquette de la décision B (page unique, sans onglets) pour le téléphone : à utiliser pour la PR 20.

## Vérifications
- Captures avant/après à 360, 390 et 1440 px, clair et sombre, pour chaque état.
- `outils/audit-grille.js` sur `ProfilTel` et `CoordonneesTel` : 0 écart.
- Lecteur d’écran : les changements d’état de la carte CV sont annoncés.
- Typographie : apostrophes ’, espace fine insécable avant : ; ? !
