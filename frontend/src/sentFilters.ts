import type { Application } from "./api/client";
import { followUpList } from "./applicationState";

// Le filtre des Envoyées (paquet du 11 novembre, PR 39 ; maquette CandidaturesOrdinateurB, état « envoyees-filtre ») :
// un statut à la fois, gardé dans l'adresse (?statut=relancer), et un tri (?tri=recentes).
// Statuts (Kevin, 18.11.2026, 13 h 38 et 13 h 39) : Envoyée, Réponse reçue, Entretien, Refusée, plus « À relancer ».
// « Envoyée » regroupe les candidatures sans réponse de l'employeur (en attente, relancées, sans réponse). Pas de
// « Vue » : l'app ne sait pas si l'employeur a ouvert la candidature.

export type SentFilter = "toutes" | "relancer" | "envoyee" | "reponse" | "entretien" | "refusees";
export type SentSort = "relancer" | "recentes" | "anciennes";

export const SENT_FILTERS: { value: SentFilter; label: string }[] = [
  { value: "toutes", label: "Toutes" },
  { value: "relancer", label: "À relancer" },
  { value: "envoyee", label: "Envoyée" },
  { value: "reponse", label: "Réponse reçue" },
  { value: "entretien", label: "Entretien" },
  { value: "refusees", label: "Refusée" },
];
export const SENT_SORTS: { value: SentSort; label: string }[] = [
  { value: "relancer", label: "Trier : à relancer d’abord" },
  { value: "recentes", label: "Trier : plus récentes" },
  { value: "anciennes", label: "Trier : plus anciennes" },
];

// Une ancienne adresse ?statut=sans-reponse (avant le 18.11) ouvre « Envoyée ».
export function sentFilterOf(value: unknown): SentFilter {
  if (value === "sans-reponse") return "envoyee";
  return SENT_FILTERS.find((f) => f.value === value && f.value !== "toutes")?.value ?? "toutes";
}
export function sentSortOf(value: unknown): SentSort {
  return SENT_SORTS.find((s) => s.value === value)?.value ?? "relancer";
}

// « À relancer » suit la rubrique du même nom (plus de 10 jours sans réponse) ; les autres suivent le statut.
export function sentFiltered(all: Application[], filter: SentFilter): Application[] {
  if (filter === "relancer") return followUpList(all);
  if (filter === "envoyee") return all.filter((a) => ["en_attente", "relancee", "sans_reponse"].includes(a.status));
  if (filter === "reponse") return all.filter((a) => a.status === "reponse");
  if (filter === "entretien") return all.filter((a) => a.status === "entretien");
  if (filter === "refusees") return all.filter((a) => a.status === "refus");
  return all;
}

export function sentCounts(all: Application[]): Record<SentFilter, number> {
  return Object.fromEntries(SENT_FILTERS.map((f) => [f.value, sentFiltered(all, f.value).length])) as Record<SentFilter, number>;
}

export function sentSorted(items: Application[], sort: Exclude<SentSort, "relancer">): Application[] {
  const way = sort === "recentes" ? -1 : 1;
  return [...items].sort((a, b) => way * (a.sent_at.localeCompare(b.sent_at) || a.id - b.id));
}
