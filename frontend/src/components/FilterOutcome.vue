<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { api } from "../api/client";
import type { components } from "../api/schema";
import GroupedList from "./GroupedList.vue";
import GroupedRow from "./GroupedRow.vue";

// Ce que donnent tes critères (docs/63 §2), à côté du résumé : sur les 3 derniers mois, les
// offres reçues, celles qui passent, et les raisons d'écart les plus fréquentes.
// `grouped` (sous 600 px, planche « Structure téléphone ») : deux lignes d'une liste groupée.
defineProps<{ grouped?: boolean }>();
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

// « Type d'offre, lieu, taux d'activité : 1 chacune. », ou « Lieu : 4, type d'offre : 2. »
const reasonsLine = computed(() => {
  const reasons = data.value?.reasons.slice(0, 3) ?? [];
  if (!reasons.length) return "";
  const label = (text: string, index: number) =>
    index ? text.charAt(0).toLowerCase() + text.slice(1) : text.charAt(0).toUpperCase() + text.slice(1);
  const counts = new Set(reasons.map((r) => r.count));
  if (counts.size === 1) {
    const count = reasons[0]!.count;
    const each = reasons.length > 1 ? " chacune" : "";
    return `${reasons.map((r, i) => label(r.label, i)).join(", ")} : ${count}${each}.`;
  }
  return `${reasons.map((r, i) => `${label(r.label, i)} : ${r.count}`).join(", ")}.`;
});
</script>

<template>
  <GroupedList
    v-if="grouped && data && data.received"
    title="Effet des critères"
    data-test="filter-outcome"
  >
    <GroupedRow
      :title="`${data.retained} offres passent sur ${data.received}`"
      :description="`Ces 3 derniers mois, ${share(data.retained, data.received)} des offres reçues.`"
    />
    <GroupedRow
      v-if="reasonsLine"
      title="Écartées surtout pour"
      :description="reasonsLine"
    />
  </GroupedList>
  <!-- Ce qu'on consulte, comme les CFF (docs/110) : le titre au-dessus, les chiffres sur fond gris. -->
  <section
    v-else-if="data && data.received"
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
