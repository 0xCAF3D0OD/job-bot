// Le personnage de jobA1 (kit du 6.11.2026, docs/141) : une pose du kit, en 400 px (1×) et 800 px (2×).
// Il marque un moment ou remplit un écran plein ; jamais sur un écran de travail, jamais avec une petite
// mascotte d'humeur ni le logo transformé sur le même écran (docs/141 §1, test personnage.test.ts).
export type Pose =
  | "debout"
  | "bonjour"
  | "cv"
  | "marche"
  | "assis"
  | "perplexe"
  | "revelation"
  | "avion"
  | "cables"
  | "hors-ligne"
  | "loupe"
  | "celebration";

// Dans l'ordre des numéros du kit (perso-01 à perso-12).
const ORDER: Pose[] = ["debout", "bonjour", "cv", "marche", "assis", "perplexe", "revelation", "avion", "cables", "hors-ligne", "loupe", "celebration"];

// Les poses sont servies telles quelles depuis public/personnage/ : pas d'adresses hachées dans le code (24
// adresses, 1,2 Ko de moins dans le budget de poids, docs/117). `KIT` change quand le kit change, pour
// que les navigateurs reprennent les nouvelles images.
export const KIT = "20261106";
export function poseFile(pose: Pose, size: 400 | 800): string {
  return `/personnage/perso-${String(ORDER.indexOf(pose) + 1).padStart(2, "0")}-${pose}-${size}.webp?v=${KIT}`;
}
