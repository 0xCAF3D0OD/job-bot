// Le logo jobA1 (docs/100), copié de la planche « Le logo final » : un trait au stylo qui
// entoure, une seule fois, et qui dépasse ; au centre, un diamant pêche tracé au même trait.
// viewBox « 4 6 92 92 ». Ne pas redessiner : la planche fait foi.
export const LOGO_VIEWBOX = "4 6 92 92";
export const LOGO_LOOP =
  "M70 20 C 88 30, 92 58, 78 75 C 63 92, 30 91, 16 72 C 4 54, 14 26, 38 17 C 54 11, 70 14, 84 25 C 88 29, 90 32, 91 35";
export const LOGO_DIAMOND = "M50.8 32.0 C 52.2 45.0, 55.0 48.4, 68.5 51.4 C 55.5 53.8, 52.4 57.0, 49.6 68.5 C 47.4 57.2, 44.2 53.4, 32.5 50.4 C 44.8 48.2, 47.8 44.5, 50.2 35.0 L 51.6 30.0";
// À 32 px et moins, la planche agrandit un peu le diamant pour qu'il reste lisible.
export const LOGO_DIAMOND_SMALL_SIZE = "M50.9 28.8 C 52.6 44.0, 55.8 48.0, 71.6 51.5 C 56.4 54.3, 52.8 58.0, 49.5 71.4 C 47.0 58.2, 43.2 53.8, 29.6 50.3 C 43.9 47.7, 47.4 43.4, 50.2 32.3 L 51.9 26.5";

// La mascotte de l'assistant (docs/99), planche « La mascotte de l'Assistant » : un visage rond
// avec la pointe d'une bulle à droite, et trois expressions. viewBox « 0 0 100 100 ».
export const MASCOT_FACE = "M46 15 A35 35 0 0 1 79.7 40.5 L 91 48.6 C 92.2 49.4, 92.2 50.6, 91 51.4 L 79.7 59.5 A35 35 0 1 1 46 15 Z";
// L'étincelle à 4 branches, qui ne vit que dans l'IA.
export function mascotSparkle(cx: number, cy: number, r: number): string {
  // Les creux tirés vers les coins (k) donnent des branches dodues, comme sur la planche.
  const k = r * 0.16;
  return [
    `M${cx} ${cy - r}`,
    `Q${cx + k} ${cy - k} ${cx + r} ${cy}`,
    `Q${cx + k} ${cy + k} ${cx} ${cy + r}`,
    `Q${cx - k} ${cy + k} ${cx - r} ${cy}`,
    `Q${cx - k} ${cy - k} ${cx} ${cy - r} Z`,
  ].join(" ");
}
export const MASCOT_EYE_LEFT = { x: 33, y: 42 };
export const MASCOT_EYE_RIGHT = { x: 59, y: 42 };
// À l'écoute : l'œil fermé en arc, l'étincelle, le sourire.
export const MASCOT_CLOSED_EYE = "M26 45 C 28.5 37, 37.5 37, 40 45";
export const MASCOT_SMILE = "M29 60 C 37 71, 55 71, 63 60";
// Réfléchit : la bouche est un point, comme les yeux (docs/100).
export const MASCOT_MOUTH_DOT = { x: 46, y: 63 };
// A trouvé : le grand sourire ouvert, plein.
export const MASCOT_OPEN_SMILE = "M31 58 C 31 57, 32 56.5, 33 56.5 L 59 56.5 C 60 56.5, 61 57, 61 58 C 60.5 68.5, 54 74.5, 46 74.5 C 38 74.5, 31.5 68.5, 31 58 Z";
