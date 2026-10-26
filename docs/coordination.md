# Coordination des sessions

Trois sessions de Claude Code travaillent en même temps sur ce dépôt et sur le fichier Figma jobA1. Ce tableau fait foi.

## Territoires

| Session | Seule à modifier | Ne touche pas |
|---|---|---|
| Design | Figma ; les variables de `frontend/src/style.css` (largeurs, espacements, couleurs, mesures) ; `docs/regles-ui-ergonomie.md` ; l'en-tête | le code des pages et leurs tests ; l'outillage |
| Pages | le code des pages (`frontend/src/views`, `frontend/src/components`, `backend/`) et leurs tests | les variables de `style.css` ; les règles ; Figma (lecture seule) |
| Dépôt | l'outillage et l'organisation : la structure et les règles de `docs/coordination.md` et `docs/versions.md`, `changelog.d/README.md`, `scripts/`, `Makefile`, `.github/` | les pages, les règles, les variables ; Figma (lecture seule) |

Un fichier hors de son territoire ne se modifie pas : la session s'arrête et le signale ici et à Kevin.

Exception : **chaque session tient elle-même ses propres lignes** dans les deux tableaux (`docs/coordination.md` et
`docs/versions.md`), dans la PR de sa tâche ou par une PR courte. Elle ne modifie pas les lignes des autres sessions.

## Avant de commencer une tâche

1. Lire ce tableau.
2. Y inscrire sa tâche, sa branche, son numéro de version (réservé dans `docs/versions.md`) et les fichiers qu'elle touchera.
3. Si un fichier est déjà pris par une autre session, ne pas le modifier : le signaler et attendre.
4. Mettre sa ligne à jour à chaque changement d'état : prévu, en cours, PR ouverte, fusionnée.

Partir de main à jour, et se remettre à jour juste avant d'ouvrir la PR. Une PR ne dépend jamais de la branche d'une autre session. La CI doit être au vert avant d'annoncer une PR.

## Tableau

