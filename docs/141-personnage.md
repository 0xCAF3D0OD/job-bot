# 141 — Le personnage, le logo transformé et les mascottes d'humeur

> Statut : **demandé** par Kevin le 2026-11-06 (consigne « Illustrations jobA1 », kit `jobA1_kit_illustrations.zip`
> et maquette `jobA1_maquette_2026-11-06.zip`). Remplace les consignes précédentes sur les illustrations (kit du
> 5.11, PR 526). Livré en quatre PR : écrans 1 à 4 ; 5 à 7 ; 8 et 9 ; 10 à 13 et Alertes.

## 1. La règle

Trois figures, chacune avec son rôle :

| Figure | Rôle | Où |
| --- | --- | --- |
| **Logo transformé** (`FaceTransform` : soleil, loupe, cloche, roue dentée, cravate, flèche, anneau) | Où l'on est | Transitions de page et en-têtes. Il reste tel quel. La planche « Animations du logo, isolées » n'est pas une référence. |
| **Personnage** (`Illustration`, kit `personnage/`) | Un moment, un écran plein | La liste du §3, rien d'autre. |
| **Petites mascottes d'humeur** (`MoodAnimation` : feston, triangle, arche…) | Un état dans un petit espace | Chargement, erreur dans la page, icônes des notifications. |

- **Un seul des trois par écran.**
- **Jamais le personnage sur un écran de travail** : fiche offre, lettre, CV, formulaires.
- Garde-fou : `frontend/src/personnage.test.ts`. Aucune page n'affiche à la fois le personnage et une mascotte
  d'humeur (ou le logo transformé, ou le visage d'un état) ; seuls les écrans du §3 montrent le personnage ; les
  écrans de travail ne le montrent jamais.

Les animations de transition entre les pages et les mascottes d'humeur existantes ne changent pas.

## 2. Le composant

`frontend/src/components/Illustration.vue` :

- `<img src="…-400.webp" srcset="…-400.webp 1x, …-800.webp 2x">`, `width` et `height` fixés (le rapport de la
  pose), `alt=""`, `aria-hidden="true"`.
- `loading="lazy"`, sauf sur un écran plein (`full`), chargé tout de suite.
- Un fondu de 200 ms à l'arrivée, coupé par « réduire les animations ». Aucune autre animation.
- Hauteur : 200 px au plus dans une liste, 240 à 280 px sur un écran plein, 400 px au plus sur ordinateur
  (`height`, `desktopHeight`, bornés par le composant).
- Les fichiers : `frontend/src/assets/personnage/perso-NN-nom-400.webp` et `-800.webp`, 12 poses. Plus aucune pose
  sans suffixe. Les accessoires (`assets/accessoires/`) et les fonds (soleil, colline, sol, nuage, en SVG aux
  couleurs du thème) se posent autour, dans l'écran qui les utilise.

L'ancienne série d'illustrations (docs/67, `illustrations_transparentes.zip`) s'appelle désormais
`SceneIllustration.vue`. Elle disparaît écran par écran (§4).

## 3. Où (pose du kit → écran)

| # | Pose | Écran | Board | PR |
| --- | --- | --- | --- | --- |
| 1 | perso-03-cv | Premiers pas, étape CV (soleil, colline, sol) | OnboardingC, étape 2 | 1 |
| 2 | perso-07-revelation | « Tout est prêt. », à la place de la coche | OnboardingC | 1 |
| 3 | perso-02-bonjour | Connexion, téléphone et ordinateur | Connexion, ConnexionSombre, ConnexionOrdinateur | 1 |
| 4 | perso-06-perplexe + panneau | Page introuvable | PageIntrouvable(Sombre) | 1 |
| 5 | perso-09-cables (nouvelle tête) | Maintenance : mise à jour et maintenance annoncée | MaintenanceMaj, MaintenanceAnnoncee, MaintenanceSombre | 2 |
| 6 | perso-10-hors-ligne | Pas de connexion (distinct de la maintenance) | MaintenanceHorsLigne | 2 |
| 7 | perso-11-loupe | Aucune offre avec ces filtres (à la place du logo attentif) | AucuneOffre | 2 |
| 8 | perso-08-avion | Candidature envoyée (nouvel écran) | CandidatureEnvoyee | 3 |
| 9 | perso-12-celebration | Objectif ORP atteint (à la place du logo ravi et du soleil) | ObjectifAtteint | 3 |
| 10 | perso-05-assis + tasse | En attente de la première collecte | (mise en page de AucuneOffre) | 4 |
| 11 | perso-01-debout, 160 px | Candidatures › Rendez-vous sans rendez-vous prévu | — | 4 |
| 12 | perso-12-celebration | Entretien décroché (mise en page de l'écran 8) | — | 4 |
| 13 | perso-02-bonjour | Compte supprimé (au revoir) et refus reçu (encourageant) | — | 4 |

Alertes : en-tête et liste vide avec le logo transformé « cloche » (`FaceTransform kind="alerts"`), pas le
personnage (PR 4).

## 4. Écarts connus

- Page introuvable : la maquette met le personnage à 290 px sur téléphone ; il est à 280 px, le plafond d'un écran
  plein (§2). 290 px sur ordinateur.
- L'ancienne série (`SceneIllustration`) reste sur des écrans hors de la liste du §3, en attendant la décision de
  Kevin : Découvrir (page publique), Assistant avant la première question (`assistant-vide`), Réglages › IA
  (`ia-vide`), Formations vide (`formations-vide`), Bilan « Trop tôt » (`trop-tot`), Préparer vide
  (`preparer-vide`), réussites « Tri terminé » et « Tout est à jour » (`reussite`), offre introuvable
  (`introuvable`), erreur réseau sur ordinateur (`connexion-perdue`). Elles sont retirées au fil des PR quand
  l'écran passe au personnage ou à une mascotte d'humeur.
