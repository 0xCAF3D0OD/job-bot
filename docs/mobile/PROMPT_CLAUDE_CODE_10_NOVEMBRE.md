# Prompt Claude Code, 10 novembre 2026

À installer par-dessus le paquet du 9 novembre. Ce fichier prime sur les précédents pour les points ci-dessous.
Maquettes à jour : `OffreProvisoire`, `CandidaturesOrdinateurB`, `CandidaturesOrdinateurBSombre`, `CandidaturesOrdinateurAjouter`, `CandidaturesOrdinateurSpontanee`, `CandidaturesOrdinateurStatut`.
Ordre des PR : 13, 14, 15, 16. Pour chaque PR : captures avant/après à 360 et 390 px (téléphone) et 1440 px (ordinateur), en clair et en sombre.

## PR 13. Annonce complète lue automatiquement (téléphone et ordinateur)

Décision : l'utilisateur ne doit pas aller chercher une information que jobA1 peut récupérer seul (ISO 9241-110, adéquation à la tâche ; loi de Tesler). On ne lui demande le texte que si la lecture automatique échoue.

- Quand une offre arrive par une alerte avec un lien, récupérer le texte complet en arrière-plan (tâche asynchrone) : récupération du HTML, extraction du contenu principal, respect de robots.txt et des conditions des sites, délai maximal 15 s, 1 seul nouvel essai.
- États de la carte de la note (voir `OffreProvisoire`, variable `st`) :
  - `reading` (par défaut) : note provisoire visible avec le badge « Provisoire », sous-titre « Calculée sur l’extrait de l’alerte, en attendant l’annonce complète. », puis une ligne « jobA1 lit l’annonce complète… » avec un petit indicateur circulaire (`role="status"`, `aria-live="polite"`). Aucun bouton.
  - `done` : note recalculée, badge « Provisoire » retiré, message « Note refaite sur l’annonce complète. », texte complet dans « Le poste ».
  - `refused` (blocage, connexion obligatoire comme LinkedIn, 404, annonce expirée) : bloc « jobA1 n’a pas pu lire l’annonce », texte « Ce site bloque la lecture automatique. Colle le texte : la note sera refaite tout de suite. », un bouton tonal « Coller le texte » (ouvre la feuille de collage existante) et un lien « Ouvrir l’annonce ».
- Supprimer le bouton « Lire l’annonce » et le bandeau orange « Il manque l’annonce complète ».
- Téléphone : le bloc reste DANS la carte (séparé par un filet), jamais en pleine largeur qui dépasse le contour. Pas d’espace vide sous le bloc.
- Journaliser la raison de l’échec par domaine, pour voir quels sites posent problème.

## PR 14. Ligne profil de l’écran Compte (téléphone, clair et sombre)

Modèle : `CompteImage`. Cause probable du bug : le badge crayon est positionné par rapport à un conteneur plus large que l’avatar.
- Conteneur `position: relative` de la taille exacte de l’avatar : `display: inline-flex; width: 52px; height: 52px; flex: none;` sans padding.
- Avatar 52 × 52 rond : image choisie dans Profil si elle existe, sinon les initiales (clair #E8ECFB / #2445C2, sombre #232B45 / #AEBDFF).
- Badge 22 × 22 rond, `right: -3px; bottom: -3px`, fond = fond de la carte, bordure 1 px (#E5E2D9 clair, #3A352E sombre), crayon 12 px, `aria-hidden="true"` : toute la ligne est le lien.
- Ne pas reprendre les tailles de ProfilOrdinateur (72 / 28 px), réservées à l’ordinateur.
- Ligne : padding 14 px, gap 14 px. Sous-titre « CV, compétences, postes recherchés » sur 2 lignes maximum, sans troncature.

## PR 15. Détail d’une offre (téléphone)

- Lien du bas de la carte de la note : texte aligné à gauche (même retrait que le contenu de la carte), chevron à droite, libellé « Le détail de la note ». Ne pas reprendre le retrait de 98,5 px de l’ordinateur.

## PR 16. Onglet Rendez-vous (téléphone, clair et sombre)

- Si un rendez-vous passé attend « Noter ce qui a été convenu », la section « À noter » s’affiche EN PREMIER, avant le formulaire.
- Titre de l’état vide : « Aucun rendez-vous à venir ».
- Contenu : `padding-bottom` = hauteur de la barre du bas + dépassement du bouton central + 16 px. Rien ne passe dessous (WCAG 2.4.11).
- Champs Date et Heure sur une même ligne (Date `flex: 1.4`, Heure `flex: 1`), comme dans la feuille « Ce qui a été convenu ».
- Texte d’exemple du lieu : « Ex. : ORP Renens, rue de Lausanne 35 ».
- Ne pas changer la casse du lieu saisi (garder « EPFL »).
- Carte à noter : titre « Rendez-vous ORP », sous-titre « Vendredi 30 octobre, 11 h · EPFL ».
- Supprimer le titre « Derniers rendez-vous ORP » : la ligne « Carnet ORP » suffit.
- Personnage de l’état vide : en attente, la nouvelle scène sera livrée dans un prochain paquet. Ne pas utiliser le personnage à capuche (réservé aux notifications).

## Typographie (partout)
- Espace fine insécable (U+202F) avant « : ; ? ! » dans tous les textes en français.
- Apostrophe typographique ’ partout (pas d’apostrophe droite).
