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
export const KIT = "20261108";
export function poseFile(pose: Pose, size: 400 | 800): string {
  return `/personnage/perso-${String(ORDER.indexOf(pose) + 1).padStart(2, "0")}-${pose}-${size}.webp?v=${KIT}`;
}

// Les bustes (MODIFICATIONS du 8 novembre au soir, lot 16.3) : le haut du corps, fondu en bas dans le fichier,
// pour les écrans de téléphone où le personnage partage la place avec un formulaire. Largeur et hauteur des
// fichiers -400.
export const BUST: Partial<Record<Pose, { width: number; height: number }>> = {
  debout: { width: 129, height: 215 },
  bonjour: { width: 150, height: 220 },
  cv: { width: 130, height: 220 },
  revelation: { width: 196, height: 220 },
};
export function bustFile(pose: Pose, size: 400 | 800): string {
  const number = String(ORDER.indexOf(pose) + 1).padStart(2, "0");
  const name = pose === "debout" ? "buste" : `${pose}-buste`;
  return `/personnage/perso-${number}-${name}-${size}.webp?v=${KIT}`;
}
