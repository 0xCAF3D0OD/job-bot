<script setup lang="ts">
import { computed } from "vue";

import type { components } from "../../api/schema";
import { funnelText, STEPS, weakStep } from "../../bilanText";

// La carte Parcours (maquette Explorer, onglet Bilan ; B13, 8d) : une barre par étape, à l'échelle des offres
// reçues, puis l'encadré orange « Le plus de pertes ». Les cinq étapes de la maquette ; « Postes obtenus »
// s'ajoute dès le premier.
const props = defineProps<{ funnel: components["schemas"]["FunnelOut"] }>();
const LABELS: Record<string, string> = {
  received: "Offres reçues",
  retained: "Gardées",
  applications: "Candidatures",
  responses: "Réponses",
  interviews: "Entretiens",
  engagements: "Postes obtenus",
};
const weak = computed(() => weakStep(props.funnel));
const rows = computed(() => {
  const f = props.funnel;
  const steps = STEPS.filter((s) => s.key !== "engagements" || f.engagements > 0);
  const top = Math.max(1, ...steps.map((s) => f[s.key]));
  return steps.map((s) => ({
    key: s.key,
    label: LABELS[s.key]!,
    count: f[s.key],
    width: f[s.key] ? `${Math.max((f[s.key] / top) * 100, 3)}%` : "0",
  }));
});
</script>

<template>
  <section
    class="bilan-funnel"
    aria-labelledby="bilan-funnel-title"
    data-test="funnel"
  >
    <h2 id="bilan-funnel-title">
      Parcours
    </h2>
    <!-- Le texte pour les lecteurs d'écran (WCAG 1.1.1) ; les barres sont un dessin. -->
    <p class="visually-hidden">
      {{ funnelText(funnel) }}
    </p>
    <ul aria-hidden="true">
      <li
        v-for="row in rows"
        :key="row.key"
        :data-test="`funnel-${row.key}`"
      >
        <span>{{ row.label }}</span>
        <span class="bilan-funnel-track"><span :style="{ width: row.width }" /></span>
        <strong>{{ row.count }}</strong>
      </li>
    </ul>
    <p
      v-if="weak"
      class="bilan-funnel-loss"
      data-test="funnel-work"
    >
      <strong>Le plus de pertes :</strong> {{ weak.between }}. À travailler : {{ weak.work }}.
    </p>
  </section>
</template>
