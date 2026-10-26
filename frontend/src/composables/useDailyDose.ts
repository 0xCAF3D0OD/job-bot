import { computed, ref } from "vue";

import { api, type Offer, type Today } from "../api/client";
import { dayKey, orpPace } from "../format";

// La dose du jour (docs/86, docs/124 §D) : les 3 meilleures offres à examiner ; 5 quand le mois ORP est
// à rattraper. Partagée par Aujourd'hui et l'écran de tri (1.6.50).
export const DOSE = 3;
export const DOSE_CATCH_UP = 5;

// Le tri du jour terminé (1.6.51) : l'écran de tri le note à la fin de la pile, sur cet appareil
// (comme l'objectif du mois atteint). Aujourd'hui montre alors « Tri terminé · À demain ».
function doneKey(now: Date = new Date()): string {
  return `jobA1.tri.${dayKey(now.toISOString())}`;
}
export function markTriageDone(): void {
  try {
    localStorage.setItem(doneKey(), "1");
  } catch {
    // Stockage refusé : Aujourd'hui reproposera le tri, sans gêne.
  }
}
export function triageDoneToday(): boolean {
  try {
    return localStorage.getItem(doneKey()) === "1";
  } catch {
    return false;
  }
}

export function useDailyDose() {
  const today = ref<Today | null>(null);
  const best = ref<Offer[]>([]);
  const loaded = ref(false);
  // Un jour de repos (docs/86) : aucune liste à traiter.
  const restDay = computed(() => today.value?.rhythm?.research_today === false);
  const dose = computed(() => {
    const t = today.value;
    const behind = !!t && orpPace(t.month_count, t.month_target, t.month)?.state === "behind";
    return best.value.slice(0, behind ? DOSE_CATCH_UP : DOSE);
  });

  async function load(): Promise<void> {
    const [day, offers] = await Promise.all([
      api.GET("/api/today"),
      api.GET("/api/offers", { params: { query: { view: "to_review", sort: "score", limit: DOSE_CATCH_UP } } }),
    ]);
    today.value = day.data ?? null;
    best.value = (offers.data?.items ?? []).filter((o) => o.score !== null && o.score !== undefined);
    loaded.value = true;
  }

  return { today, best, dose, restDay, loaded, load };
}
