// Le logo jobA1 (docs/103) : le visage du 1. Le 1 du nom trace le sourcil et le nez, un œil
// bleu, un œil pêche (la bille), un sourire discret. viewBox « 8 8 86 86 », trait de 14.
export const LOGO_VIEWBOX = "8 8 86 86";
// Le visage du 1 cadré au plus près de son dessin (de l'œil à la bille, du 1 à la bouche) : il
// remplit sa taille au lieu de paraître plus petit (1.6.5 dans la note, 1.6.6 partout).
export const FACE_VIEWBOX = "13 15 74 74";
// S4, l'en-tête : le visage penché de −6° autour du centre.
export const LOGO_TILT = "rotate(-6 50 50)";
export const LOGO_ONE = "M43 31 L54 22 V56";
export const LOGO_EYE = { x: 24, y: 45, r: 10 };
export const LOGO_SPARK = { x: 76, y: 41, r: 10 };
export const LOGO_SMILE = "M28 72 C 40 82, 60 82, 72 70";
// S5, les icônes : le visage droit, le sourire plus court, dans un carré bleu
// (frontend/scripts/icones.py).
export const ICON_ONE = "M43 33 L54 24 V58";
export const ICON_EYE = { x: 24, y: 46 };
export const ICON_SPARK = { x: 76, y: 44 };
export const ICON_SMILE = "M32 74 C 42 80, 58 80, 68 74";

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

// Le visage du 1 et ses quatre humeurs (docs/123 §1) : le visage droit des icônes (S5), seule
// la bouche change. Jamais déçu : pas de bouche qui tombe.
export type Mood = "ravi" | "content" | "attentif" | "neutre";
export const FACE_MOUTH: Record<Mood, string> = {
  ravi: "M28 70 C 38 84, 62 84, 72 70",
  content: ICON_SMILE,
  attentif: "M34 75 L 66 75",
  neutre: "M40 76 L 60 76",
};
