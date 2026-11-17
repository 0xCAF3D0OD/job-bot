// À part de useOfferFilters : Envoyées (suivi) s'en sert sans charger les filtres des Offres ni leurs traductions.
/** Les flèches d'un groupe de boutons radio : le choix suit le focus (WAI-ARIA, radiogroup). */
export function radioKey(event: KeyboardEvent): void {
  const step = ["ArrowRight", "ArrowDown"].includes(event.key) ? 1 : ["ArrowLeft", "ArrowUp"].includes(event.key) ? -1 : 0;
  if (!step) return;
  const radios = Array.from((event.currentTarget as HTMLElement).querySelectorAll<HTMLElement>("[role=radio]"));
  const next = radios[(radios.indexOf(event.target as HTMLElement) + step + radios.length) % radios.length];
  if (!next) return;
  event.preventDefault();
  next.focus();
  next.click();
}
