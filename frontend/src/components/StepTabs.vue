<script setup lang="ts">
// Les étapes d'une candidature (maquette Preparer, étape 7a) : le contrôle segmenté de D4, un segment
// par étape. Le segment en relief dit l'étape ouverte ; chaque segment porte une pastille teintée
// (--primary-soft) avec son numéro, ou une coche verte quand l'étape est faite. Pas de rond plein :
// D4 le réserve à la barre du bas. Les étapes partagent l'adresse (seul `?doc=` change) : seule
// l'étape ouverte est annoncée, par aria-current="step" (WCAG 4.1.2).
import type { RouteLocationRaw } from "vue-router";

import AppIcon from "./AppIcon.vue";

export type Step = { key: string; label: string; to: RouteLocationRaw; done?: boolean; test?: string };

defineProps<{ steps: Step[]; current: string; label: string }>();
</script>

<template>
  <nav
    class="segmented segmented-full step-tabs"
    :aria-label="label"
  >
    <RouterLink
      v-for="(step, index) in steps"
      :key="step.key"
      :to="step.to"
      :aria-current="current === step.key ? 'step' : undefined"
      :data-test="step.test ?? `step-${step.key}`"
    >
      <span
        :class="['step-dot', { done: step.done }]"
        aria-hidden="true"
      ><AppIcon
        v-if="step.done"
        name="check"
      /><template v-else>{{ index + 1 }}</template></span>
      <span class="segmented-label">{{ step.label }}</span><span
        v-if="step.done"
        class="visually-hidden"
        data-test="step-done"
      > (faite)</span>
    </RouterLink>
  </nav>
</template>
