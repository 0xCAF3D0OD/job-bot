import { dayLabel } from "./dates";

// Les réponses pour les formulaires de candidature (récapitulatif du 11 novembre, PR 44 ; maquettes
// CoordonneesOrdinateur et CoordonneesTel) : ce que la ligne affiche, ce que le panneau propose et ce qui est
// enregistré. Les anciennes saisies libres ne sont jamais effacées : elles s'affichent telles quelles, ou, pour un
// salaire qu'on ne sait pas lire, la ligne dit « À compléter » et le panneau rappelle ce qui était écrit.
export type AnswerKey = "linkedin" | "permit" | "availability" | "notice" | "salary" | "website";
export type SalaryMode = "auto" | "demander";

/** Les cinq réponses comptées ; « Site ou portfolio » est facultatif et ne compte pas. */
export const COUNTED: AnswerKey[] = ["linkedin", "permit", "availability", "notice", "salary"];

export const PERMITS = ["Nationalité suisse", "Permis C", "Permis B", "Permis G"];
export const AVAILABILITIES = ["Tout de suite", "Dans 1 mois", "Dans 3 mois"];
export const NOTICES = ["Aucun", "1 mois", "2 mois", "3 mois"];
const ISO_DAY = /^\d{4}-\d{2}-\d{2}$/;
export const isDay = (value: string): boolean => ISO_DAY.test(value.trim());

/** « 95 000 » : les milliers séparés par une espace fine insécable. */
export function groupThousands(digits: string): string {
  return digits.replace(/\B(?=(\d{3})+(?!\d))/g, " ");
}

/** Le salaire annuel en chiffres, ou `null` quand la saisie ne se lit pas sans doute (« 90 à 100k », « à discuter »). */
export function parseSalary(value: string): string | null {
  const text = value
    .toLowerCase()
    .replace(/chf|fr\.?|francs?|brut|par an|\/ ?an|annuel(s|le)?|\.–|\.-/g, "")
    .replace(/[\s'’  ]/g, "");
  return /^\d{4,7}$/.test(text) ? String(Number(text)) : null;
}

/** « linkedin.com/in/kevin » : l'adresse sans le protocole ni « www. », comme sur le CV. */
export function shortAddress(value: string): string {
  return value.trim().replace(/^https?:\/\//i, "").replace(/^www\./i, "").replace(/\/$/, "");
}

export const linkedinProfile = (value: string): boolean => /^(https?:\/\/)?([a-z]{2,3}\.)?linkedin\.com\/in\/[^\s/]+\/?$/i.test(value.trim());

/** Ce que la ligne affiche ; vide : la ligne dit « À compléter » (ou « Facultatif »). */
export function answerText(key: AnswerKey, value: string): string {
  const text = value.trim();
  if (!text) return "";
  if (key === "linkedin" || key === "website") return shortAddress(text);
  if (key === "availability" && isDay(text)) return dayLabel(text);
  if (key === "salary") {
    const amount = parseSalary(text);
    return amount ? `${groupThousands(amount)} CHF brut par an` : "";
  }
  return text;
}
