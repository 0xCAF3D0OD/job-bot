import { computed, ref } from "vue";

import { api, type Offer, type Today } from "../api/client";
import { orpPace } from "../format";

// La dose du jour (docs/86, docs/124 §D) : les 3 meilleures offres à examiner ; 5 quand le mois ORP est
// à rattraper. Partagée par Aujourd'hui et l'écran de tri (1.6.50).
export const DOSE = 3;
export const DOSE_CATCH_UP = 5;

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
