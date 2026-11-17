import { ref } from "vue";

import type { Lang } from "./languages";

// La langue de l'interface (docs/147), la seule partie chargée sur toutes les pages : la langue choisie, `<html lang>`
// et les formats de date. Les traductions elles-mêmes (`t()`, `tn()`, catalogues) sont dans i18n.ts, chargé seulement
// par les écrans traduits et, hors du français, avant chaque page. La langue des documents (lettre, CV) est un autre
// réglage, dans Préparer : on n'y touche jamais ici.

// Les langues relues par une personne dont c'est la langue maternelle (Kevin, 17.11) : les seules qu'on peut choisir.
// Les autres restent grisées « Bientôt ». L'allemand et l'italien seront activés en premier.
export const ACTIVE: readonly Lang[] = ["fr"];

// La locale des dates, nombres et montants (Intl, jamais à la main) : la variante suisse quand ICU en a une utile.
// L'anglais en en-CH : « 1'000 » et « 17.11.2026 », là où en-GB écrirait « 1,000 » (docs/147 §4).
const FORMAT: Record<Lang, string> = {
  fr: "fr-CH",
  de: "de-CH",
  it: "it-CH",
  en: "en-CH",
  pt: "pt-PT",
  es: "es-ES",
  sq: "sq",
};

export const KEY = "jobA1-langue";
export const isActive = (code: string | null | undefined): code is Lang => ACTIVE.includes(code as Lang);

// Le choix enregistré passe toujours avant ; au premier lancement, la langue du navigateur si elle est l'une des
// langues activées ; sinon le français.
function initial(): Lang {
  try {
    const stored = localStorage.getItem(KEY);
    if (isActive(stored)) return stored;
  } catch {
    // Stockage indisponible : la langue du navigateur.
  }
  for (const tag of navigator.languages ?? [navigator.language]) {
    const code = tag?.slice(0, 2).toLowerCase();
    if (isActive(code)) return code;
  }
  return "fr";
}

export const lang = ref<Lang>(initial());

export function formatLocale(): string {
  return FORMAT[lang.value];
}

export function applyLang(): void {
  document.documentElement.lang = lang.value;
}

// Un format de date de la langue en cours, gardé une fois créé (créer un Intl.DateTimeFormat coûte).
const dateFormats = new Map<string, Intl.DateTimeFormat>();
export function dateFormat(options: Intl.DateTimeFormatOptions): Intl.DateTimeFormat {
  const id = `${formatLocale()}|${JSON.stringify(options)}`;
  let found = dateFormats.get(id);
  if (!found) {
    found = new Intl.DateTimeFormat(formatLocale(), options);
    dateFormats.set(id, found);
  }
  return found;
}
