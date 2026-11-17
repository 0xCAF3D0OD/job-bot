import { reactive } from "vue";

import { KEY, applyLang, formatLocale, isActive, lang } from "./lang";
import type { Lang } from "./languages";
import pages from "./locales/pages.json";

// Les traductions (docs/147). Une fonction maison plutôt que vue-i18n (environ 15 Ko gzip sur chaque page) : le
// français reste le texte du code, `t("Écarter l’offre")`, et s'affiche tel quel ; une autre langue charge, page par
// page, un catalogue `locales/<langue>/<page>.json` (texte français → traduction). Ce qui manque reste en français,
// jamais un vide. La langue choisie, `<html lang>` et les formats sont dans lang.ts, chargé sur toutes les pages.

// Une entrée de catalogue : une phrase, ou ses formes de pluriel (Intl.PluralRules de la langue).
export type Plural = Partial<Record<Intl.LDMLPluralRule, string>> & { other: string };
type Catalog = Record<string, string | Plural>;
const loaded = reactive<Record<string, Catalog>>({});

// Les catalogues, un fichier par page et par langue, chargés à la demande : un bloc chacun dans le build, que
// `poids.mjs` mesure (limite par catalogue, docs/decisions/2026-11-17-1330-poids-catalogues-langues.md).
const FILES = import.meta.glob<Catalog>("./locales/*/*.json", { import: "default" });

// Charge le catalogue d'une page dans la langue en cours (rien en français, rien s'il n'existe pas encore).
export async function loadCatalog(page: string): Promise<void> {
  const code = lang.value;
  const id = `${code}/${page}`;
  const file = FILES[`./locales/${id}.json`];
  if (code === "fr" || !file || loaded[id]) return;
  loaded[id] = await file();
}

// Les catalogues d'une route (pages.json) : le sien et `commun`, chargés avant d'afficher la page.
export async function loadRoute(name: string): Promise<void> {
  const names = Object.entries(pages as Record<string, { routes: string[] }>)
    .filter(([, page]) => page.routes.includes("*") || page.routes.includes(name))
    .map(([page]) => page);
  await Promise.all(names.map(loadCatalog));
}

// Pour les tests : un catalogue posé à la main.
export function addCatalog(code: Lang, page: string, catalog: Catalog): void {
  loaded[`${code}/${page}`] = catalog;
}

function lookup(source: string): string | Plural | undefined {
  if (lang.value === "fr") return undefined;
  const prefix = `${lang.value}/`;
  for (const id in loaded) {
    if (!id.startsWith(prefix)) continue;
    const found = loaded[id]![source];
    if (found !== undefined) return found;
  }
  return undefined;
}

type Params = Record<string, string | number>;
// `{nom}` remplacé par sa valeur ; un nombre est écrit par Intl dans la langue (« 1'000 » en allemand).
function fill(text: string, params?: Params): string {
  if (!params) return text;
  return text.replace(/\{(\w+)\}/g, (all, name: string) => {
    const value = params[name];
    if (value === undefined) return all;
    return typeof value === "number" ? new Intl.NumberFormat(formatLocale()).format(value) : value;
  });
}

// Une phrase de l'interface, écrite en français dans le code : `t("Bonjour {prenom}", { prenom })`.
export function t(source: string, params?: Params): string {
  const found = lookup(source);
  return fill(typeof found === "string" ? found : source, params);
}

// Une phrase qui dépend d'un nombre, par règles de pluriel (jamais par morceaux collés) :
// `tn(n, { one: "{n} offre", other: "{n} offres", zero: "Aucune offre" })`. La clé du catalogue est la forme `other`
// française ; `zero` (facultatif) sert pour 0 dans toutes les langues, comme « aucune offre » aujourd'hui.
export function tn(count: number, forms: Plural, params?: Params): string {
  const found = lookup(forms.other);
  const chosen: Plural = typeof found === "object" ? found : forms;
  const locale = found ? formatLocale() : "fr-CH";
  const rule = count === 0 && chosen.zero ? "zero" : new Intl.PluralRules(locale).select(count);
  return fill(chosen[rule] ?? chosen.other, { n: count, ...params });
}

// Change la langue (une langue relue seulement) : retenue sur l'appareil, `<html lang>` à jour, puis les catalogues
// des pages ouvertes.
export async function setLang(next: Lang, routes: string[] = []): Promise<void> {
  if (!isActive(next)) return;
  lang.value = next;
  try {
    localStorage.setItem(KEY, next);
  } catch {
    // Stockage indisponible : la langue vaut pour cette visite.
  }
  applyLang();
  await Promise.all(routes.map(loadRoute));
}
