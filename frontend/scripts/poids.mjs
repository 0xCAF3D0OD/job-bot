// Le budget de poids (docs/performance.md, docs/117 §3). Après `vite build`, le script mesure :
//   - le JavaScript et le CSS de chaque page de l'application, une à une (PAGES) : ce sont eux qui ont une limite ;
//   - le JavaScript et le CSS au total (js-total, css-total) : affichés, pas bloquants (Kevin, 16.11) ;
//   - les images servies (dist/) : leur poids total, et les illustrations toutes en WebP (ou SVG).
// Chaque taille est donnée brute, en gzip et en brotli. La limite porte sur gzip pour le code et le CSS (ce que le
// serveur envoie : Caddy compresse en zstd ou gzip), sur le poids brut pour les images (déjà compressées).
// Au-delà d'une limite, le script échoue et dit quels fichiers pèsent le plus.
//
//     npm run poids                      (construit, puis mesure)
//     node scripts/poids.mjs --releve    (après un build : les tailles d'aujourd'hui + 5 %)
//     node scripts/poids.mjs --dist D --json F   (mesure le build D, écrit les tailles dans F ; scripts/poids-delta.sh)
//     node scripts/poids.mjs --base F    (F : les tailles de main ; scripts/poids-ci.sh : avant/après, voir plus bas)
//
// Main qui dépasse déjà (Kevin, 16.11, docs/decisions/2026-11-16-1425-audit-poids-main-depasse.md) : avec --base, une
// mesure au-dessus de sa limite passe quand main la dépassait déjà et que la branche ne l'alourdit pas (taille égale
// ou plus petite que sur main). Seule une branche qui ajoute du poids à une mesure en dépassement reste bloquée.
import { appendFileSync, existsSync, readdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { join, relative } from "node:path";
import { brotliCompressSync, constants, gzipSync } from "node:zlib";

const arg = (name) => {
  const at = process.argv.indexOf(name);
  return at > 0 ? process.argv[at + 1] : undefined;
};
const DIST = arg("--dist") ?? new URL("../dist/", import.meta.url).pathname;

// Les limites par page (Kevin, 16.11, issue #797 : docs/decisions/2026-11-16-1518-limites-par-page.md). Pour chaque
// page, la plus basse entre (a) le budget public d'un téléphone moyen en 4G (365 Kio de JS et 365 Kio pour le reste,
// gzip, The Performance Inequality Gap 2024) et (b) la mesure de main le 16.11 + 5 %, arrondie à la centaine
// d'octets inférieure. Aujourd'hui (b) est toujours la plus basse. Ces limites sont fixées une fois et ne se relèvent
// jamais : une PR qui dépasse compense sur sa propre page ou attend. Seule exception : une décision écrite dans
// docs/decisions/ avec l'accord de Kevin.
export const LIMITS = {
  "js-accueil": 108_600, // Aujourd'hui : le premier écran
  "js-accueil-telephone": 113_700,
  "js-accueil-ordinateur": 115_000,
  "js-trier": 106_000,
  "js-candidatures": 175_500,
  "js-preparer": 157_400,
  "js-preparer-panneaux": 157_400,
  "js-suivi": 176_800,
  "js-alertes": 124_800,
  "js-rendez-vous-orp": 134_700,
  "js-relances": 106_100,
  "js-bilan": 114_900,
  "js-resultats": 111_000,
  "js-formations": 117_500,
  "js-fiche-orp": 98_200,
  "js-entrainement": 99_900,
  "js-notifications": 98_500,
  "js-compte": 97_500,
  "js-profil": 135_800,
  "js-reglages": 137_800,
  "js-diagnostic": 98_000,
  "js-connexion": 100_000,
  "js-inscription": 97_900,
  "js-acces": 98_000,
  "js-bienvenue": 119_200,
  "js-getemall": 96_300,
  "js-extension": 95_600,
  "js-la-plateforme": 98_700,
  "js-tes-donnees": 97_800,
  "js-accessibilite": 94_800,
  "js-conditions": 95_400,
  "js-a-propos": 95_000,
  "js-introuvable": 94_800,
  "css-accueil": 61_800, // Aujourd'hui : le premier écran
  "css-accueil-telephone": 63_200,
  "css-accueil-ordinateur": 64_400,
  "css-trier": 65_000,
  "css-candidatures": 72_500,
  "css-preparer": 70_500,
  "css-preparer-panneaux": 70_500,
  "css-suivi": 73_600,
  "css-alertes": 63_000,
  "css-rendez-vous-orp": 66_300,
  "css-relances": 60_300,
  "css-bilan": 62_100,
  "css-resultats": 60_000,
  "css-formations": 60_900,
  "css-fiche-orp": 61_500,
  "css-entrainement": 61_000,
  "css-notifications": 62_200,
  "css-compte": 60_300,
  "css-profil": 64_300,
  "css-reglages": 61_600,
  "css-diagnostic": 59_000,
  "css-connexion": 60_900,
  "css-inscription": 59_300,
  "css-acces": 59_300,
  "css-bienvenue": 66_700,
  "css-getemall": 60_100,
  "css-extension": 59_000,
  "css-la-plateforme": 59_000,
  "css-tes-donnees": 59_200,
  "css-accessibilite": 59_000,
  "css-conditions": 59_000,
  "css-a-propos": 59_000,
  "css-introuvable": 60_000,
  images: 4_893_100,
};

// Affichés à chaque mesure, sans limite (Kevin, 16.11) : ce n'est pas ce que charge une page.
const TOTALS = ["js-total", "css-total"];

// Les pages mesurées une à une : toutes les vues de router.ts, avec leur page parente (Candidatures, Bilan). Une page
// compte l'application (le socle), sa vue et ce qu'elles importent d'emblée. Une vue qui n'est dans aucune page fait
// échouer le budget : une nouvelle page reçoit ses limites dans la PR qui la crée.
export const PAGES = {
  accueil: ["views/TodayView.vue"], // le premier écran
  // Aujourd'hui charge ensuite, à part, son bloc selon l'écran : l'accueil du téléphone ou le mini-tri de l'ordinateur.
  "accueil-telephone": ["views/TodayView.vue", "components/HomePhone.vue"],
  "accueil-ordinateur": ["views/TodayView.vue", "components/TriageMini.vue"],
  trier: ["views/TriageView.vue"],
  candidatures: ["views/JobsView.vue", "views/OffersView.vue"], // Candidatures › Offres
  preparer: ["views/PreparationView.vue"],
  // Préparer avec l'étape CV et tous ses panneaux chargés à la demande ouverts (allègement (c), issue #797) : le pire cas garde les
  // limites de Préparer d'avant l'allègement, pour qu'ouvrir un panneau ne coûte jamais plus qu'avant.
  "preparer-panneaux": [
    "views/PreparationView.vue",
    "components/ApplicationSent.vue",
    "components/GoalReached.vue",
    "components/OfferCompatSheet.vue",
    "components/FalseClaimSheet.vue",
    "components/ProfileCompletionPanel.vue",
    "components/CvPanel.vue",
  ],
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
    // Les empreintes des noms de fichiers (« OffersView-CBxXxxP9.js ») changent à chaque PR et font varier le gzip de
    // +13 à +21 o sans rien changer au code : on les remplace par une empreinte fixe avant de mesurer le JS et le CSS.
    const read = readFileSync(join(DIST, file));
    const bytes = /\.(js|css)$/.test(file)
      ? Buffer.from(read.toString("utf8").replace(/-[\w-]{8}\.(js|css|woff2?|webp|svg|png|jpe?g|avif)\b/g, "-xxxxxxxx.$1"))
      : read;
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
// La clé d'un fichier de PAGES. Un composant importé à la fois d'emblée et à la demande devient un bloc partagé, nommé
// « _Composant-empreinte.js ». Un composant sans bloc à lui est fondu dans le bloc qui l'importe, déjà compté : il
// n'ajoute rien (null). Un fichier qui n'existe pas dans src/ est une faute de frappe : on s'arrête.
const keyOf = (path) => {
  const keys = Object.keys(manifest);
  const name = path.split("/").pop().replace(/\.vue$/, "");
  const key = keys.find((k) => k.endsWith(path)) ?? keys.find((k) => new RegExp(`^_${name}-[\\w-]{8}\\.js$`).test(k));
  if (key) return key;
  if (/^components\//.test(path) && existsSync(new URL(`../src/${path}`, import.meta.url))) return null;
  throw new Error(`${path} absent du manifeste de vite`);
};
const entry = Object.keys(manifest).find((key) => manifest[key].isEntry);
const loaded = (paths) =>
  paths.reduce((seen, path) => {
    const key = keyOf(path);
    return key ? closure(key, seen) : seen;
  }, closure(entry));
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
  "js-total": allJs,
  "css-total": allCss,
  images,
};
for (const [page, paths] of Object.entries(PAGES)) {
  groups[`js-${page}`] = jsOf(loaded(paths));
  groups[`css-${page}`] = cssOf(loaded(paths));
}

// Une limite sans page (une page retirée de PAGES) : le dire plutôt que planter.
const orphans = Object.keys(LIMITS).filter((name) => !groups[name]);
if (orphans.length) {
  console.log(`TROP limites sans page : ${orphans.join(", ")} (à ajouter dans PAGES ou à retirer de LIMITS)`);
  process.exit(1);
}

const kb = (bytes) => `${(bytes / 1000).toFixed(1)} Ko`;
const measured = Object.fromEntries(Object.entries(groups).map(([name, files]) => [name, sum(files)]));
const limited = (name) => (name === "images" ? measured[name].raw : measured[name].gzip);

if (arg("--json")) {
  writeFileSync(arg("--json"), JSON.stringify(Object.fromEntries([...Object.keys(LIMITS), ...TOTALS].map((name) => [name, limited(name)]))));
  process.exit(0);
}

if (process.argv.includes("--releve")) {
  for (const name of Object.keys(LIMITS)) {
    console.log(`  "${name}": ${Math.floor((limited(name) * 1.05) / 100) * 100},`);
  }
  process.exit(0);
}

const base = arg("--base") ? JSON.parse(readFileSync(arg("--base"), "utf8")) : {};
// Au-dessus de la limite, mais main la dépassait déjà et la branche n'ajoute rien : la mesure passe.
const tolerated = (name, limit) => base[name] > limit && limited(name) <= base[name];

let failed = false;
// Toutes les vues, et tout bloc chargé à part (import() hors des vues), sont mesurés dans une page.
const inPages = new Set(Object.values(PAGES).flat());
const unmeasured = Object.keys(manifest)
  .filter((key) => /src\/views\/\w+\.vue$/.test(key) || manifest[key].isDynamicEntry)
  .map((key) => key.replace(/^.*?src\//, ""))
  .filter((file) => !inPages.has(file));
if (unmeasured.length) {
  failed = true;
  console.log(`TROP vues ou blocs chargés à part sans limite : ${unmeasured.join(", ")} (à ajouter dans PAGES, et leurs limites dans LIMITS)`);
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

// Les totaux : affichés, sans limite.
for (const name of TOTALS) {
  const m = measured[name];
  console.log(`    ${name.padEnd(17)}${kb(m.raw).padStart(10)}${kb(m.gzip).padStart(10)}${kb(m.brotli).padStart(10)}   (gzip, sans limite)`);
}

// Avant/après (avec --base) : les mesures que la branche change, pour la PR. Dans la CI, aussi dans le résumé de
// l'exécution (GITHUB_STEP_SUMMARY) et en note sur la PR.
if (arg("--base")) {
  const changed = [...Object.keys(LIMITS), ...TOTALS].filter((name) => base[name] !== undefined && base[name] !== limited(name));
  const line = (name) => {
    const d = limited(name) - base[name];
    const limit = LIMITS[name] ? ` (limite ${LIMITS[name]})` : " (sans limite)";
    return `${name} : ${base[name]} → ${limited(name)} o, ${d > 0 ? "+" : ""}${d}${limit}`;
  };
  const pages = changed.filter((name) => !TOTALS.includes(name));
  console.log(`\nAvant/après (main → branche, octets) : ${pages.length ? `${pages.length} mesure(s) de page changée(s)` : "aucune page changée"}`);
  for (const name of changed) console.log(`  ${line(name)}`);
  if (process.env.GITHUB_ACTIONS) {
    // En bref : par sorte (JS, CSS), le nombre de pages changées, l'écart le plus fort et la marge la plus petite.
    const brief = ["js", "css"].flatMap((kind) => {
      const names = pages.filter((name) => name.startsWith(`${kind}-`));
      if (!names.length) return [];
      const deltas = names.map((name) => limited(name) - base[name]);
      const top = names[deltas.indexOf(Math.max(...deltas))];
      const tight = names.reduce((a, b) => (LIMITS[a] - limited(a) <= LIMITS[b] - limited(b) ? a : b));
      return [
        `${kind.toUpperCase()} : ${names.length} page(s), de ${Math.min(...deltas)} à ${Math.max(...deltas)} o ; la plus touchée ${top.slice(kind.length + 1)} (${line(top)}) ; ` +
          `marge la plus petite ${tight.slice(kind.length + 1)} (${LIMITS[tight] - limited(tight)} o)`,
      ];
    });
    const totals = TOTALS.map((name) => `${name} ${limited(name) - base[name] > 0 ? "+" : ""}${limited(name) - base[name]} o`).join(", ");
    const notice = [...(brief.length ? brief : ["aucune page changée"]), `totaux (sans limite) : ${totals}`].join(" ; ");
    console.log(`::notice title=Poids avant/après (gzip)::${notice}`);
  }
  if (process.env.GITHUB_STEP_SUMMARY) {
    const rows = changed.map((name) => {
      const d = limited(name) - base[name];
      return `| ${name} | ${base[name]} | ${limited(name)} | ${d > 0 ? "+" : ""}${d} | ${LIMITS[name] ?? "—"} |`;
    });
    appendFileSync(
      process.env.GITHUB_STEP_SUMMARY,
      `## Poids avant/après (gzip, octets)\n\n` +
        (rows.length ? `| Mesure | main | branche | écart | limite |\n|---|---:|---:|---:|---:|\n${rows.join("\n")}\n` : "Aucune page changée.\n"),
    );
  }
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
