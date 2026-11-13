import type { Application } from "./api/client";
import { followUpList } from "./applicationState";

// Le filtre des Envoyées (paquet du 11 novembre, PR 39 ; maquette CandidaturesOrdinateurB, état « envoyees-filtre ») :
// un statut à la fois, gardé dans l'adresse (?statut=relancer), et un tri (?tri=recentes).

export type SentFilter = "toutes" | "relancer" | "sans-reponse" | "entretien" | "refusees";
export type SentSort = "relancer" | "recentes" | "anciennes";

export const SENT_FILTERS: { value: SentFilter; label: string }[] = [
  { value: "toutes", label: "Toutes" },
  { value: "relancer", label: "À relancer" },
  { value: "sans-reponse", label: "Sans réponse" },
  { value: "entretien", label: "Entretien" },
  { value: "refusees", label: "Refusées" },
];
export const SENT_SORTS: { value: SentSort; label: string }[] = [
  { value: "relancer", label: "Trier : à relancer d’abord" },
  { value: "recentes", label: "Trier : plus récentes" },
  { value: "anciennes", label: "Trier : plus anciennes" },
];

export function sentFilterOf(value: unknown): SentFilter {
  return SENT_FILTERS.find((f) => f.value === value && f.value !== "toutes")?.value ?? "toutes";
}
export function sentSortOf(value: unknown): SentSort {
  return SENT_SORTS.find((s) => s.value === value)?.value ?? "relancer";
}

// « À relancer » suit la rubrique du même nom (plus de 10 jours sans réponse) ; les autres suivent le statut.
export function sentFiltered(all: Application[], filter: SentFilter): Application[] {
  if (filter === "relancer") return followUpList(all);
  if (filter === "sans-reponse") return all.filter((a) => a.status === "sans_reponse");
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
