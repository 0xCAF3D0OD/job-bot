// L'objectif ORP du mois atteint (docs/123 §2, B10) : une fête, une fois par mois et par appareil.
// L'Accueil (la carte « Objectif du mois atteint ») et « J'ai postulé » (l'écran « C'est fait ! »)
// partagent la même clé : le premier qui la voit la prend, l'autre ne la montre plus.
const key = (month: string) => `jobA1.orp-goal.${month}`;

export function firstGoal(month: string, count: number, target: number | null | undefined): boolean {
  if (!target || count < target) return false;
  try {
    if (localStorage.getItem(key(month))) return false;
    localStorage.setItem(key(month), "1");
    return true;
  } catch {
    return false;
  }
}

// « Je n'ai pas postulé » sur « C'est fait ! » : l'objectif n'est plus atteint, la fête reviendra.
export function forgetGoal(month: string): void {
  try {
    localStorage.removeItem(key(month));
  } catch {
    // Rien à faire : sans stockage, la fête n'était pas retenue.
  }
}
