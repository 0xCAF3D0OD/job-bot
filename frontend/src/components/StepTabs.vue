<script setup lang="ts">
// Les étapes d'une candidature (maquette Preparer, étape 7a). Sur téléphone, des onglets « dossier » (§47 du
// 17.11, planches MaCandidatureV2 et MaCandidatureCV) : chaque onglet porte un rond de 20 px avec son numéro (bleu
// plein pour l'étape ouverte, neutre sinon), ou une coche sur fond vert quand l'étape est faite. Les étapes
// partagent l'adresse (seul `?doc=` change) : seule l'étape ouverte est annoncée, par aria-current="step"
// (WCAG 4.1.2). Sur ordinateur (`numbered`, lot 15.1) : « 1. Lettre », « 2. CV », « 3. Postuler », sans rond, dans
// le contrôle segmenté de l'en-tête (la planche PreparerOrdinateur n'a pas d'onglets dossier).
import type { RouteLocationRaw } from "vue-router";

import AppIcon from "./AppIcon.vue";
import FolderTabs from "./FolderTabs.vue";

export type Step = { key: string; label: string; to: RouteLocationRaw; done?: boolean; test?: string };

defineProps<{ steps: Step[]; current: string; label: string; numbered?: boolean }>();
</script>

<template>
  <nav
    v-if="numbered"
    class="segmented step-tabs"
    :aria-label="label"
  >
    <RouterLink
      v-for="(step, index) in steps"
      :key="step.key"
      :to="step.to"
      :aria-current="current === step.key ? 'step' : undefined"
      :data-test="step.test ?? `step-${step.key}`"
    >
      <span class="segmented-label">{{ `${index + 1}. ${step.label}` }}</span><span
        v-if="step.done"
        class="visually-hidden"
        data-test="step-done"
      > (faite)</span>
    </RouterLink>
  </nav>
  <FolderTabs
    v-else
    class="step-tabs"
    :tabs="steps.map((step) => ({ value: step.key, label: step.label, to: step.to, test: step.test ?? `step-${step.key}` }))"
    :selected="current"
    :label="label"
    current="step"
  >
    <template #tab="{ tab, selected }">
      <span
        :class="['step-dot', { done: steps.find((step) => step.key === tab.value)?.done, on: selected }]"
        aria-hidden="true"
      ><AppIcon
        v-if="steps.find((step) => step.key === tab.value)?.done"
        name="check"
      /><template v-else>{{ steps.findIndex((step) => step.key === tab.value) + 1 }}</template></span>
      <span class="folder-tab-label">{{ tab.label }}</span><span
        v-if="steps.find((step) => step.key === tab.value)?.done"
        class="visually-hidden"
        data-test="step-done"
      > (faite)</span>
    </template>
  </FolderTabs>
</template>

<style>
/* Les ronds des onglets (planches MaCandidatureV2 et MaCandidatureCV, + Sombre) : 20 px, chiffre 12 px gras. */
.step-tabs { --dot-off: #DAD6CC; --dot-off-text: var(--text); }
.step-dot { display: inline-grid; place-items: center; flex: none; width: 20px; height: 20px; border-radius: var(--radius-pill); background: var(--dot-off); color: var(--dot-off-text); font-size: var(--font-caption); font-weight: var(--weight-bold); line-height: var(--leading-none); }
.step-dot.on { background: var(--action); color: var(--on-action); }
.step-dot.done { background: none; color: var(--success); --icon-on-fill: var(--on-action); }
.step-dot > .icon { width: 20px; height: 20px; }
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) .step-tabs { --dot-off: #4E473E; }
}
:root[data-theme="dark"] .step-tabs { --dot-off: #4E473E; }
/* Ordinateur : les étapes numérotées dans le contrôle segmenté. */
.segmented.step-tabs { width: fit-content; }
.segmented.step-tabs > a { flex: none; gap: var(--space-2); padding-inline: var(--space-5); font-size: var(--font-body); }
.segmented > a[aria-current="step"] {
  border-color: var(--line); background: var(--surface); color: var(--text); font-weight: var(--weight-bold);
  box-shadow: 0 1px 2px rgb(27 31 42 / 12%);
}
</style>
