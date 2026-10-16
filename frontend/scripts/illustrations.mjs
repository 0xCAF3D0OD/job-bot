// Prépare les illustrations de jobA1 (docs/67) : des images générées pour la plateforme.
//
//   node scripts/illustrations.mjs <dossier des images transparentes> [<dossier de la série sombre>]
//
// Pour chaque nom de ILLUSTRATIONS, prend l'original (1000 px de large, WebP transparent) et écrit
// src/assets/illustrations/<nom>-480.webp : deux fois la taille affichée (220 px au plus), pour les
// écrans nets. Les grandes (connexion, Engagement) ont aussi <nom>-800.webp. Si la série sombre
// contient la même image, elle est écrite à côté (<nom>-sombre-480.webp…) ; sinon, en sombre, la
// version claire est simplement assombrie (feuille de style).
import { existsSync, mkdirSync, readdirSync, rmSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

import sharp from "sharp";

// nom dans la plateforme → fichier d'origine (sans .webp) ; `large` : aussi en 800 px ;
// `efface` : un rectangle [gauche, haut, largeur, hauteur] de l'original rendu transparent.
export const ILLUSTRATIONS = {
  "accueil-reseau": { source: "15_Reseau" },
  "actualites-video": { source: "Actualites_C_Videos" },
  "alertes-carte": { source: "02_Alertes" },
  "aucune-offre": { source: "03_Offres_Aucune_Offre" },
  bilan: { source: "06_Bilan" },
  "emails-tries": { source: "00_Accueil_Banniere", large: true },
  formations: { source: "06_Formations" },
  "lecture-calme": { source: "13_Parametres" },
  "lieux-carte": { source: "07_Profil" },
  // Le personnage qui parle (docs/66) : sa bulle vide est effacée, la nôtre se pose au-dessus.
  messager: { source: "12_Messagerie", efface: [475, 132, 340, 200] },
  "offres-profils": { source: "02_Candidatures_Offres" },
  "porte-ouverte": { source: "Actualites_A_Marche_Emploi", large: true },
  "preuves-orp": { source: "04_Preuves_ORP" },
  "suivi-envoi": { source: "03_Candidatures_Suivi" },
  "tableau-de-bord": { source: "01_Dashboard" },
};

const OUT = fileURLToPath(new URL("../src/assets/illustrations/", import.meta.url));

// Les marges transparentes sont rognées : l'image remplit la place qu'on lui donne.
async function prepare(file, { efface }) {
  let image = sharp(file).ensureAlpha();
  if (efface) {
    const [left, top, width, height] = efface;
    const opaque = { create: { width, height, channels: 4, background: { r: 0, g: 0, b: 0, alpha: 1 } } };
    image = sharp(await image.composite([{ input: opaque, left, top, blend: "dest-out" }]).png().toBuffer());
  }
  return sharp(await image.trim({ background: { r: 0, g: 0, b: 0, alpha: 0 }, threshold: 1 }).png().toBuffer());
}

async function write(file, name, spec, suffix) {
  for (const width of spec.large ? [480, 800] : [480]) {
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
