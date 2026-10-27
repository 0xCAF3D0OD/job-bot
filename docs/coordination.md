# Coordination des sessions

Trois sessions de Claude Code travaillent en même temps sur ce dépôt et sur le fichier Figma jobA1. Ce document fixe
leurs territoires et leurs règles ; le travail en cours se lit dans les PR ouvertes.

## Territoires

| Session | Seule à modifier | Ne touche pas |
|---|---|---|
| Design | Figma ; les variables de `frontend/src/style.css` (largeurs, espacements, couleurs, mesures) ; `docs/regles-ui-ergonomie.md` ; l'en-tête | le code des pages et leurs tests ; l'outillage |
| Pages | le code des pages (`frontend/src/views`, `frontend/src/components`, `backend/`) et leurs tests | les variables de `style.css` ; les règles ; Figma (lecture seule) |
| Dépôt | l'outillage et l'organisation : `docs/coordination.md`, `changelog.d/README.md`, `scripts/`, `Makefile`, `.github/` | les pages, les règles, les variables ; Figma (lecture seule) |

Un fichier hors de son territoire ne se modifie pas : la session s'arrête et le signale à Kevin.

## Une PR ne touche aucun fichier partagé

Deux PR qui modifient le même endroit d'un fichier entrent en conflit dès que l'une est fusionnée. Les fichiers que
toutes les PR modifiaient (les tableaux de réservation, `CHANGELOG.md`) ne sont donc plus édités à la main :

- **Le numéro de version est donné à la fusion.** Une PR dépose `changelog.d/<sujet>.md` (minuscules, chiffres et
  tirets, par exemple `boutons-segmentes.md`), sans numéro. Sur main, après la fusion, l'action `changelog.yml` lui
  donne le numéro suivant dans l'ordre de fusion, le renomme en `changelog.d/X.Y.Z.md` et assemble `CHANGELOG.md`.
  La CI refuse une PR qui ajoute un fichier `changelog.d/X.Y.Z.md`.
- **Pas de numéro avant la fusion** : ni dans la branche (`fix/<sujet>`, `feat/<sujet>`), ni dans le titre de la PR,
  ni dans les commits, ni dans un dossier de captures (`docs/captures/<sujet>/`). Le numéro se lit après la fusion,
  dans `changelog.d/` ou `CHANGELOG.md`.
- **Les tâches en cours se suivent dans les PR ouvertes**, plus dans un tableau. La description de chaque PR donne la
  session, la tâche et la liste des fichiers touchés.

## Avant de commencer une tâche

1. Partir de main à jour.
2. Lire les PR ouvertes (`gh pr list`, puis `gh pr view <n> --json files`) : si un fichier qu'on va toucher est déjà
   modifié par la PR d'une autre session, ne pas le modifier ; le signaler à cette session et attendre sa fusion.
3. Prévenir les autres sessions avant de toucher à un fichier partagé, et quand on ouvre une PR.
4. Se remettre à jour sur main juste avant d'ouvrir la PR. Une PR ne dépend jamais de la branche d'une autre session.
5. La CI doit être au vert avant d'annoncer une PR. Compte rendu court, en français, avec la liste des fichiers touchés.

L'historique des anciens tableaux (jusqu'au 27.10) : `docs/coordination-historique.md`.
