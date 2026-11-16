// Le budget de poids (docs/performance.md, docs/117 §3). Après `vite build`, le script mesure :
//   - le JavaScript : le premier écran (l'application et Aujourd'hui), tout le code, et page par page ;
//   - le CSS : tout le CSS, et chaque page de l'application une à une (CSS_PAGES, limites par page du 16.11) ;
//   - les images servies (dist/) : leur poids total, et les illustrations toutes en WebP (ou SVG).
// Chaque taille est donnée brute, en gzip et en brotli. La limite porte sur gzip pour le code et le CSS (ce que le
// serveur envoie : Caddy compresse en zstd ou gzip), sur le poids brut pour les images (déjà compressées).
// Au-delà d'une limite, le script échoue et dit quels fichiers pèsent le plus.
//
//     npm run poids                      (construit, puis mesure)
//     node scripts/poids.mjs --releve    (après un build : les limites à + 5 % des tailles d'aujourd'hui, + 3 % pour le CSS)
//     node scripts/poids.mjs --dist D --json F   (mesure le build D, écrit les tailles dans F ; scripts/poids-delta.sh)
//     node scripts/poids.mjs --base F    (F : les tailles de main ; scripts/poids-ci.sh, voir plus bas)
//
// Main qui dépasse déjà (Kevin, 16.11, docs/decisions/2026-11-16-1425-audit-poids-main-depasse.md) : avec --base, une
// mesure au-dessus de sa limite passe quand main la dépassait déjà et que la branche ne l'alourdit pas (taille égale
// ou plus petite que sur main). Seule une branche qui ajoute du poids à une mesure en dépassement reste bloquée.
import { readdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { join, relative } from "node:path";
import { brotliCompressSync, constants, gzipSync } from "node:zlib";

const arg = (name) => {
  const at = process.argv.indexOf(name);
  return at > 0 ? process.argv[at + 1] : undefined;
};
const DIST = arg("--dist") ?? new URL("../dist/", import.meta.url).pathname;

// Les limites : la taille mesurée le 2026-11-10 (main après la PR 20) + 5 %, arrondie à la centaine d'octets
// inférieure (décision de Kevin du 10.11 : « budget = taille compressée actuelle + 5 % maximum »). Pour en relever
// une, le dire dans la PR et noter la nouvelle valeur dans docs/performance.md.
export const LIMITS = {
  "js-premier": 111_500,
  "js-total": 431_500, // #764, #770 et #771 ensemble, sans découpage (Kevin, 16.11 14 h 19 : une fois, 428 780 → 431 500 ; docs/decisions/2026-11-16-1419-releve-js-trois-pr.md). Plus de relèvement hors de l'issue « Budget JS ».
  "js-accueil": 111_500,
  "js-candidatures": 168_000,
  "js-bilan": 113_400,
  "js-compte": 98_800,
  // Le CSS, page par page (Kevin, 16.11, issue #797 : docs/decisions/2026-11-16-1510-css-limites-par-page.md). Chaque
  // limite est le CSS que charge la page sur main le 16.11, + 3 %, arrondi à la centaine d'octets inférieure.
  // css-total, refixé une seule fois de la même façon, n'est plus qu'un garde-fou : ce qui compte, c'est la page ouverte.
  "css-total": 123_100, // refixé une fois avec les limites par page (119 581 sur main le 16.11, + 3 %)
  "css-accueil": 60_600, // le premier écran (l'ancien css-premier)
  "css-trier": 63_800,
  "css-candidatures": 71_100,
  "css-preparer": 69_200,
  "css-suivi": 72_200,
  "css-alertes": 61_800,
  "css-rendez-vous-orp": 65_000,
  "css-relances": 59_100,
  "css-bilan": 60_900,
  "css-resultats": 58_900,
  "css-formations": 59_800,
  "css-fiche-orp": 60_400,
  "css-entrainement": 59_800,
  "css-notifications": 61_100,
  "css-compte": 59_200,
  "css-profil": 63_100,
  "css-reglages": 60_400,
  "css-diagnostic": 57_900,
  "css-connexion": 59_700,
  "css-inscription": 58_200,
  "css-acces": 58_200,
  "css-bienvenue": 65_400,
  "css-getemall": 59_000,
  "css-extension": 57_900,
  "css-la-plateforme": 57_900,
  "css-tes-donnees": 58_100,
  "css-accessibilite": 57_900,
  "css-conditions": 57_900,
  "css-a-propos": 57_900,
  "css-introuvable": 58_900,
  images: 4_893_100,
};

// Les pages mesurées une à une pour le JS : la vue et ses sous-vues ouvertes par défaut (router.ts).
const PAGES = {
  accueil: ["views/TodayView.vue"],
  candidatures: ["views/JobsView.vue", "views/OffersView.vue"],
  bilan: ["views/BilanView.vue", "views/BilanOrpView.vue"],
  compte: ["views/AccountView.vue"],
};

// Les pages mesurées une à une pour le CSS : toutes les vues de router.ts, avec leur page parente (Candidatures,
// Bilan). Une vue qui n'est dans aucune page fait échouer le budget : une nouvelle page reçoit sa limite.
export const CSS_PAGES = {
  accueil: ["views/TodayView.vue"], // le premier écran
  trier: ["views/TriageView.vue"],
  candidatures: ["views/JobsView.vue", "views/OffersView.vue"], // Candidatures › Offres
  preparer: ["views/PreparationView.vue"],
  suivi: ["views/JobsView.vue", "views/ApplicationsView.vue"],
  alertes: ["views/JobsView.vue", "views/AlertsView.vue"],
  "rendez-vous-orp": ["views/JobsView.vue", "views/OrpMeetingView.vue"],
  relances: ["views/FollowUpsView.vue"],
  bilan: ["views/BilanView.vue", "views/BilanOrpView.vue"], // Bilan › ORP
  resultats: ["views/BilanView.vue", "views/InsightsView.vue"],
  formations: ["views/BilanView.vue", "views/TrainingsView.vue"],
  "fiche-orp": ["views/OrpFicheView.vue"],
  entrainement: ["views/PracticeView.vue"],
  notifications: ["views/NotificationsView.vue"],
  compte: ["views/AccountView.vue"],
  profil: ["views/ProfileView.vue"],
  reglages: ["views/SettingsView.vue"],
  diagnostic: ["views/DiagnosticView.vue"],
  connexion: ["views/LoginView.vue"],
  inscription: ["views/SignupView.vue"],
  acces: ["views/AccessView.vue"],
  bienvenue: ["views/WelcomeView.vue"],
  getemall: ["views/GetemallAuthorizeView.vue"],
  extension: ["views/ExtensionLinkView.vue"],
  "la-plateforme": ["views/DiscoverView.vue"],
  "tes-donnees": ["views/PrivacyView.vue"],
  accessibilite: ["views/AccessibilityView.vue"],
  conditions: ["views/TermsView.vue"],
  "a-propos": ["views/AboutView.vue"],
  introuvable: ["views/NotFoundView.vue"],
};

// Les dossiers d'illustrations : WebP (ou SVG) seulement. Les icônes de l'application (favicon, écran d'accueil)
// restent en PNG, comme le demandent les navigateurs.
const ILLUSTRATIONS = /^(illustrations|personnage|troupe|avatars)\//;
const IMAGE = /\.(png|jpe?g|gif|webp|avif|svg)$/i;

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
  "css-total": allCss,
  images,
};
for (const [page, paths] of Object.entries(PAGES)) {
  groups[`js-${page}`] = jsOf(loaded(paths));
}
for (const [page, paths] of Object.entries(CSS_PAGES)) groups[`css-${page}`] = cssOf(loaded(paths));

