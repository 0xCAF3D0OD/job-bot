<script setup lang="ts">
import { computed } from "vue";

import type { components } from "../../api/schema";
import { funnelText, STEPS, weakStep, word } from "../../bilanText";

// « Parcours » déplié (1.6.62) : les six étapes chiffrées en ligne, l'étape faible en accent, et ce
// qu'il faut travailler. Sur téléphone, une grille de trois, sans flèches.
const props = defineProps<{ funnel: components["schemas"]["FunnelOut"] }>();
const weak = computed(() => weakStep(props.funnel));
</script>

<template>
  <div
    class="bilan-steps-card"
    data-test="funnel"
  >
    <!-- Le texte pour les lecteurs d'écran (WCAG 1.1.1) ; la rangée est un dessin. -->
    <p class="visually-hidden">
      {{ funnelText(funnel) }}
    </p>
    <ol
      class="bilan-steps"
      aria-hidden="true"
    >
      <li
        v-for="step in STEPS"
        :key="step.key"
        :class="{ weak: weak?.key === step.key }"
        :data-test="`funnel-${step.key}`"
      >
        <strong>{{ funnel[step.key] }}</strong>
        <span>{{ word(funnel[step.key], step.one, step.many) }}</span>
      </li>
    </ol>
    <p
      v-if="weak"
      class="bilan-steps-work"
      data-test="funnel-work"
    >
      C'est l'étape à travailler : {{ weak.work }}.
    </p>
  </div>
</template>
