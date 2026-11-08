// Le budget de poids (docs/117 §3) : après `npm run build`, la taille compressée (gzip) de ce
// que charge le premier écran (l'application et Aujourd'hui), de tout le code, du CSS de ce premier
// écran (« css-premier ») et de tout le CSS. Au-delà d'une limite, le script échoue et dit quel
// fichier pèse le plus.
//
//     npm run build && node scripts/poids.mjs
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { gzipSync } from "node:zlib";

const DIST = new URL("../dist/", import.meta.url).pathname;
// Relevé pour la maquette du 8 novembre (docs/143, lot 3 : panneaux de l'en-tête, image de profil, Composer).
export const LIMITS = { premier: 120_000, total: 332_000, "css-premier": 53_000, css: 70_000 };

const manifest = JSON.parse(readFileSync(join(DIST, ".vite/manifest.json"), "utf8"));
const size = (file) => gzipSync(readFileSync(join(DIST, file))).length;

// Un fichier et tout ce qu'il importe d'emblée (pas les pages chargées plus tard), par clé du manifeste.
function closure(key, seen = new Set()) {
  const entry = manifest[key];
  if (!entry || seen.has(key)) return seen;
  seen.add(key);
  for (const next of entry.imports ?? []) closure(next, seen);
  return seen;
}

const entry = Object.keys(manifest).find((key) => manifest[key].isEntry);
const today = Object.keys(manifest).find((key) => key.endsWith("views/TodayView.vue"));
const firstKeys = closure(today, closure(entry));
const first = new Set([...firstKeys].map((key) => manifest[key].file));
// Le CSS que le premier écran charge d'emblée : celui de l'entrée et de ses imports, puis d'Aujourd'hui.
const firstCss = new Set([...firstKeys].flatMap((key) => manifest[key].css ?? []));
const js = Object.values(manifest).map((e) => e.file).filter((f) => f.endsWith(".js"));
const css = [...new Set(Object.values(manifest).flatMap((e) => e.css ?? []))];

const sum = (files) => [...new Set(files)].reduce((total, file) => total + size(file), 0);
const measured = { premier: sum([...first]), total: sum(js), "css-premier": sum([...firstCss]), css: sum(css) };
const heaviest = (files) =>
  [...files].map((file) => [file, size(file)]).sort((a, b) => b[1] - a[1]).slice(0, 3)
    .map(([file, bytes]) => `${file} ${(bytes / 1000).toFixed(1)} Ko`).join(", ");

let failed = false;
for (const [name, limit] of Object.entries(LIMITS)) {
  const ok = measured[name] <= limit;
  failed ||= !ok;
  const files = { premier: first, total: js, "css-premier": firstCss, css }[name];
  console.log(
    `${ok ? "ok " : "TROP"} ${name.padEnd(11)} ${(measured[name] / 1000).toFixed(1)} Ko / ${limit / 1000} Ko` +
      (ok ? "" : `  (les plus lourds : ${heaviest(files)})`),
  );
}
process.exit(failed ? 1 : 0);