| Tâche | Session | Branche | Version | Fichiers touchés | État |
|---|---|---|---|---|---|
| Un fichier par version dans `changelog.d/` | Dépôt | `chore/1.6.36-changelog-d` | 1.6.36 | `changelog.d/`, `scripts/changelog.py`, `.github/workflows/`, `Makefile`, `CHANGELOG.md` | fusionnée |
| Renommer la PR 344 (1.6.31 pris par la PR 341) | Dépôt | `fix/1.6.31-polaris` | 1.6.35 | titre de la PR | fusionnée |
| Tableau de coordination et réservation des numéros | Dépôt | `chore/1.6.38-coordination` | 1.6.38 | `docs/coordination.md`, `docs/versions.md`, `changelog.d/1.6.38.md` | fusionnée |
| Inscriptions de la session Design dans les tableaux | Dépôt | `chore/1.6.40-inscriptions` | 1.6.40 | `docs/coordination.md`, `docs/versions.md`, `changelog.d/1.6.40.md` | fusionnée |
| Tableaux à jour (1.6.40 fusionnée, 1.6.41 précisée) | Dépôt | `chore/1.6.42-tableaux` | 1.6.42 | `docs/coordination.md`, `docs/versions.md`, `changelog.d/1.6.42.md` | fusionnée |
| Chaque session tient ses lignes ; inscription de la session Pages | Dépôt | `chore/1.6.44-inscriptions` | 1.6.44 | `docs/coordination.md`, `docs/versions.md`, `changelog.d/1.6.44.md` | PR ouverte |
| Résoudre les conflits des PR ouvertes | Dépôt | — | — | selon la PR | prévu (aucune PR ouverte le 26.10) |
| Mesure à 31 em partout (annuler les 24 em) | Design | `fix/1.6.31-polaris` | 1.6.35 | `style.css`, `docs/regles-ui-ergonomie.md`, Figma (variables `measure`) | fusionnée |
| En-tête : sélection, bulles, ligne au défilement | Design | `fix/1.6.37-en-tete` | 1.6.37 | `App.vue`, `style.css`, `docs/interface.md`, Figma | fusionnée |
| Règles §6 : la séparation sous l'en-tête en fondu au défilement | Design | `docs/regles-6-fondu` | 1.6.39 | `docs/regles-ui-ergonomie.md`, `docs/coordination.md`, `docs/versions.md`, `changelog.d/1.6.39.md` | fusionnée (#355) |
| Boutons segmentés selon Material 3 (rail neutre, pastilles ajustées au texte, actif comme l'onglet de l'en-tête) : filtre Note des Offres et période du Bilan ; règle §4 | Design | `fix/1.6.41-segmentes` | 1.6.41 | Figma (Segment, Sélecteur segmenté, variable `control-inner-h`, filtre Note de l'écran Candidatures), `docs/regles-ui-ergonomie.md` (§4), `frontend/src/style.css` (règles `.segmented` et `.score-choice`, variable `--control-inner-h` ; aucun `.vue`), `changelog.d/1.6.41.md` | fusionnée (#351) |
| Micro-animations dans Figma : objectif ORP du mois atteint, réponse d'un employeur reçue, tri du jour terminé, étape des premiers pas franchie, premier entretien obtenu, bouton Assistant (visage → « Fermer ») ; « Candidature envoyée » existe déjà (modèle) | Design | — | — | Figma seulement (aucun fichier du dépôt) | en attente (après la revue 1.6.46, demande de Kevin) |
| Revue de la plateforme : 1. menu sans bulle, soulignement ; 2. cloche et avatar en boutons ronds ; 3. Offre du jour en pile, phrase « pourquoi » ; 4. un seul « + Ajouter » ; 5. filtre Note en ligne ; 6. focus de la recherche entier | Design | `design/1.6.46-revue` | 1.6.46 | Figma (1 à 6) ; code de l'en-tête (1, 2) : `App.vue` (en-tête), `NotificationBell.vue`, `AccountMenu.vue` et leurs tests, suppression de `HeaderCapsule.vue`, `HeaderCapsule.test.ts`, `useCapsule.ts` ; `style.css` (en-tête, `--accent-band`) ; règles : `docs/regles-ui-ergonomie.md` §4, `docs/interface.md`, `docs/129-a-faire-range.md` ; `changelog.d/1.6.46.md`. Le code de 3 à 6 (Aujourd'hui, écran de tri, « + Ajouter », ligne Note, marge des filtres) revient à la session Pages | fusionnée (#356) pour l'en-tête et les règles ; pages : planche transmise à Pages (1.6.47) |
| Règle §3 : la bande d'action | Design | `docs/1.6.48-bande-action` | 1.6.48 | `docs/regles-ui-ergonomie.md` (§3), `docs/coordination.md`, `docs/versions.md`, `changelog.d/1.6.48.md` | PR ouverte |
| Composant « Bande d'action » | Design | `feat/1.6.49-bande-action` | 1.6.49 | un composant de `frontend/src/components` et son test, `style.css` | prévu (après la 1.6.48) |
| Bande d'action · planche 1 : Offres (« Commencer le tri ») | Design | — | — | Figma (page « Planche · Bande d'action ») ; le code ira à Pages | planche presque validée |
| Bande d'action · planche 2 : Suivi (relances, ou preuves en retard en priorité) | Design | — | — | Figma ; le code ira à Pages | prévu |
| Bande d'action · planche 3 : Rendez-vous (le prochain, « Préparer ») | Design | — | — | Figma ; le code ira à Pages | prévu |
| Bande d'action · planche 4 : Alertes (une alerte qui ne reçoit rien, un code attendu, « Vérifier ») | Design | — | — | Figma ; le code ira à Pages | prévu |
| Bande d'action · planche 5 : Bilan (ce qui marche le mieux, en action) | Design | — | — | Figma ; le code ira à Pages | prévu |
| « jour sans recherche » devient « jour de repos » partout (assistant, e-mails, notifications, serveur) | Pages | `fix/1.6.43-jour-de-repos` | 1.6.43 | `backend/src/jobbot/llm/prompts/assistant-v21.md` (nouveau), `assistant/service.py`, `notify/service.py`, `rhythm/service.py`, `auth/service.py` ; 12 fichiers de `backend/tests` (test_assistant, test_assistant_actions, test_connexion, test_contacts, test_insights, test_offer_filters, test_revue_0_33_1, test_revue_pages, test_revue_protections, test_rhythm, test_spontaneous, test_trainings) ; `frontend/src/components/InterviewForm.test.ts` ; `changelog.d/1.6.43.md` | fusionnée (#353) |
| Expliquer la baisse des tests de 478 à 463 | Pages | `fix/1.6.43-jour-de-repos` | 1.6.43 | aucun : la 1.6.25 a retiré les 16 tests d'Actualités et en a ajouté 1 au Bilan | expliquée |
| Corriger les tests qui dépendent de la date | Pages | `fix/1.6.43-jour-de-repos` | 1.6.43 | dans les fichiers de tests de la ligne « jour de repos » | fusionnée (#353) |
| Passe de concision des textes de l'interface (NN/g, « Concise, Scannable, and Objective ») : boutons et liens en 1 à 3 mots avec un verbe ; une phrase de conclusion ; points forts et manques d'une offre en 3 puces de 12 mots au plus ; aides des Réglages et textes du Rendez-vous en une phrase, le reste replié ; rien de répété entre la phrase du haut et les cartes | Pages | `fix/1.6.45-concision` | 1.6.45 | d'abord aucun : un tableau avant/après à valider par Kevin ; ensuite les `.vue` concernés, leurs tests et la consigne de l'IA pour les points forts (liste précise dans la PR) | prévu (tableau avant/après en cours) |
| Revue 1.6.46, Offres : un seul « + Ajouter » (menu : Ajouter une offre, Postuler spontanément), la Note en ligne « Note · Toutes › », la marge de la colonne des filtres (anneau de focus entier) | Pages | `fix/1.6.47-offres` | 1.6.47 | `frontend/src/views/OffersView.vue`, `OffersView.test.ts`, `components/OfferFiltersPanel.vue`, `components/MoreMenu.vue` (déclencheur à libellé), `style.css` (règle `.filters-column`, aucune variable), `changelog.d/1.6.47.md`, ces deux tableaux | PR ouverte |
| Revue 1.6.46, Aujourd'hui en une colonne (« Tri du jour. » dans la bande d'action, « À faire aujourd'hui. », « Mois ORP. », « À retenir. ») et l'écran de tri des offres du jour (« Commencer le tri », aussi depuis Offres) | Pages | — | à réserver | `TodayView.vue`, un nouvel écran de tri et sa route, leurs tests | prévu (après la 1.6.49, le composant ActionBand) |
