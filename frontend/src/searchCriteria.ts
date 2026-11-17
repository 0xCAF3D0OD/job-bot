import { api, type AlertsPage } from "./api/client";
import { placeLabel } from "./cantons";

// « Ta recherche » (Kevin, 17.11) : une seule source, les critères du Profil. Les postes (gardés par les premiers pas,
// 3 au plus), les lieux et le taux. Enregistrer met à jour les critères, puis recalcule les recherches des alertes :
// chaque poste × lieu qui manque est créé, chaque recherche dont le poste ou le lieu a été retiré est supprimée (les
// mêmes appels que l'assistant). Aucun lieu = « Toute la Suisse » = une recherche par poste, sans lieu.
export const MAX_SEARCHES = 8;
export const MAX_ROLES = 3;
export const LIMIT_MESSAGE = "8 recherches au maximum. Retire un poste ou un lieu.";
// Les 7 valeurs gardées, en choix unique (Kevin, 17.11, point 13).
export const RATES = [null, 50, 60, 70, 80, 90, 100] as const;
export const rateLabel = (value: number | null): string => (value === null ? "Tous" : value === 100 ? "100 %" : `Dès ${value} %`);

export interface SearchCriteria {
  roles: string[];
  places: string[];
  rate: number | null;
}

const key = (text: string) => text.trim().toLowerCase();
function distinct(values: string[]): string[] {
  const seen = new Map<string, string>();
  for (const value of values) if (value.trim() && !seen.has(key(value))) seen.set(key(value), value.trim());
  return [...seen.values()];
}

/** Un lieu de recherche : un canton écrit en entier (« VD » → « Vaud », Kevin 17.11, point 9). */
export const searchPlace = (place: string): string => placeLabel(place.trim());

/** Les recherches voulues : chaque poste avec chaque lieu, ou chaque poste seul sans lieu. */
export function combinations(criteria: Pick<SearchCriteria, "roles" | "places">): { terms: string; location: string | null }[] {
  const places = distinct(criteria.places.map(searchPlace));
  const roles = distinct(criteria.roles);
  return roles.flatMap((terms): { terms: string; location: string | null }[] =>
    places.length ? places.map((location) => ({ terms, location })) : [{ terms, location: null }],
  );
}

/** Les critères affichés : les postes et les lieux des critères, plus ceux des recherches actives qui n'y sont pas encore
 *  (un compte d'avant la règle) ; ainsi, enregistrer sans rien changer ne supprime aucune recherche. */
export async function loadSearchCriteria(page: AlertsPage | null): Promise<SearchCriteria | null> {
  const [criteria, welcome] = await Promise.all([api.GET("/api/criteria"), api.GET("/api/welcome")]);
  if (!criteria.data) return null;
  const active = page?.searches.filter((s) => s.active) ?? [];
  const roles = distinct([...(welcome.data?.roles ?? []), ...active.map((s) => s.terms)]);
  const places = distinct([...(criteria.data.criteria.locations ?? []), ...active.flatMap((s) => (s.location ? [s.location] : []))]);
  // Une même ville écrite « VD » dans les critères et « Vaud » dans une recherche : une seule fois.
  const seen = new Set<string>();
  return {
    roles,
    places: places.filter((p) => !seen.has(key(searchPlace(p))) && !!seen.add(key(searchPlace(p)))),
    rate: criteria.data.criteria.min_rate ?? null,
  };
}

export interface SavedSearches {
  page: AlertsPage | null;
  // Les sites où une recherche supprimée était déjà créée : le site continuera d'écrire.
  stillWriting: { site: string; name: string; url: string | null }[];
}

/** Enregistre les critères, puis recalcule les recherches. `null` si l'enregistrement a échoué. */
export async function saveSearchCriteria(next: SearchCriteria, page: AlertsPage): Promise<SavedSearches | null> {
  const current = await api.GET("/api/criteria");
  if (!current.data) return null;
  const roles = distinct(next.roles).slice(0, MAX_ROLES);
  const [criteria, welcome] = await Promise.all([
    api.PUT("/api/criteria", { body: { ...current.data.criteria, locations: distinct(next.places), min_rate: next.rate } }),
    api.PUT("/api/welcome", { body: { roles } }),
  ]);
  if (!criteria.data || !welcome.data) return null;

  const wanted = combinations({ roles, places: next.places });
  const id = (terms: string, location: string | null) => `${key(terms)}|${key(location ? searchPlace(location) : "")}`;
  const wantedIds = new Set(wanted.map((w) => id(w.terms, w.location)));
  const active = page.searches.filter((s) => s.active);
  const gone = active.filter((s) => !wantedIds.has(id(s.terms, s.location)));
  const kept = new Set(active.filter((s) => !gone.includes(s)).map((s) => id(s.terms, s.location)));

  let latest: AlertsPage | null = page;
  for (const search of gone) {
    const { data } = await api.DELETE("/api/alert-searches/{search_id}", { params: { path: { search_id: search.id } } });
    if (data) latest = data;
  }
  for (const search of wanted.filter((w) => !kept.has(id(w.terms, w.location)))) {
    const { data } = await api.POST("/api/alert-searches", { body: search });
    if (data) latest = data;
  }
  const names = new Map(page.sites.map((s) => [s.slug, s.name]));
  const stillWriting = new Map<string, SavedSearches["stillWriting"][number]>();
  for (const cell of gone.flatMap((s) => s.cells)) {
    if (cell.status !== "todo" && !stillWriting.has(cell.site))
      stillWriting.set(cell.site, { site: cell.site, name: names.get(cell.site) ?? cell.site, url: cell.url ?? null });
  }
  return { page: latest, stillWriting: [...stillWriting.values()] };
}
