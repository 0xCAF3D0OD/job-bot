<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { api } from "../api/client";
import type { components } from "../api/schema";
import { formatMonth } from "../format";

// À côté du plafond de l'IA (docs/63 §2) : la dépense du mois, celle qu'affiche le Diagnostic.
const status = ref<components["schemas"]["ScoringStatus"] | null>(null);
onMounted(async () => {
  try {
    const { data } = await api.GET("/api/scoring");
    status.value = data ?? null;
  } catch {
    status.value = null;
  }
});
const month = (() => {
  const now = new Date();
  return formatMonth(`${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`).split(" ")[0];
})();
const spent = computed(() => Number(status.value?.month_spend_chf ?? 0));
const budget = computed(() => Number(status.value?.budget_chf ?? 0));
const share = computed(() => (budget.value > 0 ? Math.min(1, spent.value / budget.value) : 0));
const chf = (n: number): string => n.toFixed(2).replace(".", ",");
</script>

<template>
  <section
    v-if="status"
    class="ai-spend"
    data-test="ai-spend"
  >
    <h3>{{ month }}</h3>
    <p class="ai-spend-figures">
      <strong>{{ chf(spent) }} CHF</strong> <span class="muted">sur {{ chf(budget) }}</span>
    </p>
    <span class="bilan-track">
      <span
        class="bilan-bar"
        :class="{ reached: status.budget_reached }"
        :style="{ width: `${Math.round(share * 100)}%` }"
      />
    </span>
    <p
      v-if="status.platform_budget_reached"
      class="notice"
      data-test="platform-reached"
    >
      Le plafond de la plateforme est atteint : l'IA reprend le mois prochain.
    </p>
    <p class="muted">
      {{ status.configured ? `IA configurée · ${status.model}` : "IA non configurée (réglage d'installation)" }}
    </p>
  </section>
</template>
