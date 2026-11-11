// La rangée d'étiquettes d'une carte tient sur une ligne (lot du 11 novembre au soir, PR 46) : si elle déborde,
// les dernières étiquettes sont retirées et une pastille « +k » dit combien. La première (« Gardée » quand
// l'offre l'est) n'est jamais retirée.

/**
 * Le nombre d'étiquettes montrées. `widths` : la largeur de chaque étiquette ; `available` : la largeur de la
 * rangée ; `gap` : l'écart entre deux étiquettes ; `plus(k)` : la largeur de la pastille « +k ».
 */
export function fitChips(widths: number[], available: number, gap: number, plus: (hidden: number) => number): number {
  const total = widths.reduce((sum, w) => sum + w, 0) + gap * Math.max(0, widths.length - 1);
  // Sans mesure (rien n'est encore à l'écran) ou quand tout tient : toutes.
  if (available <= 0 || total <= available) return widths.length;
  let used = 0;
  let shown = 0;
  for (let i = 0; i < widths.length - 1; i++) {
    const next = used + widths[i]! + gap;
    if (next + plus(widths.length - i - 1) > available) break;
    used = next;
    shown = i + 1;
  }
  return Math.max(1, shown);
}
