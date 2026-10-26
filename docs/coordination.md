# Coordination des sessions

Trois sessions de Claude Code travaillent en même temps sur ce dépôt et sur le fichier Figma jobA1. Ce tableau fait foi.

## Territoires

| Session | Seule à modifier | Ne touche pas |
|---|---|---|
| Design | Figma ; les variables de `frontend/src/style.css` (largeurs, espacements, couleurs, mesures) ; `docs/regles-ui-ergonomie.md` ; l'en-tête | le code des pages et leurs tests ; l'outillage |
| Pages | le code des pages (`frontend/src/views`, `frontend/src/components`, `backend/`) et leurs tests | les variables de `style.css` ; les règles ; Figma (lecture seule) |
| Dépôt | l'outillage et l'organisation : `docs/coordination.md`, `docs/versions.md`, `changelog.d/README.md`, `scripts/`, `Makefile`, `.github/` | les pages, les règles, les variables ; Figma (lecture seule) |

Un fichier hors de son territoire ne se modifie pas : la session s'arrête et le signale ici et à Kevin.

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
| Tableau de coordination et réservation des numéros | Dépôt | `chore/1.6.38-coordination` | 1.6.38 | `docs/coordination.md`, `docs/versions.md`, `changelog.d/1.6.38.md` | PR ouverte |
| Résoudre les conflits des PR ouvertes | Dépôt | — | — | selon la PR | prévu (aucune PR ouverte le 26.10) |
| Mesure à 31 em partout (annuler les 24 em) | Design | `fix/1.6.31-polaris` | 1.6.35 | `style.css`, `docs/regles-ui-ergonomie.md`, Figma (variables `measure`) | fusionnée |
| En-tête : sélection, bulles, ligne au défilement | Design | `fix/1.6.37-en-tete` | 1.6.37 | `App.vue`, `style.css`, `docs/interface.md`, Figma | fusionnée |
| Micro-animations dans Figma | Design | — | à réserver | Figma | prévu |
| « jour sans recherche » devient « jour de repos » partout (assistant, e-mails, notifications, serveur) | Pages | — | à réserver | à inscrire | prévu |
| Expliquer la baisse des tests de 478 à 463 | Pages | — | à réserver | à inscrire | prévu |
| Corriger les tests qui dépendent de la date | Pages | — | à réserver | à inscrire | prévu |
