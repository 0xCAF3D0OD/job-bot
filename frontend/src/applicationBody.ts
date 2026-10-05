import type { ApplicationFormValue } from "./components/ApplicationForm.vue";

// Champs communs d'une candidature, tels que l'API les attend (une seule source : aucun
// formulaire n'oublie un champ, comme le lien de candidature ajouté en 0.7.3).
export function applicationBody(value: ApplicationFormValue) {
  return {
    sent_at: value.sent_at,
    method: value.method,
    assigned_by_orp: value.assigned_by_orp,
    company: value.company,
    company_address: value.company_address || null,
    contact_name: value.contact_name || null,
    contact_phone: value.contact_phone || null,
    job_title: value.job_title,
    location: value.location || null,
    rate_text: value.rate_text || null,
    application_url: value.application_url || null,
  };
}

// Avec le suivi, pour modifier une candidature enregistrée.
export function applicationUpdateBody(value: ApplicationFormValue) {
  return {
    ...applicationBody(value),
    status: value.status ?? "en_attente",
    status_reason: value.status_reason || null,
    status_at: value.status_at ?? null,
    interview_at: value.interview_at ?? null,
  };
}
