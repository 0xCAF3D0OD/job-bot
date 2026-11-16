## Fenêtre de l'extension sur « Créer une alerte » de jobup (Kevin, 16.11.2026, 21 h 25)

Section 42 de la maquette (planches ExtAlerte, ExtAlerteCodeAttente, ExtAlerteCodeColle, ExtAlerteTerminee,
ExtAlerteCodeSecours, et leurs versions Sombre). Quatre règles strictes :

1. L'extension remplit des champs mais ne clique jamais sur un bouton de jobup (ni créer, ni confirmer). Cela
   remplace, pour jobup seulement, le clic sur « Continuer » de la page du code (docs/112 §3, validé le 21.10) :
   le code est rempli, la personne clique. jobs.ch garde le clic.
2. Elle n'agit que sur la page d'alerte ouverte par la personne : l'onglet où la fenêtre a été ouverte sur le
   formulaire, et lui seul, jusqu'à l'alerte créée.
3. Le code n'est jamais écrit dans les logs, ni dans l'extension ni sur le serveur. Il passe du serveur à l'extension
   par la requête authentifiée existante (`GET /api/extension/codes?site=jobup`) et n'est pas gardé après usage
   (ni stockage du navigateur, ni message à la page jobA1).
4. Si le formulaire jobup change (sélecteurs introuvables), la fenêtre passe à l'état secours (code affiché et
   « Copier le code ») au lieu d'échouer.

Le contrat avec la page jobA1 (détection et suivi en direct) est dans
`2026-11-16-2130-extension-contrat-page.md` (PR du choix « Avec l'extension / À la main »).

Précisions de Kevin (16.11.2026, 23 h 05, sur #805) :
- Le résumé « Formulaire rempli » n'affiche que ce qui est stocké (mots et lieu, sans rayon).
- « Copier l'adresse jobA1 » seulement si le champ e-mail est resté vide, avec le libellé
  « Le champ e-mail est vide ? » + lien « Copier l'adresse jobA1 ».
- Plus tard, dans une PR à part : quand la fenêtre jobs.ch passera à la liste en 4 étapes, retirer aussi le clic
  automatique sur « Continuer » pour jobs.ch. LinkedIn garde sa fenêtre actuelle avec « J'ai créé l'alerte »
  jusqu'à nouvel ordre.
