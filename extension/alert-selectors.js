// Les formulaires « Créer une alerte » des sites (docs/142 §4) : le seul fichier à mettre à jour
// quand un site change sa page. Chaque site a un test sur une page type
// (frontend/src/extensionAlerte.test.ts, extension/fixtures/alertes/).
//
// - hosts : les adresses où chercher (exactement celles du manifeste, host_permissions).
// - forms : où se trouve le formulaire, du plus précis au plus général ; le premier visible qui
//   contient un champ e-mail et le texte de `marker` est retenu.
// - email : le champ e-mail dans ce formulaire, du plus précis au plus général.
// - marker : le texte qui dit qu'il s'agit d'une alerte (expression régulière, sans casse).
// - opener : un texte de la page qui dit que le formulaire d'alerte est là ou s'ouvre ; sert au
//   repli « Copier » quand le champ n'est pas trouvé.
// Jamais le bouton d'envoi : la personne valide elle-même.

globalThis.jobA1AlertSelectors = {
  jobup: {
    name: "jobup",
    hosts: ["www.jobup.ch", "jobup.ch"],
    forms: ['[data-cy="job-alert-modal"]', '[data-cy*="alert" i]', '[role="dialog"]', "form"],
    email: ['input[data-cy="job-alert-email"]', 'input[type="email"]', 'input[name*="mail" i]', 'input[autocomplete="email"]'],
    marker: "alerte|job-?alert|job-?abo",
    opener: "créer une alerte|alerte emploi|job-alert erstellen|create (a )?job alert",
  },
  jobsch: {
    name: "jobs.ch",
    hosts: ["www.jobs.ch", "jobs.ch"],
    forms: ['[data-cy="job-alert-modal"]', '[data-cy*="alert" i]', '[role="dialog"]', "form"],
    email: ['input[data-cy="job-alert-email"]', 'input[type="email"]', 'input[name*="mail" i]', 'input[autocomplete="email"]'],
    marker: "alerte|job-?alert|job-?abo",
    opener: "créer une alerte|alerte emploi|job-alert erstellen|create (a )?job alert",
  },
  linkedin: {
    name: "LinkedIn",
    hosts: ["www.linkedin.com"],
    forms: [".jobs-alert-modal", '[aria-labelledby*="alert" i]', '[role="dialog"]'],
    email: ['input[type="email"]', 'input[id*="email" i]', 'input[name*="email" i]'],
    marker: "alerte|job alert|jobalarm",
    opener: "créer une alerte|activer l.alerte|set alert|create (a )?job alert|jobalarm",
  },
};
