// Les écouteurs du bouton retour des feuilles et panneaux de filtres (filterHistory.ts). Ce petit module est importé
// en premier par main.ts : son écouteur passe AVANT celui que createWebHistory() (router.ts) pose ensuite, car Chrome
// appelle les écouteurs de window dans l’ordre d’inscription. Le reste de filterHistory.ts se charge avec les pages.
const listeners = new Set<() => void>();
if (typeof window !== "undefined") window.addEventListener("popstate", () => [...listeners].forEach((listener) => listener()));
export function onBack(listener: () => void): void {
  listeners.add(listener);
}
export function offBack(listener: () => void): void {
  listeners.delete(listener);
}
