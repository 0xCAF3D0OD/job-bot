import type { ParseStatus, Source } from "./api/client";

export const sourceLabel: Record<Source, string> = {
  jobup: "jobup",
  indeed: "Indeed",
  jobroom: "Job-Room",
  unknown: "inconnu",
};

export const parseStatusLabel: Record<ParseStatus, string> = {
  parsed: "analysé",
  empty: "sans offre",
  unrecognized: "non reconnu",
  failed: "erreur d'analyse",
};

const dateTime = new Intl.DateTimeFormat("fr-CH", {
  dateStyle: "short",
  timeStyle: "short",
  timeZone: "Europe/Zurich",
});

export function formatDateTime(iso: string): string {
  return dateTime.format(new Date(iso));
}

export function rateText(min: number | null, max: number | null): string {
  if (min === null || max === null) return "";
  return min === max ? `${min} %` : `${min}–${max} %`;
}

const shortDate = new Intl.DateTimeFormat("fr-CH", {
  day: "numeric",
  month: "short",
  year: "numeric",
  timeZone: "Europe/Zurich",
});

export function formatDate(iso: string): string {
  return shortDate.format(new Date(iso));
}

/** Couleur stable (0 à 3) pour la pastille d'une entreprise. */
export function colorIndex(name: string): number {
  let hash = 0;
  for (const char of name) hash = (hash * 31 + char.charCodeAt(0)) >>> 0;
  return hash % 4;
}

/** Niveau d'une note, pour sa couleur : bonne (≥ 70), moyenne (≥ 50) ou faible. */
export function scoreLevel(score: number): "high" | "mid" | "low" {
  if (score >= 70) return "high";
  if (score >= 50) return "mid";
  return "low";
}

export const methodLabel: Record<"electronique" | "ecrit" | "telephone" | "personnel", string> = {
  electronique: "Électronique",
  ecrit: "Écrit (courrier)",
  telephone: "Téléphone",
  personnel: "En personne",
};

export const applicationStatusLabel: Record<
  "en_attente" | "relancee" | "entretien" | "refus" | "engagement" | "sans_reponse",
  string
> = {
  en_attente: "En attente",
  relancee: "Relancée",
  entretien: "Entretien",
  refus: "Refus",
  engagement: "Engagement",
  sans_reponse: "Sans réponse",
};

const monthFormat = new Intl.DateTimeFormat("fr-CH", { month: "long", year: "numeric", timeZone: "UTC" });

/** « 2026-10 » → « octobre 2026 ». */
export function formatMonth(month: string): string {
  const [year, m] = month.split("-").map(Number);
  return monthFormat.format(new Date(Date.UTC(year ?? 2000, (m ?? 1) - 1, 1)));
}

export function shiftMonth(month: string, delta: number): string {
  const [year, m] = month.split("-").map(Number);
  const date = new Date(Date.UTC(year ?? 2000, (m ?? 1) - 1 + delta, 1));
  return `${date.getUTCFullYear()}-${String(date.getUTCMonth() + 1).padStart(2, "0")}`;
}
