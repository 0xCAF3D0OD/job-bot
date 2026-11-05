// Les formes d'humeur (maquette Animations, docs/139 étape 12), dans un carré de 100 sur 100.
// Le feston pêche (soleil) : 12 pointes, rayon de 40,5 à 47, les creux arrondis.
export const SUN =
  "M" +
  Array.from({ length: 144 }, (_, i) => {
    const a = (i / 144) * Math.PI * 2;
    const r = 40.5 + 6.5 * (1 - Math.abs(((i % 12) / 12) * 2 - 1)) ** 1.6;
    return `${(50 + r * Math.cos(a)).toFixed(1)} ${(50 + r * Math.sin(a)).toFixed(1)}`;
  }).join("L") +
  "Z";
// Le feston d'attente : une vague de 9 bosses, rayon 44 ± 3,2.
export const WAVE =
  "M" +
  Array.from({ length: 90 }, (_, i) => {
    const a = (i / 90) * Math.PI * 2;
    const r = 44 + 3.2 * Math.cos(9 * a);
    return `${(50 + r * Math.cos(a)).toFixed(1)} ${(50 + r * Math.sin(a)).toFixed(1)}`;
  }).join("L") +
  "Z";
