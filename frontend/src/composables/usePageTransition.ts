import { reactive, watch } from "vue";

import type { IllustrationName } from "../components/Illustration.vue";

// Les pages qui chargent des données (docs/61 §2) : à l'arrivée sur la page, si les données ne
// sont pas là après 0,15 s, l'écran se grise avec l'illustration de la page au centre ; dès
// qu'elles arrivent, le voile s'efface, après 0,5 s au moins pour ne pas clignoter.
export const PAGE_TRANSITIONS: Record<string, { illustration: IllustrationName; label: string }> = {
  today: { illustration: "morning-plans", label: "Aujourd'hui" },
  offers: { illustration: "mailbox", label: "Offres" },
  applications: { illustration: "done", label: "Suivi" },
  insights: { illustration: "stepping-up", label: "Bilan" },
  alerts: { illustration: "message-sent", label: "Alertes" },
  news: { illustration: "absorbed", label: "Actualités" },
  trainings: { illustration: "certification", label: "Formations" },
};
export const SHOW_AFTER_MS = 150;
export const SHOW_AT_LEAST_MS = 500;
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
