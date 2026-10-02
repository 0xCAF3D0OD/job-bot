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
