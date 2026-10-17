// Prépare les personnages animés du titre (docs/68) : un par heure, à la place du « 1 » de jobA1.
//
//   node scripts/personnages.mjs <dossier des versions animées>
//
// Pour chaque fichier undraw_<nom>_<code>.svg du dossier, écrit src/assets/personnages/<nom>.svg :
// - sans largeur ni hauteur fixes (la taille vient de la feuille de style) ;
// - couleurs en minuscules, pour que la feuille de style les reprenne au thème (`.drawing`) ;
// - classes et animations préfixées par le nom (`a-<nom>-…`), le « réduire les animations »
//   limité au personnage (`.brand-figure *`).
// Aucune forme n'est touchée : le script s'arrête si un tracé ou une forme diffère.
import { mkdirSync, readdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const OUT = fileURLToPath(new URL("../src/assets/personnages/", import.meta.url));

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
    .replace(/<style>([\s\S]*?)<\/style>/g, (_m, css) => `<style>${prefix(css).replace(/\*\s*\{/g, ".brand-figure * {")}</style>`)
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

const dir = process.argv[2];
if (!dir) {
  console.error("usage : node scripts/personnages.mjs <dossier des versions animées>");
  process.exit(1);
}
rmSync(OUT, { recursive: true, force: true });
mkdirSync(OUT, { recursive: true });
for (const file of readdirSync(dir).filter((f) => /^undraw_.+\.svg$/.test(f)).sort()) {
  const name = file.replace(/^undraw_/, "").replace(/_[^_]+\.svg$/, "");
  writeFileSync(join(OUT, `${name}.svg`), prepare(readFileSync(join(dir, file), "utf8"), name));
  console.log(`${name} ← ${file}`);
}
