<script setup lang="ts">
import { computed } from "vue";

import { type PlanKey, usePlan } from "../composables/usePlan";

// À la limite de la formule (docs/125 §4) : une ligne grise sous l'action, qui dit ce qui est
// épuisé et quand ça revient, et mène à la formule. Une fois par écran, jamais en bandeau.
const props = defineProps<{ usage: PlanKey }>();
const { plan, reached } = usePlan();
// Les offres continuent d'arriver : seule leur note attend.
const text = computed(() => {
  const limit = plan.value?.usage.find((u) => u.key === props.usage)?.limit_text ?? "";
  return limit && props.usage === "score" ? `${limit} Les nouvelles offres arrivent sans note jusque-là.` : limit;
});
</script>

<template>
  <p
    v-if="reached(usage) && text"
    class="hint plan-limit"
    :data-test="`plan-limit-${usage}`"
  >
    {{ text }} <RouterLink to="/reglages?rubrique=compte">
      Voir la formule
    </RouterLink>
  </p>
</template>
