// Vérification au fil de la saisie (docs/29 §4) : un message par champ, affiché en le quittant,
// effacé dès qu'on corrige. Le serveur vérifie de nouveau à l'enregistrement.

import { ref } from "vue";

export type Check = (value: string) => string | null;

export const postcode: Check = (value) => (!value.trim() || /^\d{4}$/.test(value.trim()) ? null : "Quatre chiffres, par exemple 1020.");

export const email: Check = (value) =>
  !value.trim() || /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(value.trim()) ? null : "Une adresse complète, par exemple nom@exemple.ch.";

export const webAddress: Check = (value) => {
  const text = value.trim();
  if (!text) return null;
  return /^(https?:\/\/)?[^\s/.]+(\.[^\s/.]+)+(\/\S*)?$/i.test(text) ? null : "Une adresse web, par exemple linkedin.com/in/ton-nom.";
};

export const secureAddress: Check = (value) => {
  const text = value.trim();
  if (!text) return null;
  return /^https:\/\/[^\s/.]+(\.[^\s/.]+)+(\/\S*)?$/i.test(text) ? null : "Une adresse qui commence par https://.";
};

// Adresses d'expédition d'un site suivi : adresses e-mail ou domaines, séparés par des espaces.
export const senders: Check = (value) => {
  const items = value.split(/[\s,;]+/).filter(Boolean);
  if (!items.length) return "Au moins une adresse d'expédition ou un domaine.";
  const bad = items.find((item) => !/^([^\s@]+@)?[^\s@.]+(\.[^\s@.]+)+$/.test(item));
  return bad ? `« ${bad} » n'est ni une adresse e-mail ni un domaine.` : null;
};

export const futureOrToday =
  (today: string): Check =>
  (value) =>
    !value || value >= today ? null : "Une date à venir : la suite attendue ne peut pas être passée.";


// Erreurs d'un formulaire : `check` en quittant un champ, `clearIfFixed` en tapant, `validate`
// à l'envoi (renvoie faux et met le curseur dans le premier champ en erreur, d'id `prefix-champ`).
export function useChecks<K extends string>(checks: Record<K, Check>, read: (field: K) => string, prefix: string) {
  const errors = ref<Partial<Record<K, string>>>({});
  const fields = Object.keys(checks) as K[];

  function check(field: K): void {
    const message = checks[field](read(field));
    const next = { ...errors.value } as Partial<Record<K, string>>;
    if (message) next[field] = message;
    else delete next[field];
    errors.value = next;
  }

  function clearIfFixed(field: K): void {
    if (errors.value[field]) check(field);
  }

  function validate(): boolean {
    fields.forEach(check);
    const first = fields.find((f) => errors.value[f]);
    if (first) document.getElementById(`${prefix}-${first}`)?.focus();
    return !first;
  }

  return { errors, check, clearIfFixed, validate };
}
