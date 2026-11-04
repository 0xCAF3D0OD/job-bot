// Entrée des chiffres et des barres (docs/60 §3) : une fois par visite, à la première ouverture
// d'Aujourd'hui et du Bilan ; jamais si « réduire les animations » est demandé.
const seen = new Set<string>();

export function motionAllowed(): boolean {
  return typeof window.matchMedia === "function" && !window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

// Vrai la première fois qu'un élément s'affiche dans la visite (pour ajouter la classe `intro`).
export function firstTime(key: string): boolean {
  if (seen.has(key)) return false;
  seen.add(key);
  return motionAllowed();
}
