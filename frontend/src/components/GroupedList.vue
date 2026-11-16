<script setup lang="ts">
import { useId } from "vue";

import CountBadge from "./CountBadge.vue";

// Une liste groupée (règles §4, Apple HIG « inset grouped ») : le titre de section hors de la carte,
// avec son compteur à droite, puis une carte dont les lignes (GroupedRow) sont séparées par un filet.
withDefaults(defineProps<{ title?: string; count?: number; level?: 2 | 3 }>(), { title: "", count: undefined, level: 2 });
const titleId = useId();
</script>

<template>
  <section
    class="grouped"
    :aria-labelledby="title ? titleId : undefined"
  >
    <component
      :is="`h${level}`"
      v-if="title"
      :id="titleId"
      class="grouped-title"
    >
      {{ title }}<CountBadge
        v-if="count !== undefined"
        :count="count"
        class="grouped-count"
      />
    </component>
    <ul class="grouped-card">
      <slot />
    </ul>
  </section>
</template>

<style>
/* Sorti de style.css (allègement du 16.11, issue #797) : ces règles ne servent qu'ici, chargées avec ce composant. */
.grouped-title { display: flex; align-items: center; gap: var(--space-2); margin: 0; padding-inline: var(--space-1); font-size: var(--font-small); font-weight: var(--weight-semibold); color: var(--muted); }
.grouped-card { list-style: none; margin: 0; padding: 0; overflow: hidden; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); }
</style>
