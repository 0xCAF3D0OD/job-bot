import { computed } from "vue";
import { useRoute, useRouter, type LocationQuery } from "vue-router";

import type { Source } from "../api/client";
import { sourceLabel } from "../format";

export type View = "to_review" | "filtered_out" | "later" | "in_progress" | "expired" | "all";
export type Sort = "day" | "recent" | "popular" | "score" | "activity";

// Télétravail (docs/26 §4) : au moins partiel, ou complet.
export type Remote = "partial" | "full";

export interface OfferFilters {
  view: View;
  sort: Sort;
  q: string;
  sources: Source[];
  cantons: string[];
  minRate: number | null;
  minScore: number | null;
  // Note maximale (docs/27 §3), avec ?note=60-90 ; null : jusqu'à 100.
  maxScore: number | null;
  externalOnly: boolean;
  remote: Remote | null;
  // Offres « à vérifier » masquées (docs/30 §3), ?verifier=masquer.
  hideDoubtful: boolean;
}

export const DEFAULT_FILTERS: OfferFilters = {
  view: "to_review",
  // Par jour, la mieux notée d'abord dans chaque jour (retour d'usage du 2026-10-14).
  sort: "day",
  q: "",
  sources: [],
  cantons: [],
  minRate: null,
  minScore: null,
  maxScore: null,
  externalOnly: false,
  remote: null,
  hideDoubtful: false,
};

const VIEWS: View[] = ["to_review", "filtered_out", "later", "in_progress", "expired", "all"];
const SORTS: Sort[] = ["day", "recent", "popular", "score", "activity"];

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
  const [scoreLow, scoreHigh] = (one(query.note) ?? "").split("-");
  const score = Number(scoreLow);
  const scoreMax = scoreHigh === undefined || scoreHigh === "" ? NaN : Number(scoreHigh);
  return {
    view: view && VIEWS.includes(view) ? view : DEFAULT_FILTERS.view,
    sort: sort && SORTS.includes(sort) ? sort : DEFAULT_FILTERS.sort,
    q: one(query.q) ?? "",
    sources: list(query.site).filter((s): s is Source => /^[a-z0-9]{2,30}$/.test(s)),
    cantons: list(query.canton).map((c) => c.toUpperCase()),
    minRate: Number.isInteger(rate) && rate >= 1 && rate <= 100 ? rate : null,
    minScore: Number.isInteger(score) && score >= 1 && score <= 100 ? score : null,
    maxScore: Number.isInteger(scoreMax) && scoreMax >= 0 && scoreMax <= 99 ? scoreMax : null,
    externalOnly: one(query.externe) === "1",
    remote: one(query.teletravail) === "complet" ? "full" : one(query.teletravail) === "partiel" ? "partial" : null,
    hideDoubtful: one(query.verifier) === "masquer",
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
  if (filters.minScore !== null || filters.maxScore !== null) {
    query.note = `${filters.minScore ?? 0}${filters.maxScore !== null ? `-${filters.maxScore}` : ""}`;
  }
  if (filters.externalOnly) query.externe = "1";
  if (filters.remote) query.teletravail = filters.remote === "full" ? "complet" : "partiel";
  if (filters.hideDoubtful) query.verifier = "masquer";
  return query;
}

/** Nombre de filtres d'affichage actifs (hors statut et tri), pour le bouton mobile. */
export function activeCount(filters: OfferFilters): number {
  return (
    (filters.q.trim() ? 1 : 0) +
    filters.sources.length +
    filters.cantons.length +
    (filters.minRate !== null ? 1 : 0) +
    (filters.minScore !== null || filters.maxScore !== null ? 1 : 0) +
    (filters.externalOnly ? 1 : 0) +
    (filters.remote ? 1 : 0) +
    (filters.hideDoubtful ? 1 : 0)
  );
}

// Les choix de la note en mots (format.ts, scoreWord) : 70 « Proche », 85 « Très proche ».
export const SCORE_CHOICES = [
  { label: "Toutes", min: null },
  { label: "Proche et plus", min: 70 },
  { label: "Très proche", min: 85 },
] as const;

/** La note filtrée en mots ; une adresse d'avant (?note=60-90) garde ses bornes. */
export function scoreLabel(filters: Pick<OfferFilters, "minScore" | "maxScore">): string {
  const choice = filters.maxScore === null ? SCORE_CHOICES.find((c) => c.min === filters.minScore) : undefined;
  return choice ? choice.label : `${filters.minScore ?? 0}–${filters.maxScore ?? 100}`;
}

export interface FilterChip {
  key: string;
  label: string;
  patch: Partial<OfferFilters>;
}

/** Les filtres actifs en pastilles sous la barre d'outils (1.6.55), une par valeur, chacune avec son retrait.
 *  La recherche n'en a une que si son champ est caché (téléphone : il est dans la feuille). */
export function activeChips(filters: OfferFilters, withSearch: boolean): FilterChip[] {
  const chips: FilterChip[] = [];
  const q = filters.q.trim();
  if (withSearch && q) chips.push({ key: "q", label: `Recherche : ${q}`, patch: { q: "" } });
  if (filters.minScore !== null || filters.maxScore !== null)
    chips.push({ key: "score", label: `Note minimale : ${scoreLabel(filters)}`, patch: { minScore: null, maxScore: null } });
  if (filters.remote)
    chips.push({
      key: "remote",
      label: `Télétravail : ${filters.remote === "full" ? "complet" : "au moins partiel"}`,
      patch: { remote: null },
    });
  for (const source of filters.sources)
    chips.push({
      key: `source-${source}`,
      label: `Site : ${sourceLabel[source] ?? source}`,
      patch: { sources: filters.sources.filter((s) => s !== source) },
    });
  for (const canton of filters.cantons)
    chips.push({
      key: `canton-${canton}`,
      label: `Canton : ${canton}`,
      patch: { cantons: filters.cantons.filter((c) => c !== canton) },
    });
  if (filters.minRate !== null)
    chips.push({ key: "rate", label: `Taux : ${filters.minRate} % et plus`, patch: { minRate: null } });
  if (filters.externalOnly) chips.push({ key: "external", label: "Chez l'employeur", patch: { externalOnly: false } });
  if (filters.hideDoubtful)
    chips.push({ key: "doubtful", label: "Sans les offres à vérifier", patch: { hideDoubtful: false } });
  return chips;
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
