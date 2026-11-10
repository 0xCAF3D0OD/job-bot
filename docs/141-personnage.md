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
- Les fichiers : `frontend/public/personnage/perso-NN-nom-400.webp` (servis tels quels : pas d'adresses hachées dans le code) et `-800.webp`, 12 poses. Plus aucune pose
  sans suffixe. Les accessoires (`assets/accessoires/`) et les fonds (soleil, colline, sol, nuage, en SVG aux
  couleurs du thème) se posent autour, dans l'écran qui les utilise.

L'ancienne série d'illustrations (docs/67, `illustrations_transparentes.zip`) s'appelle désormais
`SceneIllustration.vue`. Elle disparaissait écran par écran (§4) ; depuis le 9 novembre (MODIFICATIONS_9 §6), elle
reste pour présenter et expliquer une situation : page de présentation, premiers pas, alertes d'un nouveau compte.

Budget de poids (docs/117, limite 315 Ko depuis la PR 543) : le personnage ajoute environ 1 Ko de code. En
compensation, l'ancienne série est servie elle aussi depuis `frontend/public/illustrations/`, sans adresses
hachées (48 adresses de moins dans le premier chargement) : 1,4 Ko de moins, le total passe de 314,2 Ko
(main) à 313,8 Ko.

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
| 11 | perso-01-debout, 186 px | Candidatures › Rendez-vous sans rendez-vous prévu | — | 4 |
| 12 | perso-12-celebration | Entretien décroché (mise en page de l'écran 8) | — | 4 |
| 13 | perso-02-bonjour | Compte supprimé (au revoir, sur la connexion) et refus reçu (encourageant) | — | 4 |
| 14 | perso-01-buste, 72 px de large | Téléphone : Candidatures › Rendez-vous vide (buste posé en bas de l'en-tête) | RendezVous | lot 16 |
| 15 | perso-02-bonjour-buste, 118 px | Téléphone : Connexion, clair et sombre (au lieu du personnage en pied de 140 px) | Connexion, ConnexionSombre | lot 16 |
| 16 | perso-03-cv-buste, 100 px | Téléphone : Premiers pas, étape « Ton CV » (au lieu de 122 px) | OnboardingC | lot 16 |
| 17 | perso-07-revelation-buste, 150 px | Téléphone : Premiers pas, dernière étape (au lieu de 186 px) | OnboardingC | lot 16 |
| 18 | perso-05-assis, 150 px de large, ombre ovale de 120 x 12 px | Téléphone : Notifications, Tout est lu (au lieu de la cloche dans l'arche, qui reste sur ordinateur) | Notifications, NotificationsSombre (`etats/…--tout-lu.png`) | §10.9 |

Bustes (MODIFICATIONS du 8 novembre au soir, lot 16.3) : quand le personnage partage l'écran du téléphone avec un
formulaire, seul le haut du corps reste, fondu en bas (le fondu est dans le fichier), posé sur la ligne de sol du
décor. Restent en pied : les pages d'état plein écran et toutes les pages ordinateur. `Illustration` prend le buste
avec `bust-height`, sur téléphone seulement.

Alertes : en-tête et liste vide avec le logo transformé « cloche » (`FaceTransform kind="alerts"`), pas le
personnage (PR 4).

## 4. Écarts connus

- Page introuvable : la maquette met le personnage à 290 px sur téléphone ; il est à 280 px, le plafond d'un écran
  plein (§2). 290 px sur ordinateur.
- L'ancienne série (`SceneIllustration`) reste sur des écrans hors de la liste du §3, en attendant la décision de
  Kevin : Découvrir (page publique), Assistant avant la première question (`assistant-vide`), Réglages › IA
  (`ia-vide`), Formations vide (`formations-vide`), Bilan « Trop tôt » (`trop-tot`), Préparer vide
  (`preparer-vide`), réussites « Tri terminé » et « Tout est à jour » (`reussite`). Elles sont retirées au fil des
  PR quand l'écran passe au personnage ou à une mascotte d'humeur.
- Décision du 9 novembre (MODIFICATIONS_9 §6) : la série `SceneIllustration` n'est plus « à retirer ». Elle reste
  pour la page de présentation, les premiers pas (`offres-profils`, `lecture-calme`, `formations-vide`,
  `connexion-perdue`, `lieux-carte`, `reussite`) et les alertes d'un nouveau compte (`alertes-carte`). Un seul type
  d'illustration par écran : jamais une scène et le personnage ensemble.
- Retirées (PR 2) : `connexion-perdue` (la baie de serveurs : l'erreur réseau dans la page montre la mascotte qui
  fait « non », sur ordinateur comme sur téléphone ; une nouvelle scène du même nom, l'ordinateur débranché, revient
  le 9 novembre pour la coupure pendant la lecture du CV des premiers pas, MODIFICATIONS_9 §13), `introuvable` (la personne devant un écran : l'offre
  introuvable est un écran de travail, elle garde le visage du 1), `aucune-offre` (remplacée par le personnage à la
  loupe ; l'image n'était plus utilisée).
- Maintenance et pas de connexion : 250 px sur téléphone (maquette), 290 px sur ordinateur. Les deux poses sont
  chargées d'avance, puisque le réseau peut manquer quand l'écran s'affiche.
- Candidature envoyée (PR 3) : remplace « Candidature notée » dans Ma candidature et suit aussi « Marquer comme
  envoyée » (formulaire de la liste des offres). « Je n'ai pas postulé » reste en lien discret dans Ma candidature
  (la maquette ne l'a pas, mais c'est la seule façon d'annuler). Sur ordinateur, l'en-tête « jobA1 » de l'écran
  laisse la place à celui de l'application.
- Objectif ORP atteint (PR 3) : le personnage à 240 px remplace le soleil qui saute et les confettis.
- En attente de la première collecte (PR 4) : le personnage assis à 200 px (plafond d'une liste), la tasse posée au
  sol à sa droite ; « Créer mes alertes » et « Ajouter une offre » restent.
- Rendez-vous sans rendez-vous prévu (PR 4) : le personnage debout, 160 px, à la place de `rendez-vous-vide`
  (retirée). Depuis la maquette RendezVous du 7.11.2026, 186 px, dans `OrpMeetingEmpty.vue` avec le formulaire
  du rendez-vous : la page n'a plus le personnage dans son propre fichier. Le prompt du 10 novembre
  (PR 16) réserve le personnage à capuche aux notifications : l'état montre le « 1 » de la troupe (#618).
- Entretien décroché et refus (PR 4) : un écran plein de même mise en page que l'écran 8 (`MomentScreen.vue`,
  partagé), qui remplace le Suivi jusqu'à l'action. Entretien : « Préparer l'entretien » ouvre la préparation de la
  candidature, « Plus tard » revient au Suivi. Refus : « Réponse de <entreprise>. », « Pas pour cette fois. Chaque
  candidature envoyée te rapproche d'un oui. », « Préparer la prochaine » et « Voir mes candidatures ». Pas de board :
  textes à valider. Seul le changement de statut dans le Suivi les ouvre ; un refus lu dans un courriel n'en
  ouvre pas.
- Au revoir (PR 4) : la page de connexion avec `?au-revoir=1` (le personnage qui salue y est déjà) : « Ton compte
  est supprimé. » et ce qui est effacé, à la place de « Content de te revoir. ». Une page à part coûtait 0,6 Ko de
  plus et dépassait les 315 Ko.
- Alertes (PR 4) : l'en-tête est la transition de page, qui montrait déjà la cloche. La liste vide n'existe pas
  comme telle : sans recherche en place, la page ouvre l'assistant ; le logo à la cloche se pose au-dessus, avec
  « Aucune alerte pour l'instant ». Pas de board.

## 5. Les 4 personnages du logo (MODIFICATIONS du 9 novembre, §15, PR 11)

Validé par Kevin le 9 novembre au soir : les 4 morceaux du logo (point bleu, « 1 », sourire, point orange) remplacent
le personnage à capuche partout, **sauf dans les notifications**. Composant `TroupeScene.vue` (prop `scene`, table
`src/troupe.ts`, fichiers servis depuis `public/troupe/`), variante sombre selon Réglages ou le système en Auto.

| Écran | Scène | Fichier |
|---|---|---|
| Connexion (téléphone, ordinateur), au revoir | groupe | `AuthIllustration.vue` |
| Pas de connexion | hors-ligne | `MaintenanceOverlay.vue` |
| Maintenance annoncée | maintenance | `MaintenanceOverlay.vue` |
| « jobA1 se met à jour » | mise-a-jour | `MaintenanceOverlay.vue` |
| Page introuvable | introuvable | `NotFoundView.vue` |
| Aucune offre (avec filtres, et en attente de la première collecte) | aucune-offre | `CharacterState.vue` |
| Candidature envoyée | envoyee | `ApplicationSent.vue` |
| Objectif ORP atteint, entretien décroché | objectif | `GoalReached.vue`, `MomentScreen.vue` |
| Premiers pas sur téléphone, aucun rendez-vous ORP prévu | un | `WelcomeView.vue`, `OrpMeetingEmpty.vue` |

- Jamais sur un refus, une échéance ORP dépassée, une perte de données ou une erreur grave : la réponse négative
  montre une icône sobre (`MomentScreen` avec `icon`), testé dans `personnage.test.ts`.
- La scène « ecriture » (réserve) n'est pas placée ; les originaux haute définition restent dans le zip du 9 novembre.
- L'attente : `TroupeLoader.vue`, rien sous 1 s, les 4 morceaux qui sautent l'un après l'autre jusqu'à 10 s, puis un
  texte. Placé dans le voile du premier chargement (téléphone, et Formations sur ordinateur), à 1 s au lieu de 300 ms
  et jusqu'à 10 s au lieu de 8. Sur ordinateur, les pages avec un objet gardent le logo transformé.
- Entretien décroché (absent du tableau du §15) : la scène « objectif », à confirmer par Kevin.
