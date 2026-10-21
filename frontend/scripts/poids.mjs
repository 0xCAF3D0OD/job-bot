// Le budget de poids (docs/117 §3) : après `npm run build`, la taille compressée (gzip) de ce
// que charge le premier écran (l'application et Aujourd'hui), de tout le code, et du CSS.
// Au-delà d'une limite, le script échoue et dit quel fichier pèse le plus.
//
//     npm run build && node scripts/poids.mjs
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { gzipSync } from "node:zlib";

const DIST = new URL("../dist/", import.meta.url).pathname;
export const LIMITS = { premier: 120_000, total: 270_000, css: 45_000 };

const manifest = JSON.parse(readFileSync(join(DIST, ".vite/manifest.json"), "utf8"));
const size = (file) => gzipSync(readFileSync(join(DIST, file))).length;

// Un fichier et tout ce qu'il importe d'emblée (pas les pages chargées plus tard).
function closure(key, seen = new Set()) {
  const entry = manifest[key];
  if (!entry || seen.has(entry.file)) return seen;
  seen.add(entry.file);
  for (const next of entry.imports ?? []) closure(next, seen);
  return seen;
}

const entry = Object.keys(manifest).find((key) => manifest[key].isEntry);
const today = Object.keys(manifest).find((key) => key.endsWith("views/TodayView.vue"));
const first = closure(today, closure(entry));
const js = Object.values(manifest).map((e) => e.file).filter((f) => f.endsWith(".js"));
const css = [...new Set(Object.values(manifest).flatMap((e) => e.css ?? []))];

const sum = (files) => [...new Set(files)].reduce((total, file) => total + size(file), 0);
const measured = { premier: sum([...first]), total: sum(js), css: sum(css) };
const heaviest = (files) =>
  [...files].map((file) => [file, size(file)]).sort((a, b) => b[1] - a[1]).slice(0, 3)
    .map(([file, bytes]) => `${file} ${(bytes / 1000).toFixed(1)} Ko`).join(", ");

let failed = false;
for (const [name, limit] of Object.entries(LIMITS)) {
  const ok = measured[name] <= limit;
  failed ||= !ok;
  const files = name === "premier" ? first : name === "total" ? js : css;
  console.log(
    `${ok ? "ok " : "TROP"} ${name.padEnd(8)} ${(measured[name] / 1000).toFixed(1)} Ko / ${limit / 1000} Ko` +
      (ok ? "" : `  (les plus lourds : ${heaviest(files)})`),
  );
}
process.exit(failed ? 1 : 0);
