import { reactive, watch } from "vue";

// Les pages qui chargent des données (docs/61 §2) : à l'arrivée sur la page, si les données ne
// sont pas là après 0,15 s, l'écran se grise avec le visage du 1 au centre, l'œil et la bille
// qui pulsent (docs/123 §2, T) ; dès qu'elles arrivent, le voile s'efface, après 1,2 s au moins
// (docs/63 §3).
export const PAGE_TRANSITIONS: Record<string, { label: string }> = {
  today: { label: "Aujourd'hui" },
  offers: { label: "Offres" },
  applications: { label: "Suivi" },
  insights: { label: "Bilan" },
  alerts: { label: "Alertes" },
  news: { label: "Actualités" },
  trainings: { label: "Formations" },
};
export const SHOW_AFTER_MS = 150;
// Plus lente (docs/63 §3) : le temps de voir le visage.
export const SHOW_AT_LEAST_MS = 1200;
const GIVE_UP_MS = 8000;

export const pageTransition = reactive({ page: null as string | null, shown: false });
let ready = true;
let shownAt = 0;
const timers: ReturnType<typeof setTimeout>[] = [];

function clear(): void {
  timers.splice(0).forEach(clearTimeout);
}
function hide(): void {
  clear();
  pageTransition.shown = false;
  pageTransition.page = null;
}

// À l'arrivée sur une page (le routeur l'appelle quand le nom de la page change).
export function startPage(name: string | null): void {
  clear();
  if (!name || !(name in PAGE_TRANSITIONS)) {
    hide();
    ready = true;
    return;
  }
  ready = false;
  pageTransition.page = name;
  pageTransition.shown = false;
  timers.push(
    setTimeout(() => {
      if (ready) return;
      pageTransition.shown = true;
      shownAt = Date.now();
    }, SHOW_AFTER_MS),
    setTimeout(hide, GIVE_UP_MS),
  );
}

// La page dit que ses données sont là.
export function pageReady(name: string): void {
  if (pageTransition.page !== name || ready) return;
  ready = true;
  if (!pageTransition.shown) return hide();
  clear();
  timers.push(setTimeout(hide, Math.max(0, SHOW_AT_LEAST_MS - (Date.now() - shownAt))));
}

// Dans une page : prévient dès que ses données sont chargées.
export function usePageReady(name: string, isReady: () => boolean): void {
  watch(isReady, (now) => now && pageReady(name), { immediate: true });
}
