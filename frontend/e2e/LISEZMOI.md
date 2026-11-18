# Test d'affichage

Ce test fait échouer la CI quand un écran change sans le vouloir, ou quand il montre un défaut d'affichage. Il vient de la décision de Kevin du 18.11.2026, 9 h 25, point 3 (`docs/decisions/2026-11-18-0925-controle-visuel-pr.md`).

## Ce qu'il vérifie

Il passe sur 8 écrans : Accueil, Offres, Envoyées, Rendez-vous, fiche d'une offre, Bilan, Réglages et Profil. Chaque écran est vu en 4 formats : téléphone (390 × 844) et ordinateur (1440 × 900), en clair et en sombre.

1. **Capture de référence** (`toHaveScreenshot`). La page entière est comparée à `references/<format>/<écran>.png`. Aucun pixel de différence n'est toléré. Seul l'anticrénelage d'un pixel passe, au seuil par défaut de Playwright.
2. **Contrôles a à h** (`controles.ts`). Le test échoue si :
   - a. un élément dépasse de sa carte ou de l'écran, ou un texte est coupé sans « … » ;
   - b. une pastille fait plus de 32 px de haut, ou un élément s'étire (il est mesuré une seconde fois, aligné en haut) ;
   - c. le même texte apparaît deux fois dans une même carte ;
   - d. une police autre que Figtree est demandée par le style, ou sert réellement à dessiner une lettre (la police utilisée est lue dans Chromium) ;
   - e. un texte a un contraste sous 4,5:1, ou sous 3:1 dès 18 px ;
   - f. une zone cliquable fait moins de 24 × 24 px (un lien dans une phrase est exempté) ;
   - g. un lien n'a pas de destination, un bouton n'a pas d'action (aucun écouteur de clic sur lui ni sur ses 3 parents), ou une zone cliquable n'a pas de nom ;
   - h. un texte noir est posé sur un fond sombre, ou un fond blanc apparaît en mode sombre.

`controles.e2e.ts` vérifie que chaque règle trouve bien le défaut qu'elle cherche, sur une page piégée exprès.

## Les écarts connus

`ecarts-connus.json` liste les défauts déjà connus. Chacun a une raison : soit il est dessiné ainsi sur la planche, soit il a été relevé sur main et doit être corrigé dans sa propre PR. Tout défaut absent de la liste fait échouer le test. On n'y relève jamais un seuil.

Quand une PR corrige un écart, elle retire sa ligne. Le test signale d'ailleurs un écart connu qui ne se produit plus.

## Lancer le test

    make test-affichage                              # tout
    make test-affichage ARGS="-g envoyees"           # un écran
    make test-affichage ARGS="--project=telephone-sombre"

`scripts/affichage.sh` prépare une démo à heure figée (`E2E_TIME`, par défaut le 18.11.2026 à 10 h). Il remplit la base `jobbot_e2e` (`E2E_DATABASE_URL`), lance le serveur sur le port 8300 et l'interface sur le port 5300, puis Playwright.

## Une PR qui change un écran exprès

1. Reprendre les références de l'écran : `make test-affichage ARGS="--update-snapshots -g <écran>"`.
2. Regarder chaque nouvelle image et la comparer à sa planche.
3. Joindre les nouvelles images à la PR.

Les références se prennent avec le Chromium de `@playwright/test`, à la version exacte de `package.json`. Si la CI voit une différence que le poste local ne voit pas, mettre « [maj-captures] » dans le message du dernier commit : le job « Références » reprend alors les captures sur la CI et les pousse sur la branche.
