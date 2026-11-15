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
// « Annuler » sur la dernière offre : le tri du jour reprend.
export function unmarkTriageDone(): void {
  try {
    localStorage.removeItem(doneKey());
  } catch {
    // Rien à défaire.
  }
}
export function triageDoneToday(): boolean {
  try {
    return localStorage.getItem(doneKey()) === "1";
  } catch {
    return false;
  }
}

// La dose du jour à partir des offres « à examiner » (notées, meilleures d'abord) : une seule règle pour Aujourd'hui,
// la page « Trier les offres » et l'assistant, pour que le compteur d'Aujourd'hui et la pile de Trier ne divergent
// jamais.
export function pickDose(today: Today | null, best: Offer[]): Offer[] {
  const behind = !!today && orpPace(today.month_count, today.month_target, today.month)?.state === "behind";
  return best.slice(0, behind ? DOSE_CATCH_UP : DOSE);
}

// Le tri à faire : une dose, pas de pause, pas déjà fait aujourd'hui. Le jour de repos ne bloque jamais le tri
// (planche AujourdhuiOrdinateurV2, état is_repos) : il change seulement le ton d'Aujourd'hui et coupe les rappels.
export function isTriagePending(today: Today | null, dose: Offer[], done: boolean): boolean {
  return !today?.rhythm?.pause_until && dose.length > 0 && !done;
}

export function useDailyDose() {
  const today = ref<Today | null>(null);
  const best = ref<Offer[]>([]);
  const loaded = ref(false);
  const dose = computed(() => pickDose(today.value, best.value));
  // Le tri à faire, comme sur Aujourd'hui (même règle, isTriagePending).
  const triagePending = computed(() => isTriagePending(today.value, dose.value, triageDoneToday()));

  async function load(): Promise<void> {
    const [day, offers] = await Promise.all([
      api.GET("/api/today"),
      api.GET("/api/offers", { params: { query: { view: "to_review", sort: "score", limit: DOSE_CATCH_UP } } }),
    ]);
    today.value = day.data ?? null;
    best.value = (offers.data?.items ?? []).filter((o) => o.score !== null && o.score !== undefined);
    loaded.value = true;
  }

  return { today, best, dose, triagePending, loaded, load };
}
