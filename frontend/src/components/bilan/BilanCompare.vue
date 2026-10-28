<script setup lang="ts">
import { computed } from "vue";

import type { components } from "../../api/schema";
import { COMPARE_TITLES, groupLabel } from "../../bilanText";

// « Ce qui marche » déplié (1.6.62) : des barres de taux par site, avec un contact, après une relance.
// Un groupe sans assez de données n'a pas de barre : une ligne en gris, le chiffre écrit (WCAG 1.4.1).
const props = defineProps<{ comparisons: components["schemas"]["ComparisonOut"][] }>();
const parts = computed(() =>
  Object.keys(COMPARE_TITLES)
    .map((key) => props.comparisons.find((c) => c.key === key))
    .filter((c): c is components["schemas"]["ComparisonOut"] => !!c && c.groups.length > 0),
);
function width(responses: number, total: number): string {
  return `${total ? Math.max(responses ? 3 : 0, (responses / total) * 100) : 0}%`;
}
</script>

<template>
  <div
    class="bilan-compare"
    data-test="bilan-compare"
  >
    <section
      v-for="comparison in parts"
      :key="comparison.key"
      class="bilan-compare-part"
      :data-test="`comparison-${comparison.key}`"
    >
      <h3 class="bilan-subtitle">
        {{ COMPARE_TITLES[comparison.key] }}
      </h3>
      <ul class="bilan-rates">
        <template
          v-for="group in comparison.groups"
          :key="group.key"
        >
          <li
            v-if="group.enough"
            class="bilan-rate"
            :data-test="`group-${group.key}`"
          >
            <span class="bilan-rate-label">{{ groupLabel(comparison.key, group) }}</span>
            <span
              class="bilan-track"
              aria-hidden="true"
            ><span
              class="bilan-bar"
              :style="{ width: width(group.responses, group.total) }"
            /></span>
            <strong class="bilan-rate-count">{{ group.responses }} sur {{ group.total }}</strong>
          </li>
          <li
            v-else
            class="bilan-rate-few"
            :data-test="`group-${group.key}`"
          >
            {{ groupLabel(comparison.key, group) }} : trop peu pour conclure ({{ group.responses }} sur {{ group.total }})
          </li>
        </template>
      </ul>
    </section>
    <p
      v-if="!parts.length"
      class="hint"
    >
      Aucune comparaison pour l'instant.
    </p>
  </div>
</template>
