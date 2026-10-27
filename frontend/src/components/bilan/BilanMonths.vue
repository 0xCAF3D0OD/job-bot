<script setup lang="ts">
import { computed } from "vue";

import type { components } from "../../api/schema";
import { monthShort, monthsText } from "../../bilanText";

// « Par mois » déplié (1.6.62) : une colonne par mois depuis la première activité, la ligne pointillée
// de l'objectif ; le mois en cours en clair, contour pointillé, « 7 / 10 » et « oct. · en cours » :
// le mot, pas seulement la couleur (WCAG 1.4.1).
const props = defineProps<{ months: components["schemas"]["MonthCountOut"][]; target?: number | null }>();
const top = computed(() => Math.max(1, props.target ?? 0, ...props.months.map((m) => m.count)));
function height(n: number): string {
  return `${(n / top.value) * 100}%`;
}
</script>

<template>
  <div
    class="bilan-months"
    data-test="bilan-months"
  >
    <p class="visually-hidden">
      {{ monthsText(months, target) }}
    </p>
    <div
      class="bilan-months-plot"
      aria-hidden="true"
    >
      <span
        v-if="target"
        class="bilan-goal"
        :style="{ bottom: height(target) }"
      ><span>Objectif : {{ target }}</span></span>
      <div
        v-for="(m, i) in months"
        :key="m.month"
        :class="['bilan-month', { current: i === months.length - 1 }]"
        :data-test="`month-${m.month}`"
      >
        <div class="bilan-month-area">
          <div
            class="bilan-month-bar"
            :style="{ height: height(m.count) }"
          >
            <strong class="bilan-month-value">{{ i === months.length - 1 && target ? `${m.count} / ${target}` : m.count }}</strong>
          </div>
        </div>
        <span class="bilan-month-label">{{ monthShort(m.month) }}<template v-if="i === months.length - 1"> · en cours</template></span>
      </div>
    </div>
  </div>
</template>
