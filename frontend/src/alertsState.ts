import type { AlertsPage } from "./api/client";
import { sinceDays } from "./dates";
import { onDay } from "./format";

// L'état des alertes, recherche par recherche et site par site (planche « 6. Alertes ») : ce que dit
// chaque ligne, la pastille de la recherche et la bande d'action. Fonctions pures, testées à part.

// Les deux délais, à ajuster après le test utilisateurs (demande de Kevin).
// Jamais rien reçu, NOTHING_YET_DAYS jours après la création : le réglage est sans doute à revoir
// (orange sur la ligne, et la bande).
export const NOTHING_YET_DAYS = 3;
// Déjà reçu, puis plus rien depuis QUIET_DAYS jours : un marché calme, une simple mention grise
// (§4 : l'orange est réservé à l'action).
export const QUIET_DAYS = 14;

const DAY_MS = 86_400_000;

type Search = AlertsPage["searches"][number];
type Cell = Search["cells"][number];

export type SiteState =
  | { kind: "received"; label: string }
  | { kind: "quiet"; label: string; days: number }
  | { kind: "waiting"; label: string }
  | { kind: "silent"; label: string; days: number }
  | { kind: "todo"; label: string };

const daysSince = (iso: string, now: Date) => Math.floor((now.getTime() - Date.parse(iso)) / DAY_MS);

/** L'état d'un site pour une recherche, à partir de sa cellule (reçue, créée ou à créer). */
export function siteState(cell: Pick<Cell, "status" | "received_at" | "created_at">, now: Date): SiteState {
  if (cell.status === "received" && cell.received_at) {
    const days = daysSince(cell.received_at, now);
    if (days >= QUIET_DAYS) return { kind: "quiet", label: `rien ${sinceDays(cell.received_at, now)}`, days };
    return { kind: "received", label: `Reçue ${onDay(cell.received_at, now)}` };
  }
  if (cell.created_at) {
    const days = daysSince(cell.created_at, now);
    if (days >= NOTHING_YET_DAYS) return { kind: "silent", label: "Rien reçu depuis la création", days };
    return { kind: "waiting", label: "En attente du premier envoi" };
  }
  return { kind: "todo", label: "À créer" };
}

// Les lieux écrits comme on les lit : majuscule et accents (« geneve » → « Genève », « VD » → « Vaud »).
const PLACES: Record<string, string> = {
  ag: "Argovie", ai: "Appenzell", ar: "Appenzell", be: "Berne", bl: "Bâle-Campagne", bs: "Bâle", fr: "Fribourg",
  ge: "Genève", gl: "Glaris", gr: "Grisons", ju: "Jura", lu: "Lucerne", ne: "Neuchâtel", nw: "Nidwald",
  ow: "Obwald", sg: "Saint-Gall", sh: "Schaffhouse", so: "Soleure", sz: "Schwytz", tg: "Thurgovie",
  ti: "Tessin", ur: "Uri", vd: "Vaud", vs: "Valais", zg: "Zoug", zh: "Zurich",
  argovie: "Argovie", berne: "Berne", bern: "Berne", bale: "Bâle", basel: "Bâle", fribourg: "Fribourg",
  geneve: "Genève", geneva: "Genève", glaris: "Glaris", grisons: "Grisons", jura: "Jura", lucerne: "Lucerne",
  luzern: "Lucerne", neuchatel: "Neuchâtel", "saint-gall": "Saint-Gall", soleure: "Soleure", tessin: "Tessin",
  ticino: "Tessin", thurgovie: "Thurgovie", vaud: "Vaud", valais: "Valais", wallis: "Valais", zoug: "Zoug",
  zug: "Zoug", zurich: "Zurich", "zürich": "Zurich", lausanne: "Lausanne", sion: "Sion", sierre: "Sierre",
  martigny: "Martigny", monthey: "Monthey", montreux: "Montreux", vevey: "Vevey", nyon: "Nyon", morges: "Morges",
  renens: "Renens", yverdon: "Yverdon-les-Bains", "yverdon-les-bains": "Yverdon-les-Bains", bienne: "Bienne",
  biel: "Bienne", delemont: "Delémont", "la chaux-de-fonds": "La Chaux-de-Fonds", "suisse romande": "Suisse romande",
  suisse: "Suisse", switzerland: "Suisse", "teletravail": "Télétravail",
};
function bare(text: string): string {
  return text.trim().toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
}
export function placeLabel(raw: string): string {
  const key = raw.trim().toLowerCase();
  const known = PLACES[key] ?? PLACES[bare(raw)];
  if (known) return known;
  // Inconnu : la majuscule à chaque mot, le reste tel quel (« la sarraz » → « La Sarraz »).
  return raw
    .trim()
    .split(/(\s+|-)/)
    .map((part) => (/^[\s-]+$/.test(part) ? part : part.charAt(0).toUpperCase() + part.slice(1)))
    .join("");
}

