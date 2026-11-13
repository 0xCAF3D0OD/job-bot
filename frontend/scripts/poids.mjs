// Le budget de poids (docs/performance.md, docs/117 §3). Après `vite build`, le script mesure :
//   - le JavaScript : le premier écran (l'application et Aujourd'hui), tout le code, et page par page ;
//   - le CSS : le premier écran, tout le CSS, et page par page (Accueil, Candidatures, Bilan, Compte) ;
//   - les images servies (dist/) : leur poids total, et les illustrations toutes en WebP (ou SVG).
// Chaque taille est donnée brute, en gzip et en brotli. La limite porte sur gzip pour le code et le CSS (ce que le
// serveur envoie : Caddy compresse en zstd ou gzip), sur le poids brut pour les images (déjà compressées).
// Au-delà d'une limite, le script échoue et dit quels fichiers pèsent le plus.
//
//     npm run poids                      (construit, puis mesure)
//     node scripts/poids.mjs --releve    (après un build : les limites à + 5 % des tailles d'aujourd'hui)
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative } from "node:path";
import { brotliCompressSync, constants, gzipSync } from "node:zlib";

const DIST = new URL("../dist/", import.meta.url).pathname;

// Les limites : la taille mesurée le 2026-11-10 (main après la PR 20) + 5 %, arrondie à la centaine d'octets
// inférieure (décision de Kevin du 10.11 : « budget = taille compressée actuelle + 5 % maximum »). Pour en relever
// une, le dire dans la PR et noter la nouvelle valeur dans docs/performance.md.
export const LIMITS = {
  "js-premier": 111_500,
  "js-total": 401_300,
  "js-accueil": 111_500,
  "js-candidatures": 162_400,
  "js-bilan": 113_400,
  "js-compte": 98_800,
  "css-premier": 59_800,
  "css-total": 100_000,
  "css-accueil": 59_800,
  "css-candidatures": 68_300,
  "css-bilan": 62_400,
  "css-compte": 61_200,
  images: 4_893_100,
};

// Les pages mesurées une à une : la vue et ses sous-vues ouvertes par défaut (router.ts).
const PAGES = {
  accueil: ["views/TodayView.vue"],
  candidatures: ["views/JobsView.vue", "views/OffersView.vue"],
  bilan: ["views/BilanView.vue", "views/BilanOrpView.vue"],
  compte: ["views/AccountView.vue"],
};

// Les dossiers d'illustrations : WebP (ou SVG) seulement. Les icônes de l'application (favicon, écran d'accueil)
// restent en PNG, comme le demandent les navigateurs.
const ILLUSTRATIONS = /^(illustrations|personnage|troupe|avatars)\//;
const IMAGE = /\.(png|jpe?g|gif|webp|avif|svg)$/i;
// Les anciens avatars en PNG (256 px) : plus lus par l'application (useProfileImage.ts sert les WebP), gardés en
// attendant l'accord de Kevin pour les retirer (610 Ko). Aucun autre PNG n'est admis dans ces dossiers.
const OLD_PNG = new Set([1, 2, 3, 4, 5, 6, 7, 8].map((n) => `avatars/avatar-${n}-256.png`));

const manifest = JSON.parse(readFileSync(join(DIST, ".vite/manifest.json"), "utf8"));
const cache = new Map();
function sizes(file) {
  if (!cache.has(file)) {
    const bytes = readFileSync(join(DIST, file));
    cache.set(file, {
      raw: bytes.length,
      gzip: gzipSync(bytes).length,
      brotli: brotliCompressSync(bytes, { params: { [constants.BROTLI_PARAM_QUALITY]: 11 } }).length,
    });
  }
  return cache.get(file);
}
const sum = (files) =>
  [...new Set(files)].reduce(
    (total, file) => {
      const s = sizes(file);
      return { raw: total.raw + s.raw, gzip: total.gzip + s.gzip, brotli: total.brotli + s.brotli };
    },
    { raw: 0, gzip: 0, brotli: 0 },
  );

