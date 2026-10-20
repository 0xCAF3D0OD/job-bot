<script setup lang="ts">
import { onMounted, ref } from "vue";

import { api } from "../api/client";
import type { components } from "../api/schema";

// Ce que donnent tes critères (docs/63 §2), à côté du résumé : sur les 3 derniers mois, les
// offres reçues, celles qui passent, et les raisons d'écart les plus fréquentes.
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
</script>

<template>
  <!-- Ce qu'on consulte, comme les CFF (docs/110) : le titre au-dessus, les chiffres sur fond gris. -->
  <section
    v-if="data && data.received"
    class="filter-outcome-section"
    data-test="filter-outcome"
  >
    <h2 class="section-title">
      Effet des critères
    </h2>
    <div class="info-card filter-outcome">
      <p class="muted">
        Ces 3 derniers mois
      </p>
      <p class="filter-outcome-figures">
        <strong>{{ data.retained }}</strong> offres passent sur <strong>{{ data.received }}</strong> reçues
        <span class="muted">({{ share(data.retained, data.received) }})</span>
      </p>
      <template v-if="data.reasons.length">
        <h3>Écartées surtout pour</h3>
        <ul>
          <li
            v-for="reason in data.reasons.slice(0, 3)"
            :key="reason.rule"
          >
            <span>{{ reason.label }}</span>
            <span class="bilan-track">
              <span
                class="bilan-bar"
                :style="{ width: `${Math.round((reason.count / (data.received - data.retained)) * 100)}%` }"
              />
            </span>
            <strong>{{ reason.count }}</strong>
          </li>
        </ul>
      </template>
    </div>
  </section>
</template>
