import type { ParseStatus } from "./api/client";

export const SITE_NAMES: Record<string, string> = {
  jobup: "jobup",
  indeed: "Indeed",
  jobroom: "Job-Room",
  jobsch: "jobs.ch",
  linkedin: "LinkedIn",
  unknown: "inconnu",
};

// Nom affiché d'un site ; un site ajouté dans les Réglages garde son identifiant.
export const sourceLabel: Record<string, string> = new Proxy(SITE_NAMES, {
  get: (names, slug: string) => names[slug] ?? slug,
});

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

// Bandeau d'une offre retirée (docs/10 §1) : certaine (page introuvable) ou probable (Indeed).
export function expiredText(offer: { expired_at?: string | null; expiry_source?: string | null }): string {
  if (!offer.expired_at) return "";
  const day = new Date(offer.expired_at).toLocaleDateString("fr-CH");
  if (offer.expiry_source === "manual") return `Signalée expirée par toi le ${day}.`;
  return offer.expiry_source === "age"
    ? `Probablement expirée : plus vue dans aucune alerte depuis 30 jours (${day}).`
    : `Offre expirée le ${day} : l'annonce n'est plus en ligne.`;
}
