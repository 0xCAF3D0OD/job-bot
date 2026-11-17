<script setup lang="ts">
import { onMounted, ref } from "vue";

import { api } from "../api/client";
import type { components } from "../api/schema";
import { plural } from "../format";

// Ce que donnent tes critères (docs/63 §2), sous le résumé : sur les 3 derniers mois, les offres reçues, celles qui
// passent, et les raisons d'écart les plus fréquentes. Prompt du 10 novembre (PR 20, points 3 et 5) : des lignes au
// format de ProfilOrdinateur dans une carte blanche, plus de tuile grise ; une ligne par raison (« 95 offres pour le
// lieu »).
type Reason = components["schemas"]["FilterSummaryOut"]["reasons"][number];
const data = ref<components["schemas"]["FilterSummaryOut"] | null>(null);

onMounted(async () => {
  try {
    const { data: found } = await api.GET("/api/insights/filter");
    data.value = found ?? null;
  } catch {
    data.value = null;
  }
});

function share(part: number, total: number): string {
  return total ? `${Math.round((part / total) * 100)} %` : "—";
}

// L'article devant chaque règle du filtre (insights/service.py, REASON_LABELS).
const FOR: Record<string, string> = {
  locations: "pour le lieu",
  min_rate: "pour le taux d’activité",
  contract: "pour le type d’offre",
  language: "pour la langue",
  remote: "pour le télétravail",
  remote_region: "pour le télétravail hors de Suisse",
  banned_word: "pour un mot exclu",
};
function reasonLine(reason: Reason): string {
  return `${plural(reason.count, "offre", "offres")} ${FOR[reason.rule] ?? `pour : ${reason.label.replace(/'/g, "’")}`}`;
}
</script>

<template>
  <section
    v-if="data && data.received"
    class="filter-outcome-section"
    data-test="filter-outcome"
  >
    <h2 class="section-title">
      Effet des critères
    </h2>
    <ul class="criteria-rows filter-outcome-rows">
      <li>
        <div class="criteria-row">
          <span class="criteria-row-text">
            <span class="criteria-row-label">Ces 3 derniers mois</span>
            <span class="criteria-row-value">{{ data.retained }} offres passent sur {{ data.received }} reçues ({{ share(data.retained, data.received) }})</span>
          </span>
        </div>
      </li>
    </ul>
    <template v-if="data.reasons.length">
      <h3 class="filter-outcome-head">
        Écartées surtout pour
      </h3>
      <ul
        class="criteria-rows filter-outcome-rows"
        data-test="filter-reasons"
      >
        <li
          v-for="reason in data.reasons.slice(0, 3)"
          :key="reason.rule"
        >
          <div class="criteria-row">
            <span class="criteria-row-text">
              <span class="criteria-row-value">{{ reasonLine(reason) }}</span>
            </span>
          </div>
        </li>
      </ul>
    </template>
  </section>
</template>
