// Prépare les illustrations de jobA1 (docs/67) : des images générées pour la plateforme.
//
//   node scripts/illustrations.mjs <dossier des images transparentes> [<dossier de la série sombre>]
//
// Pour chaque nom de ILLUSTRATIONS, prend l'original (1000 px de large, WebP transparent) et écrit
// src/assets/illustrations/<nom>-480.webp et <nom>-800.webp : le navigateur prend la plus petite
// qui reste nette (240 px affichés sur téléphone, jusqu'à 440 px sur ordinateur). Si la série sombre
// contient la même image, elle est écrite à côté (<nom>-sombre-480.webp…) ; sinon, en sombre, la
// version claire est simplement assombrie (feuille de style).
import { existsSync, mkdirSync, readdirSync, rmSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

import sharp from "sharp";

// nom dans la plateforme → fichier d'origine (sans .webp) ;
// `efface` : un rectangle [gauche, haut, largeur, hauteur] de l'original rendu transparent ;
// `ovale` : le cadre [gauche, haut, largeur, hauteur] gardé, arrondi et aux bords estompés (pour
// une scène sur fond plein, posée sur une autre couleur) ; `largeurs` : les tailles écrites.
export const ILLUSTRATIONS = {
  // La connexion (docs/67, complément 0.55.2) : la ville et le bureau, le garçon et la fille au centre.
  connexion: { source: "Connexion_Ville", ovale: [130, 300, 1180, 500], largeurs: [480, 800, 1200] },
  "accueil-reseau": { source: "15_Reseau" },
  "actualites-video": { source: "Actualites_C_Videos" },
  "alertes-carte": { source: "02_Alertes" },
  "aucune-offre": { source: "03_Offres_Aucune_Offre" },
  bilan: { source: "06_Bilan" },
  "emails-tries": { source: "00_Accueil_Banniere" },
  formations: { source: "06_Formations" },
  "lecture-calme": { source: "13_Parametres" },
  "lieux-carte": { source: "07_Profil" },
  // Le personnage qui parle (docs/66) : sa bulle vide est effacée, la nôtre se pose au-dessus.
  messager: { source: "12_Messagerie", efface: [475, 132, 340, 200] },
  "offres-profils": { source: "02_Candidatures_Offres" },
  "porte-ouverte": { source: "Actualites_A_Marche_Emploi" },
  "preuves-orp": { source: "04_Preuves_ORP" },
  "suivi-envoi": { source: "03_Candidatures_Suivi" },
  "tableau-de-bord": { source: "01_Dashboard" },
};

const OUT = fileURLToPath(new URL("../src/assets/illustrations/", import.meta.url));

// Le cadre : un rectangle aux coins très arrondis, flouté pour que ses bords s'estompent ; le
// milieu, où sont les personnages, reste net.
function oval(width, height) {
  const soft = Math.round(height * 0.06);
  return Buffer.from(
    `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}">` +
      `<defs><filter id="f" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="${soft}"/></filter></defs>` +
      `<rect x="${soft * 1.5}" y="${soft * 1.5}" width="${width - soft * 3}" height="${height - soft * 3}" ` +
      `rx="${height * 0.45}" ry="${height * 0.45}" fill="#000" filter="url(#f)"/></svg>`,
  );
}

// Les marges transparentes sont rognées : l'image remplit la place qu'on lui donne.
async function prepare(file, { efface, ovale }) {
  let image = sharp(file).ensureAlpha();
  if (ovale) {
    const [left, top, width, height] = ovale;
    const framed = await image.extract({ left, top, width, height }).png().toBuffer();
    return sharp(await sharp(framed).composite([{ input: oval(width, height), blend: "dest-in" }]).png().toBuffer());
  }
  if (efface) {
    const [left, top, width, height] = efface;
    const opaque = { create: { width, height, channels: 4, background: { r: 0, g: 0, b: 0, alpha: 1 } } };
    image = sharp(await image.composite([{ input: opaque, left, top, blend: "dest-out" }]).png().toBuffer());
  }
  return sharp(await image.trim({ background: { r: 0, g: 0, b: 0, alpha: 0 }, threshold: 1 }).png().toBuffer());
}

async function write(file, name, spec, suffix) {
  for (const width of spec.largeurs ?? [480, 800]) {
    const image = await prepare(file, spec);
    const target = join(OUT, `${name}${suffix}-${width}.webp`);
    await image.resize({ width }).webp({ quality: 82, effort: 6, alphaQuality: 90 }).toFile(target);
    console.log(`${target.slice(OUT.length)} ← ${file}`);
  }
}

const [light, dark] = process.argv.slice(2);
if (!light) {
  console.error("usage : node scripts/illustrations.mjs <transparentes> [<sombres>]");
  process.exit(1);
}
rmSync(OUT, { recursive: true, force: true });
mkdirSync(OUT, { recursive: true });
const darkFiles = dark && existsSync(dark) ? readdirSync(dark) : [];
for (const [name, spec] of Object.entries(ILLUSTRATIONS)) {
  await write(join(light, `${spec.source}.webp`), name, spec, "");
  if (darkFiles.includes(`${spec.source}.webp`)) await write(join(dark, `${spec.source}.webp`), name, spec, "-sombre");
}