export interface SearchGroup {
  terms: string;
  ids: number[];
  active: boolean;
  locations: string[];
  sites: { slug: string; name: string; url: string | null; state: SiteState }[];
  // La pastille de la recherche.
  pill: { kind: "received" | "waiting" | "todo" | "paused"; label: string };
}

/** Une carte par recherche (les mots), ses lieux réunis ; pour chaque site, la meilleure cellule des
 *  lieux : reçue d'abord (la plus récente), sinon créée (la plus ancienne), sinon à créer. */
export function searchGroups(page: AlertsPage, now: Date): SearchGroup[] {
  const byTerms = new Map<string, Search[]>();
  for (const search of page.searches) {
    const key = search.terms.trim().toLowerCase();
    byTerms.set(key, [...(byTerms.get(key) ?? []), search]);
  }
  return [...byTerms.values()].map((searches) => {
    const active = searches.some((s) => s.active);
    const live = searches.filter((s) => s.active || !active);
    const locations = [...new Set(live.map((s) => s.location).filter((l): l is string => !!l).map(placeLabel))];
    const sites = page.sites.map((site) => {
      const cells = live.map((s) => s.cells.find((c) => c.site === site.slug)).filter((c): c is Cell => !!c);
      const received = cells.filter((c) => c.status === "received" && c.received_at).sort((a, b) => Date.parse(b.received_at!) - Date.parse(a.received_at!))[0];
      const created = cells.filter((c) => c.created_at).sort((a, b) => Date.parse(a.created_at!) - Date.parse(b.created_at!))[0];
      const cell = received ?? created ?? cells[0] ?? { status: "todo", received_at: null, created_at: null, url: null };
      return { slug: site.slug, name: site.name, url: cells.find((c) => c.url)?.url ?? null, state: siteState(cell, now) };
    });
    const fresh = sites.filter((s) => s.state.kind === "received");
    const pill: SearchGroup["pill"] = !active
      ? { kind: "paused", label: "En pause" }
      : fresh.length
        ? { kind: "received", label: `Reçue · ${fresh.map((s) => s.name).join(", ")}` }
        : sites.some((s) => s.state.kind !== "todo")
          ? { kind: "waiting", label: "En attente" }
          : { kind: "todo", label: "À créer" };
    return { terms: searches[0]!.terms, ids: searches.map((s) => s.id), active, locations, sites, pill };
  });
}

export type Band =
  | { kind: "code"; site: string; title: string; summary: string; action: string }
  | { kind: "confirm"; site: string; url: string; searchId: number; title: string; summary: string; action: string }
  | { kind: "silent"; site: string; terms: string; title: string; summary: string; action: string };

/** La bande d'action (§3), une seule à la fois : un code attendu, une confirmation demandée, puis une
 *  alerte qui n'a jamais rien reçu NOTHING_YET_DAYS jours après sa création. Sinon, rien. */
export function alertsBand(page: AlertsPage, now: Date): Band | null {
  const name = (slug: string) => page.sites.find((s) => s.slug === slug)?.name ?? slug;
  const code = page.codes?.[0];
  if (code) {
    return {
      kind: "code",
      site: code.site,
      title: `${name(code.site)} attend un code de vérification.`,
      summary: "Le code arrive par e-mail sur ton adresse d'alertes.",
      action: "Vérifier",
    };
  }
  const confirm = page.to_confirm?.[0];
  if (confirm) {
    return {
      kind: "confirm",
      site: confirm.site,
      url: confirm.url,
      searchId: confirm.search_id,
      title: `${name(confirm.site)} attend ta confirmation.`,
      summary: "Le site demande de confirmer l'alerte avant de l'envoyer : ouvre son lien.",
      action: "Confirmer",
    };
  }
  for (const group of searchGroups(page, now)) {
    if (!group.active) continue;
    const silent = group.sites.find((s) => s.state.kind === "silent");
    if (silent && silent.state.kind === "silent") {
      return {
        kind: "silent",
        site: silent.slug,
        terms: group.terms,
        title: `${silent.name} n'a encore rien reçu.`,
        summary: `Ta recherche « ${group.terms} » y existe depuis ${silent.state.days} jours, sans un seul e-mail : le réglage est sans doute à revoir.`,
        action: "Vérifier l'alerte",
      };
    }
  }
  return null;
}
