import { computed, shallowRef, watch } from "vue";
import { useRoute, useRouter, type LocationQuery } from "vue-router";

import type { OfferFacets, Source } from "../api/client";
import { sourceLabel } from "../format";
import { t } from "../i18n";

export type View = "pending" | "to_review" | "filtered_out" | "later" | "in_progress" | "expired" | "all";
export type Sort = "day" | "recent" | "popular" | "score" | "activity";

// Télétravail (docs/26 §4) : possible, même partiel, ou complet.
export type Remote = "partial" | "full";

// Filtre « Type de note » (PR 26 ; section 31 du 16.11) : notée sur l'annonce complète (définitive) ou sur l'extrait
// de l'alerte seulement (provisoire). La valeur reste "sure" dans le code et l'adresse (?base=sure).
export type Basis = "sure" | "provisional";

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
  // Agences de placement masquées (section 35 du 16.11), ?agences=masquer.
  hideAgencies: boolean;
  // À traiter avec les offres écartées par les critères (« Masquer les offres écartées » coupé,
  // docs/139 C2), ?ecartees=montrer.
  showFilteredOut: boolean;
  // À traiter avec les offres expirées (« Afficher aussi › Expirées », docs/139 5e), ?expirees=montrer.
  showExpired: boolean;
  // Notes définitives ou provisoires seulement, ?base=sure ou ?base=provisoire ; null : toutes.
  basis: Basis | null;
}

export const DEFAULT_FILTERS: OfferFilters = {
  // À traiter (docs/139, C2) : à examiner, plus tard et en préparation.
  view: "pending",
  // Par date, la mieux notée d'abord dans chaque jour (retour d'usage du 2026-10-14).
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
  hideAgencies: false,
  showFilteredOut: false,
  showExpired: false,
  basis: null,
};

const VIEWS: View[] = ["pending", "to_review", "filtered_out", "later", "in_progress", "expired", "all"];
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
    hideAgencies: one(query.agences) === "masquer",
    showFilteredOut: one(query.ecartees) === "montrer",
    showExpired: one(query.expirees) === "montrer",
    basis: one(query.base) === "sure" ? "sure" : one(query.base) === "provisoire" ? "provisional" : null,
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
  if (filters.hideAgencies) query.agences = "masquer";
  if (filters.showFilteredOut) query.ecartees = "montrer";
  if (filters.showExpired) query.expirees = "montrer";
  if (filters.basis) query.base = filters.basis === "sure" ? "sure" : "provisoire";
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
    (filters.hideDoubtful ? 1 : 0) +
    (filters.hideAgencies ? 1 : 0) +
    (filters.showFilteredOut ? 1 : 0) +
    (filters.showExpired ? 1 : 0) +
    (filters.basis ? 1 : 0)
  );
}

// « Note minimale, sur 100 » (section 31 du 16.11) : les seuils des mots de la note (format.ts, scoreWord), 50 « À
// creuser », 75 « Proche », 85 « Très proche », écrits en chiffres. Communs au panneau, à la feuille et aux pastilles.
export const SCORE_CHOICES: { label: string; min: number | null }[] = [
  { label: "Toutes", min: null },
  { label: "50 et +", min: 50 },
  { label: "75 et +", min: 75 },
  { label: "85 et +", min: 85 },
];
export const SCORE_HELP = "À quel point l’offre correspond à ton profil.";
// « Taux d'activité » (section 31 du 16.11) : un seul choix, mêmes valeurs qu'avant.
export const RATE_CHOICES: { label: string; value: number | null }[] = [
  { label: "Tous", value: null },
  { label: "Dès 60 %", value: 60 },
  { label: "Dès 80 %", value: 80 },
  { label: "100 %", value: 100 },
];
export const REMOTE_LABEL = "Télétravail possible, même partiel";

