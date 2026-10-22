<script setup lang="ts">
import { computed } from "vue";

import { usePlan } from "../composables/usePlan";

// La formule (docs/125 §4), dans Réglages › Compte : son nom, ce qu'elle limite, une ligne par
// usage (« 37 sur 150 ») avec sa jauge, quand les compteurs repartent, et ce que Plus ajoute.
// L'exploitant n'a pas de formule : la carte ne s'affiche pas.
const { plan } = usePlan();

const MONTHS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"];
const resets = computed(() => {
  const day = plan.value?.resets_on;
  if (!day) return "";
  const [, month, date] = day.split("-").map(Number);
  return `${date === 1 ? "1er" : date} ${MONTHS[month! - 1]}`;
});
const plusLimits = computed(() => plan.value?.limits.plus ?? {});

function capitalized(text: string): string {
  return text.charAt(0).toUpperCase() + text.slice(1);
}
</script>

<template>
  <div
    v-if="plan && !plan.unlimited"
    class="form-card plan-card"
    data-test="plan-panel"
  >
    <fieldset>
      <legend>Formule</legend>
      <p
        class="setting-desc"
        data-test="plan-name"
      >
        <template v-if="plan.plan === 'plus'">
          <strong>Plus</strong> : l'IA va plus loin chaque mois ; le reste n'a pas de limite.
        </template>
        <template v-else>
          <strong>Essentiel</strong>, gratuite : l'IA a des limites chaque mois ; le reste n'en a pas.
        </template>
      </p>
      <ul
        class="plan-usage"
        data-test="plan-usage"
      >
        <li
          v-for="usage in plan.usage"
          :key="usage.key"
          :data-test="`plan-${usage.key}`"
        >
          <span class="plan-usage-name">{{ capitalized(usage.label) }}</span>
          <span class="plan-usage-count">{{ usage.used }} sur {{ usage.limit }}</span>
          <span
            class="plan-usage-gauge"
            :style="{ '--p': Math.min(100, Math.round((usage.used / (usage.limit || 1)) * 100)) }"
            aria-hidden="true"
          />
        </li>
      </ul>
      <p
        class="hint plan-resets"
        data-test="plan-resets"
      >
        Les compteurs repartent le {{ resets }}.
      </p>
      <p
        v-if="plan.plan !== 'plus'"
        class="setting-info plan-plus"
        data-test="plan-plus"
      >
        <strong>Plus · {{ plan.plus_price_chf }} CHF par mois</strong> :
        {{ plusLimits.letter }} lettres, {{ plusLimits.cv }} CV, {{ plusLimits.practice }} entraînements, {{ plusLimits.score }} offres notées. Le paiement arrive bientôt.
      </p>
    </fieldset>
  </div>
</template>