// Une limite sans page (une page retirée de CSS_PAGES) : le dire plutôt que planter.
const orphans = Object.keys(LIMITS).filter((name) => !groups[name]);
if (orphans.length) {
  console.log(`TROP limites sans page : ${orphans.join(", ")} (à ajouter dans CSS_PAGES ou à retirer de LIMITS)`);
  process.exit(1);
}

const kb = (bytes) => `${(bytes / 1000).toFixed(1)} Ko`;
const measured = Object.fromEntries(Object.entries(groups).map(([name, files]) => [name, sum(files)]));
const limited = (name) => (name === "images" ? measured[name].raw : measured[name].gzip);

if (arg("--json")) {
  writeFileSync(arg("--json"), JSON.stringify(Object.fromEntries(Object.keys(LIMITS).map((name) => [name, limited(name)]))));
  process.exit(0);
}

if (process.argv.includes("--releve")) {
  for (const name of Object.keys(LIMITS)) {
    const margin = name.startsWith("css-") ? 1.03 : 1.05;
    console.log(`  "${name}": ${Math.floor((limited(name) * margin) / 100) * 100},`);
  }
  process.exit(0);
}

const base = arg("--base") ? JSON.parse(readFileSync(arg("--base"), "utf8")) : {};
// Au-dessus de la limite, mais main la dépassait déjà et la branche n'ajoute rien : la mesure passe.
const tolerated = (name, limit) => base[name] > limit && limited(name) <= base[name];

let failed = false;
// Toutes les vues du manifeste sont mesurées dans une page CSS.
const inPages = new Set(Object.values(CSS_PAGES).flat());
const unmeasured = Object.keys(manifest)
  .map((key) => key.match(/src\/(views\/\w+\.vue)$/)?.[1])
  .filter((view) => view && !inPages.has(view));
if (unmeasured.length) {
  failed = true;
  console.log(`TROP vues sans limite de CSS : ${unmeasured.join(", ")} (à ajouter dans CSS_PAGES et LIMITS)`);
}
console.log(`${"".padEnd(5)}${"mesure".padEnd(17)}${"brut".padStart(10)}${"gzip".padStart(10)}${"brotli".padStart(10)}   limite`);
for (const [name, limit] of Object.entries(LIMITS)) {
  const within = limited(name) <= limit;
  const ok = within || tolerated(name, limit);
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
      (within ? "" : ok ? `  (au-dessus, mais main y est déjà : ${base[name]} o sur main, ${limited(name)} o ici, la branche n'ajoute rien)` : `  (les plus lourds : ${heaviest})`),
  );
}

// Les polices (woff2, déjà compressées) : relevées pour le tableau de poids des PR, sans limite. Aucune n'est
// préchargée : le navigateur ne télécharge une police que si un texte affiché l'utilise.
const fonts = walk(DIST).filter((file) => /\.woff2?$/i.test(file));
console.log(`    ${"polices".padEnd(17)}${kb(sum(fonts).raw).padStart(10)}   (brut, sans limite : ${fonts.map((file) => `${file.replace(/^assets\//, "").replace(/-[\w-]{8}\./, ".")} ${kb(sizes(file).raw)}`).join(", ")})`);

// Les illustrations en WebP : une image d'un dossier d'illustrations, ou importée par le code (assets/), dans un
// autre format fait échouer le budget.
const notWebp = images.filter((file) => (ILLUSTRATIONS.test(file) || file.startsWith("assets/")) && !/\.(webp|svg)$/i.test(file));
if (notWebp.length) {
  failed = true;
  console.log(`TROP illustrations hors WebP : ${notWebp.join(", ")}`);
}
process.exit(failed ? 1 : 0);