// Le nombre d'offres sous chaque choix de Note et de Taux (§65 du 17.11) : le chiffre seul, calculé par le serveur
// avec tous les autres filtres actifs ; le choix actif donne le même nombre que « Afficher n offres ».
type ChoiceFacets = Pick<OfferFacets, "scores" | "unscored" | "rates">;
const MAX_SHOWN = 99_999;
export function choiceCount(count: number): string {
  return count > MAX_SHOWN ? t("100 k+") : new Intl.NumberFormat("fr-CH").format(count);
}
/** Note : les tranches de 5 points de la courbe des notes (sans le filtre de note), dès le seuil du choix. */
export function scoreCount(facets: ChoiceFacets, min: number | null): number {
  const scored = (facets.scores ?? []).slice(min === null ? 0 : min / 5).reduce((sum, n) => sum + n, 0);
  return min === null ? scored + (facets.unscored ?? 0) : scored;
}
/** Taux : la facette du serveur (« all », « 60 », « 80 », « 100 »), sans le filtre du taux. */
export function rateCount(facets: ChoiceFacets, value: number | null): number {
  return (facets.rates ?? []).find((f) => f.value === String(value ?? "all"))?.count ?? 0;
}

/** Les trois choix du groupe « Type de note », avec les nombres réels du serveur (hors « Toutes »). */
export function basisChoices(facets: { sure?: number; provisional?: number }): { label: string; value: Basis | null }[] {
  return [
    { label: "Toutes", value: null },
    { label: `Définitives · ${facets.sure ?? 0}`, value: "sure" },
    { label: `Provisoires · ${facets.provisional ?? 0}`, value: "provisional" },
  ];
}
export const BASIS_HELP = "Provisoire : notée sur l’extrait de l’alerte, sans l’annonce complète.";

/** Les flèches d'un groupe de boutons radio : le choix suit le focus (WAI-ARIA, radiogroup). */
export function radioKey(event: KeyboardEvent): void {
  const step = ["ArrowRight", "ArrowDown"].includes(event.key) ? 1 : ["ArrowLeft", "ArrowUp"].includes(event.key) ? -1 : 0;
  if (!step) return;
  const radios = Array.from((event.currentTarget as HTMLElement).querySelectorAll<HTMLElement>("[role=radio]"));
  const next = radios[(radios.indexOf(event.target as HTMLElement) + step + radios.length) % radios.length];
  if (!next) return;
  event.preventDefault();
  next.focus();
  next.click();
}

/** La note filtrée en mots ; une adresse d'avant (?note=60-90) garde ses bornes. */
export function scoreLabel(filters: Pick<OfferFilters, "minScore" | "maxScore">): string {
  const choice = filters.maxScore === null ? SCORE_CHOICES.find((c) => c.min === filters.minScore) : undefined;
  return choice ? choice.label : `${filters.minScore ?? 0}–${filters.maxScore ?? 100}`;
}

/** Le changement de statut : En préparation se trie par dernière action (docs/43), choix qui part avec elle.
 *  Partagé par le panneau de l'ordinateur et la feuille du téléphone. */
export function viewPatch(view: View, sort: Sort): Partial<OfferFilters> {
  if (view === "in_progress") return { view, sort: "activity" };
  return sort === "activity" ? { view, sort: DEFAULT_FILTERS.sort } : { view };
}

const STATUS_CHIP: Partial<Record<View, string>> = { to_review: "Nouvelles", later: "Gardées", in_progress: "En préparation" };

export interface FilterChip {
  key: string;
  label: string;
  patch: Partial<OfferFilters>;
}

/** Les filtres actifs en pastilles sous la barre d'outils (1.6.55), une par valeur, chacune avec son retrait.
 *  La recherche n'en a une que si son champ est caché (téléphone : il est dans la feuille). */
