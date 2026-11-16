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
//
// Le suivi de l'alerte jobup (section 42 de la maquette, docs/142 §4 bis), jobup seulement :
// - code : le champ du code de confirmation, du plus précis au plus général ; plusieurs cases d'un
//   chiffre sont aussi reconnues. Introuvable : la fenêtre passe à l'état secours (code à copier).
// - codeAsk : le texte qui dit que la page demande le code.
// - done : le texte qui dit que l'alerte est créée.
// - codeHosts : les pages où jobup demande le code (accès donné une fois, docs/112).

globalThis.jobA1AlertSelectors = {
  jobup: {
    name: "jobup",
    hosts: ["www.jobup.ch", "jobup.ch"],
    forms: ['[data-cy="job-alert-modal"]', '[data-cy*="alert" i]', '[role="dialog"]', "form"],
    email: ['input[data-cy="job-alert-email"]', 'input[type="email"]', 'input[name*="mail" i]', 'input[autocomplete="email"]'],
    marker: "alerte|job-?alert|job-?abo",
    opener: "créer une alerte|alerte emploi|job-alert erstellen|create (a )?job alert",
    code: ['input[autocomplete="one-time-code"]', 'input[name*="code" i]', 'input[id*="code" i]', 'input[data-cy*="code" i]', 'input[inputmode="numeric"]'],
    codeAsk: "code de (vérification|confirmation)|(entre|entrez|saisis|saisissez) (le|ton|votre) code|bestätigungscode|verification code|enter (the|your) code",
    done: "alerte (emploi )?(a été |est )?(créée|activée|enregistrée|confirmée)|job-?alert (wurde )?(erstellt|aktiviert)|alert (has been )?(created|activated)",
    codeHosts: ["auth.jobup.ch"],
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
