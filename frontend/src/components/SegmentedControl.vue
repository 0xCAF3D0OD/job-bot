<script setup lang="ts">
import type { RouteLocationRaw } from "vue-router";

// Le contrôle segmenté (règles §4, planche « Structure téléphone ») : 2 à 5 choix courts. Avec `to`,
// chaque segment est un lien (les vues d'une même page, comme Critères, Parcours, Coordonnées du
// Profil) et le segment actif porte aria-current ; sinon, un groupe de radios (aria-checked).
// `full` : les segments se partagent toute la largeur (2 ou 3 choix sur téléphone). Un libellé n'est
// jamais coupé : le test téléphone de la CI le vérifie en 320 px (.segmented-label).
export type SegmentOption = { value: string; label: string; to?: RouteLocationRaw; test?: string };
const props = withDefaults(defineProps<{ options: SegmentOption[]; label: string; full?: boolean }>(), { full: false });
const model = defineModel<string>({ required: true });
const asLinks = props.options.some((option) => option.to);
</script>

<template>
  <nav
    v-if="asLinks"
    :class="['segmented', { 'segmented-full': full }]"
    :aria-label="label"
  >
    <RouterLink
      v-for="option in options"
      :key="option.value"
      :to="option.to!"
      :aria-current="model === option.value ? 'page' : undefined"
      :data-test="option.test ?? `segment-${option.value}`"
    >
      <span class="segmented-label">{{ option.label }}</span>
    </RouterLink>
  </nav>
  <div
    v-else
    :class="['segmented', { 'segmented-full': full }]"
    role="radiogroup"
    :aria-label="label"
  >
    <button
      v-for="option in options"
      :key="option.value"
      type="button"
      role="radio"
      :aria-checked="model === option.value"
      :data-test="option.test ?? `segment-${option.value}`"
      @click="model = option.value"
    >
      <span class="segmented-label">{{ option.label }}</span>
    </button>
  </div>
</template>