export function activeChips(filters: OfferFilters): FilterChip[] {
  const chips: FilterChip[] = [];
  // Le statut choisi, en premier (Kevin, 16.11) : gardé d'une visite à l'autre, il doit se voir et se retirer.
  const status = STATUS_CHIP[filters.view];
  if (status)
    chips.push({ key: "view", label: `Statut : ${status}`, patch: { view: DEFAULT_FILTERS.view, sort: filters.sort === "activity" ? DEFAULT_FILTERS.sort : filters.sort } });
  if (filters.minScore !== null || filters.maxScore !== null)
    chips.push({ key: "score", label: t("Note {seuil}", { seuil: scoreLabel(filters) }), patch: { minScore: null, maxScore: null } });
  if (filters.basis)
    chips.push({ key: "basis", label: filters.basis === "sure" ? "Notes définitives" : "Notes provisoires", patch: { basis: null } });
  if (filters.remote)
    chips.push({ key: "remote", label: filters.remote === "full" ? "Télétravail complet" : REMOTE_LABEL, patch: { remote: null } });
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
    chips.push({ key: "rate", label: filters.minRate === 100 ? t("Taux 100 %") : t("Taux dès {taux} %", { taux: filters.minRate }), patch: { minRate: null } });
  if (filters.externalOnly) chips.push({ key: "external", label: "Chez l’employeur", patch: { externalOnly: false } });
  if (filters.hideDoubtful)
    chips.push({ key: "doubtful", label: "Sans les offres à vérifier", patch: { hideDoubtful: false } });
  if (filters.hideAgencies)
    chips.push({ key: "agencies", label: "Sans les agences de placement", patch: { hideAgencies: false } });
  if (filters.showFilteredOut)
    chips.push({ key: "filtered-out", label: "Avec les offres écartées", patch: { showFilteredOut: false } });
  if (filters.showExpired)
    chips.push({ key: "expired", label: "Avec les offres expirées", patch: { showExpired: false } });
  return chips;
}

// Les filtres gardés jusqu'à la fermeture de l'onglet (Kevin, 16.11, docs/decisions/2026-11-16-1644-filtres-gardes.md) :
// revenir sur Offres par un lien sans filtre (« Retour aux offres », onglet Offres) les remet ; un lien qui en porte
// un (« Tout voir » de Top du jour) l'emporte. Effacés à la déconnexion (useAuth).
const KEPT_KEY = "jobA1.offres-filtres";
const FILTER_KEYS = ["statut", "tri", "q", "site", "canton", "taux", "note", "externe", "teletravail", "verifier", "agences", "ecartees", "expirees", "base"];
const hasFilters = (query: LocationQuery): boolean => FILTER_KEYS.some((key) => query[key] != null);

function keptFilters(): LocationQuery | null {
  try {
    const kept = toQuery(fromQuery(JSON.parse(sessionStorage.getItem(KEPT_KEY) ?? "{}") as LocationQuery));
    return hasFilters(kept) ? kept : null;
  } catch {
    return null;
  }
}

export function useOfferFilters() {
  const route = useRoute();
  const router = useRouter();
  // Arrivée sans filtre dans l'adresse : les filtres gardés, tout de suite (pas de liste « Toutes » le temps du replace).
  const restoring = shallowRef(hasFilters(route.query) ? null : keptFilters());
  if (restoring.value)
    void router.replace({ query: { ...route.query, ...restoring.value } }).finally(() => (restoring.value = null));
  const filters = computed(() => fromQuery(restoring.value ? { ...route.query, ...restoring.value } : route.query));
  watch(filters, (next) => {
    if (restoring.value || route.name !== "offers") return;
    try {
      sessionStorage.setItem(KEPT_KEY, JSON.stringify(toQuery(next)));
    } catch {
      // Stockage refusé : les filtres restent dans l'adresse seulement.
    }
  }, { immediate: true });
  // Dernier état demandé : deux clics rapides se cumulent même si l'adresse n'est pas encore
  // à jour (router.replace est asynchrone).
  let pending: OfferFilters | null = null;

  // `push` : un choix appliqué hors d’une feuille ou d’un panneau (pastilles, « Tout effacer » sous la barre) crée son
  // entrée d’historique ; dans une feuille, l’adresse de l’entrée ouverte est remplacée (filterHistory.ts, Kevin 17.11).
  function navigate(next: OfferFilters, push = false): void {
    pending = next;
    const query = toQuery(next);
    void (push ? router.push({ query }) : router.replace({ query })).finally(() => {
      if (pending === next) pending = null;
    });
  }

  function update(patch: Partial<OfferFilters>, push = false): void {
    navigate({ ...(pending ?? filters.value), ...patch }, push);
  }

  function reset(push = false): void {
    const current = pending ?? filters.value;
    // « Tout effacer » retire aussi le statut (Kevin, 16.11) ; le tri reste, sauf « Dernière action », propre à En préparation.
    navigate({ ...DEFAULT_FILTERS, sort: current.sort === "activity" ? DEFAULT_FILTERS.sort : current.sort }, push);
  }

  return { filters, update, reset };
}
