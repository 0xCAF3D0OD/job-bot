import { computed, ref, watch, type Ref } from "vue";

import { api, type Offer } from "../api/client";
import { offerUndo } from "./useUndo";

// Le tri des offres du jour, une par une (lot du 11 novembre au soir, PR 45 et 49) : la page « Trier les offres » et le
// petit livre d'Aujourd'hui sur ordinateur trient de la même façon. La pile ne change pas pendant le tri ; « Garder »
// passe l'offre à l'état « Gardée » (`later`, décision de Kevin du 11 novembre), « Écarter » à `ignored` ; rien ne
// part au serveur avant la fin des 6 secondes d'« Annuler ».
export type TriageChoice = "keep" | "dismiss";

export function useTriage(dose: Ref<Offer[]>, moved: () => void = () => {}) {
  const queue = ref<Offer[]>([]);
  const index = ref(0);
  const choices = ref<TriageChoice[]>([]);
  watch(
    () => dose.value.map((o) => o.id).join(","),
    () => {
      if (index.value === 0) queue.value = [...dose.value];
    },
    { immediate: true },
  );
  const total = computed(() => queue.value.length);
  const current = computed(() => queue.value[index.value] ?? null);
  const remaining = computed(() => Math.max(0, total.value - index.value - 1));
  const finished = computed(() => total.value > 0 && index.value >= total.value);
  const kept = computed(() => queue.value.filter((_, i) => choices.value[i] === "keep"));
  const dismissed = computed(() => choices.value.filter((c) => c === "dismiss").length);

  function decide(choice: TriageChoice): void {
    const offer = current.value;
    if (!offer) return;
    const at = index.value;
    choices.value[at] = choice;
    index.value = at + 1;
    moved();
    void offerUndo({
      message: choice === "keep" ? "Offre gardée dans tes candidatures" : "Offre écartée",
      commit: async (keepalive) => {
        const { response } = await api.PATCH("/api/offers/{offer_id}/status", {
          params: { path: { offer_id: offer.id } },
          body: { status: choice === "keep" ? "later" : "ignored" },
          keepalive,
        });
        return response.ok;
      },
      restore: () => {
        choices.value.length = at;
        index.value = at;
        moved();
      },
    });
  }

  return { queue, index, total, current, remaining, finished, kept, dismissed, decide };
}
