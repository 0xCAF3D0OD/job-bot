<script setup lang="ts">
import type { RouteLocationRaw } from "vue-router";

import CountBadge from "./CountBadge.vue";

// Le contrôle segmenté (règles §4 « Sélection unique », D4 tranchée le 2026-11-03) : 2 à 5 choix courts, le
// segment choisi en carte sur un rail gris ; il dit où je suis (une puce teintée dit ce que j'ai filtré). Avec `to`,
// chaque segment est un lien (les vues d'une même page, comme Critères, Parcours, Coordonnées du
// Profil) et le segment actif porte aria-current ; sinon, un groupe de radios (aria-checked).
// `full` : les segments se partagent toute la largeur (2 ou 3 choix sur téléphone). Un libellé n'est
// jamais coupé : le test téléphone de la CI le vérifie en 320 px (.segmented-label). `count` : une pastille de
// nombre après le libellé (Candidatures sur ordinateur), absente à zéro. `name` : le nom accessible complet quand le
// libellé visible est une abréviation (FR → « Français »).
export type SegmentOption = { value: string; label: string; to?: RouteLocationRaw; test?: string; count?: number; hint?: string; name?: string };
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
      :aria-label="option.name"
      :data-test="option.test ?? `segment-${option.value}`"
    >
      <span class="segmented-label">{{ option.label }}</span>{{ option.count ? " " : "" }}<CountBadge
        v-if="option.count"
        class="tab-count"
        :title="option.hint"
        :count="option.count"
      />
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
      :aria-label="option.name"
      :data-test="option.test ?? `segment-${option.value}`"
      @click="model = option.value"
    >
      <span class="segmented-label">{{ option.label }}</span>{{ option.count ? " " : "" }}<CountBadge
        v-if="option.count"
        class="tab-count"
        :title="option.hint"
        :count="option.count"
      />
    </button>
  </div>
</template>
