// Le CSS inutilisé (docs/performance.md) : la couverture de Chrome (l'onglet Coverage des DevTools) sur Accueil,
// Candidatures et Bilan, à 390 et 1440 px, en clair et en sombre. Le script donne, page par page, la part du CSS
// chargé qui sert ; puis les règles qui ne servent sur aucune de ces pages, triées en deux listes :
//   - « à retirer » : aucune de leurs classes n'apparaît dans le code (src/, hors style.css et tests) ;
//   - « sert ailleurs » : une classe est encore écrite dans un composant (autre page, état, fenêtre).
// Rien n'est retiré par le script.
//
//     npm run build && npx vite preview --port 4173   (API de démo derrière, JOBBOT_DEV_API_URL)
//     node scripts/css-inutilise.mjs http://localhost:4173 > css-inutilise.txt
import { readdirSync, readFileSync, statSync } from "node:fs";
import { createRequire } from "node:module";
import { join } from "node:path";
import postcss from "postcss";

// Playwright n'est pas une dépendance de l'interface : celui de la machine (comme pour les audits en Python).
const { chromium } = createRequire(import.meta.url)("playwright");

const BASE = process.argv[2] ?? "http://localhost:4173";
const PAGES = { Accueil: "/aujourdhui", Candidatures: "/candidatures/offres", Bilan: "/bilan" };
const VIEWPORTS = [{ width: 390, height: 844 }, { width: 1440, height: 900 }];
const SCHEMES = ["light", "dark"];

const SRC = new URL("../src/", import.meta.url).pathname;
function walk(dir) {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    return statSync(path).isDirectory() ? walk(path) : [path];
  });
}
const code = walk(SRC)
  .filter((f) => /\.(vue|ts)$/.test(f) && !/\.test\.ts$/.test(f))
  .map((f) => readFileSync(f, "utf8"))
  .join("\n");

// Une classe est écrite dans le code : en toutes lettres, comme début d'un nom construit (`tone-${x}`, `b${n}`,
// `icon-${name}`), ou comme classe d'une transition de Vue (<Transition name="detail"> → .detail-enter-active).
const TRANSITION = /-(enter|leave)-(active|from|to)$|-move$/;
function isWritten(c) {
  if (code.includes(c)) return true;
  if (TRANSITION.test(c)) return code.includes(`"${c.replace(TRANSITION, "")}"`);
  if (c.startsWith("icon-")) return code.includes(`"${c.slice(5)}"`);
  const stem = c.replace(/(-[^-]+|\d+)$/, "");
  return stem !== c && (code.includes(`${stem}-\${`) || code.includes(`${stem}\${`) || code.includes(`"${stem}-`));
}

const browser = await chromium.launch({ executablePath: process.env.CHROME || undefined });
const used = new Map(); // url → { text, ranges[] }
const perPage = {};
for (const [page, path] of Object.entries(PAGES)) {
  const pageUsed = new Map();
  for (const viewport of VIEWPORTS) {
    for (const colorScheme of SCHEMES) {
      const context = await browser.newContext({ viewport, colorScheme });
      const tab = await context.newPage();
      await tab.coverage.startCSSCoverage();
      await tab.goto(BASE + path, { waitUntil: "networkidle" });
      await tab.waitForTimeout(800);
      // Le bas de la page aussi (ce qui ne s'affiche qu'au défilement).
      await tab.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
      await tab.waitForTimeout(300);
      for (const entry of await tab.coverage.stopCSSCoverage()) {
        if (!entry.url.includes("/assets/")) continue;
        for (const map of [used, pageUsed]) {
          const known = map.get(entry.url) ?? { text: entry.text, ranges: [] };
          known.ranges.push(...entry.ranges);
          map.set(entry.url, known);
        }
      }
      await context.close();
    }
  }
  perPage[page] = pageUsed;
}
await browser.close();

const overlaps = (ranges, start, end) => ranges.some((r) => r.start < end && r.end > start);
const usedBytes = (text, ranges) => {
  const marks = new Uint8Array(text.length);
  for (const r of ranges) marks.fill(1, r.start, r.end);
  return marks.reduce((n, m) => n + m, 0);
};

console.log("CSS chargé et CSS qui sert, page par page (union de 390 et 1440 px, clair et sombre) :");
for (const [page, map] of Object.entries(perPage)) {
  let total = 0, kept = 0;
  for (const { text, ranges } of map.values()) {
    total += text.length;
    kept += usedBytes(text, ranges);
  }
  console.log(`  ${page.padEnd(13)} ${(total / 1000).toFixed(1)} Ko chargés, ${(kept / 1000).toFixed(1)} Ko servent (${Math.round((100 * kept) / total)} %)`);
}

// Les règles qui ne servent sur aucune des trois pages.
const toRemove = [], elsewhere = [];
for (const [url, { text, ranges }] of used) {
  const root = postcss.parse(text);
  root.walkRules((rule) => {
    if (rule.parent?.type === "atrule" && /keyframes/.test(rule.parent.name)) return;
    const start = rule.source.start.offset, end = rule.source.end.offset + 1;
    if (overlaps(ranges, start, end)) return;
    const classes = [...new Set((rule.selector.match(/\.[a-zA-Z_][\w-]*/g) ?? []).map((c) => c.slice(1)))];
    if (!classes.length) return;
    const bytes = end - start;
    // Une classe « morte » n'apparaît nulle part dans le code, même comme début d'un nom construit (`tone-${x}`).
    const alive = classes.filter(isWritten);
    const media = rule.parent?.type === "atrule" ? ` @${rule.parent.name} ${rule.parent.params}` : "";
    const line = { selector: rule.selector.replace(/\s+/g, " ").slice(0, 110) + media, bytes, file: url.split("/").pop() };
    (alive.length < classes.length ? toRemove : elsewhere).push({ ...line, dead: classes.filter((c) => !alive.includes(c)) });
  });
}
const total = (list) => (list.reduce((n, r) => n + r.bytes, 0) / 1000).toFixed(1);
console.log(`\nÀ retirer : ${toRemove.length} règles, ${total(toRemove)} Ko bruts (une classe au moins n'est écrite nulle part dans src/) :`);
for (const r of toRemove.sort((a, b) => b.bytes - a.bytes)) console.log(`  ${String(r.bytes).padStart(5)} o  ${r.selector}   [${r.dead.join(", ")}]`);
console.log(`\nSert ailleurs : ${elsewhere.length} règles, ${total(elsewhere)} Ko bruts (autres pages, états, fenêtres : à garder).`);