// Un fichier et tout ce qu'il importe d'emblée (pas les pages chargées plus tard), par clé du manifeste.
function closure(key, seen = new Set()) {
  const entry = manifest[key];
  if (!entry || seen.has(key)) return seen;
  seen.add(key);
  for (const next of entry.imports ?? []) closure(next, seen);
  return seen;
}
const keyOf = (path) => {
  const key = Object.keys(manifest).find((k) => k.endsWith(path));
  if (!key) throw new Error(`${path} absent du manifeste de vite`);
  return key;
};
const entry = Object.keys(manifest).find((key) => manifest[key].isEntry);
const loaded = (paths) => paths.reduce((seen, path) => closure(keyOf(path), seen), closure(entry));
const jsOf = (keys) => [...keys].map((key) => manifest[key].file).filter((file) => file.endsWith(".js"));
const cssOf = (keys) => [...keys].flatMap((key) => manifest[key].css ?? []);

const allJs = Object.values(manifest).map((e) => e.file).filter((f) => f.endsWith(".js"));
const allCss = [...new Set(Object.values(manifest).flatMap((e) => e.css ?? []))];

function walk(dir) {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    return statSync(path).isDirectory() ? walk(path) : [relative(DIST, path)];
  });
}
const images = walk(DIST).filter((file) => IMAGE.test(file));

const groups = {
  "js-premier": jsOf(loaded(PAGES.accueil)),
  "js-total": allJs,
  "css-premier": cssOf(loaded(PAGES.accueil)),
  "css-total": allCss,
  images,
};
for (const [page, paths] of Object.entries(PAGES)) {
  groups[`js-${page}`] = jsOf(loaded(paths));
  groups[`css-${page}`] = cssOf(loaded(paths));
}

const kb = (bytes) => `${(bytes / 1000).toFixed(1)} Ko`;
const measured = Object.fromEntries(Object.entries(groups).map(([name, files]) => [name, sum(files)]));
const limited = (name) => (name === "images" ? measured[name].raw : measured[name].gzip);

if (process.argv.includes("--releve")) {
  for (const name of Object.keys(LIMITS)) {
    console.log(`  "${name}": ${Math.floor((limited(name) * 1.05) / 100) * 100},`);
  }
  process.exit(0);
}

let failed = false;
console.log(`${"".padEnd(5)}${"mesure".padEnd(17)}${"brut".padStart(10)}${"gzip".padStart(10)}${"brotli".padStart(10)}   limite`);
for (const [name, limit] of Object.entries(LIMITS)) {
  const ok = limited(name) <= limit;
  failed ||= !ok;
  const m = measured[name];
  const heaviest = [...new Set(groups[name])]
    .sort((a, b) => sizes(b).gzip - sizes(a).gzip)
    .slice(0, 3)
    .map((file) => `${file} ${kb(name === "images" ? sizes(file).raw : sizes(file).gzip)}`)
    .join(", ");
  console.log(
    `${ok ? "ok " : "TROP"} ${name.padEnd(17)}${kb(m.raw).padStart(10)}${kb(m.gzip).padStart(10)}${kb(m.brotli).padStart(10)}   ` +
      `${kb(limit)} (${name === "images" ? "brut" : "gzip"})` +
      (ok ? "" : `  (les plus lourds : ${heaviest})`),
  );
}

// Les illustrations en WebP : une image d'un dossier d'illustrations, ou importée par le code (assets/), dans un
// autre format fait échouer le budget.
const notWebp = images.filter((file) => (ILLUSTRATIONS.test(file) || file.startsWith("assets/")) && !/\.(webp|svg)$/i.test(file) && !OLD_PNG.has(file));
if (notWebp.length) {
  failed = true;
  console.log(`TROP illustrations hors WebP : ${notWebp.join(", ")}`);
}
process.exit(failed ? 1 : 0);
