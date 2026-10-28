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
