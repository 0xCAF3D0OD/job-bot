import { computed } from "vue";
import { useRoute, useRouter, type LocationQuery } from "vue-router";

import type { Source } from "../api/client";

export type View = "to_review" | "filtered_out" | "all";
export type Sort = "recent" | "popular" | "score";

export interface OfferFilters {
  view: View;
  sort: Sort;
  q: string;
  sources: Source[];
  cantons: string[];
  minRate: number | null;
  minScore: number | null;
  externalOnly: boolean;
}

export const DEFAULT_FILTERS: OfferFilters = {
  view: "to_review",
  sort: "recent",
  q: "",
  sources: [],
  cantons: [],
  minRate: null,
  minScore: null,
  externalOnly: false,
};

const VIEWS: View[] = ["to_review", "filtered_out", "all"];
const SORTS: Sort[] = ["recent", "popular", "score"];
const SOURCES: Source[] = ["jobup", "indeed", "jobroom"];

function list(value: LocationQuery[string] | undefined): string[] {
  const values = Array.isArray(value) ? value : value ? [value] : [];
  return values.filter((v): v is string => typeof v === "string" && v !== "");
}

function one(value: LocationQuery[string] | undefined): string | undefined {
  return list(value)[0];
}

/** Lit les filtres depuis l'adresse de la page (partageable, conservée au rechargement). */
export function fromQuery(query: LocationQuery): OfferFilters {
  const view = one(query.statut) as View | undefined;
  const sort = one(query.tri) as Sort | undefined;
  const rate = Number(one(query.taux));
  const score = Number(one(query.note));
  return {
    view: view && VIEWS.includes(view) ? view : DEFAULT_FILTERS.view,
    sort: sort && SORTS.includes(sort) ? sort : DEFAULT_FILTERS.sort,
    q: one(query.q) ?? "",
    sources: list(query.site).filter((s): s is Source => SOURCES.includes(s as Source)),
    cantons: list(query.canton).map((c) => c.toUpperCase()),
    minRate: Number.isInteger(rate) && rate >= 1 && rate <= 100 ? rate : null,
    minScore: Number.isInteger(score) && score >= 1 && score <= 100 ? score : null,
    externalOnly: one(query.externe) === "1",
  };
}

export function toQuery(filters: OfferFilters): LocationQuery {
  const query: LocationQuery = {};
  if (filters.view !== DEFAULT_FILTERS.view) query.statut = filters.view;
  if (filters.sort !== DEFAULT_FILTERS.sort) query.tri = filters.sort;
  if (filters.q.trim()) query.q = filters.q.trim();
  if (filters.sources.length) query.site = [...filters.sources];
  if (filters.cantons.length) query.canton = [...filters.cantons];
  if (filters.minRate !== null) query.taux = String(filters.minRate);
  if (filters.minScore !== null) query.note = String(filters.minScore);
  if (filters.externalOnly) query.externe = "1";
  return query;
}

/** Nombre de filtres d'affichage actifs (hors statut et tri), pour le bouton mobile. */
export function activeCount(filters: OfferFilters): number {
  return (
    (filters.q.trim() ? 1 : 0) +
    filters.sources.length +
    filters.cantons.length +
    (filters.minRate !== null ? 1 : 0) +
    (filters.minScore !== null ? 1 : 0) +
    (filters.externalOnly ? 1 : 0)
  );
}

export function useOfferFilters() {
  const route = useRoute();
  const router = useRouter();
  const filters = computed(() => fromQuery(route.query));
  // Dernier état demandé : deux clics rapides se cumulent même si l'adresse n'est pas encore
  // à jour (router.replace est asynchrone).
  let pending: OfferFilters | null = null;

  function navigate(next: OfferFilters): void {
    pending = next;
    void router.replace({ query: toQuery(next) }).finally(() => {
      if (pending === next) pending = null;
    });
  }

  function update(patch: Partial<OfferFilters>): void {
    navigate({ ...(pending ?? filters.value), ...patch });
  }

  function reset(): void {
    const current = pending ?? filters.value;
    navigate({ ...DEFAULT_FILTERS, view: current.view, sort: current.sort });
  }

  return { filters, update, reset };
}
