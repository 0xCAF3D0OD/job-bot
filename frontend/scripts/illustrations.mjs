// Prépare les illustrations unDraw pour la plateforme (docs/58).
//
//   node scripts/illustrations.mjs <dossier des versions animées> [<dossier des originaux>…]
//
// Pour chaque nom de ILLUSTRATIONS, prend la version animée (sinon l'original), et écrit
// src/assets/illustrations/<nom>.svg :
// - sans largeur ni hauteur fixes (la taille vient du composant `Illustration`) ;
// - couleurs en minuscules, pour que la feuille de style les reprenne au thème
//   (`.illu [fill="#6c63ff"]`, docs/58 §2) ;
// - classes et animations préfixées par le nom (`a-<nom>-…`), pour ne pas se mêler entre
//   illustrations ; le « réduire les animations » limité à l'illustration ;
// - animations jouées **une seule fois** à l'apparition (docs/59 §5) : la boucle devient un
//   passage, qui finit sur l'image d'origine.
// Aucune forme n'est touchée : le script s'arrête si un tracé ou une forme diffère.
import { readdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

export const ILLUSTRATIONS = [
  "absorbed",
  "certification",
  "done",
  "handshake-deal",
  "lock-screen-notifications",
  "login",
  "mailbox",
  "message-sent",
  "morning-plans",
  "my-resume",
  "page-eaten",
  "stepping-up",
  "tight-deadline",
];

const OUT = new URL("../src/assets/illustrations/", import.meta.url);

function find(dirs, name) {
  for (const dir of dirs) {
    const file = readdirSync(dir).find((f) => f.startsWith(`undraw_${name}_`) && f.endsWith(".svg"));
    if (file) return join(dir, file);
  }
  throw new Error(`introuvable : ${name}`);
}

// Ce qui dessine : les tracés et formes, sans leurs couleurs ni classes.
function shapes(svg) {
  return [...svg.matchAll(/<(path|rect|circle|ellipse|polygon|polyline|line)\b([^>]*)>/g)].map(([, tag, attrs]) =>
    tag + attrs.replace(/\s(class|style|fill|stroke)="[^"]*"/g, "").trim(),
  );
}

function prepare(svg, name) {
  const prefix = (text) => text.replace(/\ba-([a-z][\w-]*)/g, `a-${name}-$1`);
  let out = svg
    .replace(/<svg\b[^>]*>/, (tag) => tag.replace(/\s(width|height|role|artist|source)="[^"]*"/g, ""))
    .replace(/(fill|stroke|stop-color)="(#[0-9a-fA-F]{3,6})"/g, (_m, attr, hex) => `${attr}="${hex.toLowerCase()}"`)
    .replace(
      /<style>([\s\S]*?)<\/style>/g,
      (_m, css) => `<style>${prefix(css).replace(/\*\s*\{/g, ".illu * {").replace(/\binfinite\b/g, "1")}</style>`,
    )
    .replace(/\sclass="([^"]*)"/g, (_m, names) => ` class="${prefix(names)}"`)
    .replace(/\sstyle="([^"]*)"/g, (_m, css) => ` style="${prefix(css)}"`);
  out = out.replace(/<\?xml[^>]*>\s*/, "").trim() + "\n";
  const before = shapes(svg);
  const after = shapes(out);
  if (before.length !== after.length || before.some((s, i) => s !== after[i])) {
    throw new Error(`${name} : une forme a changé`);
  }
  return out;
}

const dirs = process.argv.slice(2);
if (!dirs.length) {
  console.error("usage : node scripts/illustrations.mjs <animées> [<originaux>…]");
  process.exit(1);
}
for (const name of ILLUSTRATIONS) {
  const source = find(dirs, name);
  writeFileSync(new URL(`${name}.svg`, OUT), prepare(readFileSync(source, "utf8"), name));
  console.log(`${name} ← ${source}`);
}
