// Le contrôle des catalogues de langue (docs/147 §5, `make i18n-check`, dans `make audits-ci`). Pour chaque catalogue
// src/locales/<langue>/<page>.json :
//   - complet : chaque texte `t("…")` et chaque pluriel `tn(n, { …, other: "…" })` des fichiers de la page
//     (src/locales/pages.json) a sa traduction ; aucune traduction orpheline (texte qui n'existe plus dans le code) ;
//   - mêmes variables `{nom}` que le français ;
//   - pluriels : une forme pour chaque catégorie de la langue (Intl.PluralRules), `other` toujours ;
//   - allemand de Suisse : jamais « ß » ;
//   - glossaire (docs/i18n/glossaire-<langue>.md) : un texte français qui contient un mot de « Contrôle FR » a une
//     traduction qui contient l'un des mots de « Contrôle ».
// Et pages.json : chaque page existe dans scripts/poids.mjs (ou `commun`), chaque fichier existe.
//
//     node scripts/i18n-check.mjs            (depuis frontend/)
import { existsSync, readdirSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";


const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, "..");
const SRC = join(ROOT, "src");
const LOCALES = join(SRC, "locales");
const DOCS = join(ROOT, "..", "docs", "i18n");
// Les noms de pages de poids.mjs, lus dans son texte (l'importer lancerait la mesure).
const POIDS = readFileSync(join(HERE, "poids.mjs"), "utf8");
const PAGES = Object.fromEntries(
  [...POIDS.slice(POIDS.indexOf("export const PAGES")).matchAll(/^\s{2}"?([\w-]+)"?: \[/gm)].map((m) => [m[1], true]),
);
const LANGS = ["de", "it", "en", "pt", "es", "sq"];
const FORMAT = { de: "de-CH", it: "it-CH", en: "en-CH", pt: "pt-PT", es: "es-ES", sq: "sq" };

const errors = [];
const fail = (where, message) => errors.push(`${where} : ${message}`);

// Les textes d'un fichier : `t("…")`, `t('…')` et la forme `other` de `tn(…, { …, other: "…" })`.
const STRING = String.raw`(["'])((?:\\.|(?!\1).)*)\1`;
const T_CALL = new RegExp(String.raw`\bt\(\s*${STRING}`, "g");
const TN_OTHER = new RegExp(String.raw`\btn\([^)]*?\bother:\s*${STRING}`, "gs");
const unescape = (text) => text.replace(/\\(["'\\])/g, "$1");
export function extract(code) {
  const found = new Set();
  for (const match of code.matchAll(T_CALL)) found.add(unescape(match[2]));
  for (const match of code.matchAll(TN_OTHER)) found.add(unescape(match[2]));
  return found;
}

const variables = (text) => [...text.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort().join(",");

// Un tableau de glossaire : les lignes avec un « Contrôle FR » et un « Contrôle ».
export function glossary(markdown) {
  const rows = markdown.split("\n").filter((line) => line.startsWith("| ") && !line.startsWith("| Id") && !line.startsWith("|---"));
  return rows
    .map((line) => line.split("|").slice(1, -1).map((cell) => cell.trim()))
    .filter((cells) => cells.length >= 7 && cells[5] && cells[6])
    .map((cells) => ({ id: cells[0], fr: cells[5].split(/,\s*/), target: cells[6].split(/,\s*/) }));
}
const escape = (word) => word.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
export function glossaryMisses(rows, source, translation) {
  const lower = translation.toLowerCase();
  return rows.filter(
    (row) =>
      row.fr.some((word) => new RegExp(`(^|[^\\p{L}])${escape(word)}([^\\p{L}]|$)`, "iu").test(source)) &&
      !row.target.some((word) => lower.includes(word.toLowerCase())),
  );
}

function main() {
  const pages = JSON.parse(readFileSync(join(LOCALES, "pages.json"), "utf8"));
  for (const [page, { files }] of Object.entries(pages)) {
    if (page !== "commun" && !PAGES[page]) fail(`pages.json`, `« ${page} » n'est pas une page de poids.mjs`);
    for (const file of files) if (!existsSync(join(SRC, file))) fail(`pages.json`, `${file} n'existe pas`);
  }
  for (const lang of LANGS) {
    const dir = join(LOCALES, lang);
    if (!existsSync(dir)) continue;
    const rules = new Intl.PluralRules(FORMAT[lang]).resolvedOptions().pluralCategories;
    const words = existsSync(join(DOCS, `glossaire-${lang}.md`)) ? glossary(readFileSync(join(DOCS, `glossaire-${lang}.md`), "utf8")) : [];
    for (const name of readdirSync(dir).filter((f) => f.endsWith(".json"))) {
      const page = name.replace(/\.json$/, "");
      const where = `locales/${lang}/${name}`;
      if (!pages[page]) {
        fail(where, `page absente de pages.json`);
        continue;
      }
      const catalog = JSON.parse(readFileSync(join(dir, name), "utf8"));
      const expected = new Set();
      for (const file of pages[page].files) for (const text of extract(readFileSync(join(SRC, file), "utf8"))) expected.add(text);
      for (const text of expected) if (!(text in catalog)) fail(where, `traduction manquante : « ${text} »`);
      for (const [source, value] of Object.entries(catalog)) {
        if (!expected.has(source)) fail(where, `texte qui n'est plus dans le code : « ${source} »`);
        const forms = typeof value === "string" ? { other: value } : value;
        if (typeof value === "object") {
          for (const rule of rules) if (!forms[rule]) fail(where, `« ${source} » : forme « ${rule} » manquante`);
        }
        for (const [rule, text] of Object.entries(forms)) {
          if (typeof text !== "string" || !text.trim()) fail(where, `« ${source} » (${rule}) : traduction vide`);
          else {
            // Un pluriel peut taire {n} dans une forme (« Une offre »), jamais ajouter une variable.
            const extra = variables(text).split(",").filter((v) => v && !variables(source).split(",").includes(v) && v !== "n");
            if (typeof value === "string" && variables(text) !== variables(source)) fail(where, `« ${source} » : variables différentes du français`);
            else if (extra.length) fail(where, `« ${source} » (${rule}) : variable inconnue ${extra.join(", ")}`);
            if (lang === "de" && text.includes("ß")) fail(where, `« ${text} » : « ß » interdit en allemand de Suisse, écrire « ss »`);
            for (const row of glossaryMisses(words, source, text)) fail(where, `« ${text} » : glossaire « ${row.id} », attendu ${row.target.join(" ou ")}`);
          }
        }
      }
    }
  }
  if (errors.length) {
    console.log(errors.map((e) => `TROP ${e}`).join("\n"));
    process.exit(1);
  }
  console.log("i18n : catalogues complets, variables, pluriels et glossaire respectés");
}

if (fileURLToPath(import.meta.url) === process.argv[1]) main();
