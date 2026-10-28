<script setup lang="ts">
import type { RouteLocationRaw } from "vue-router";

// La tête de carte commune (règles §4) : « Titre · nombre » à gauche ; à droite, le lien « Tout voir »
// qui mène à la page, ou une action (« + Ajouter ») suivie de « ⋯ », toujours en dernier (slot).
// Inspiré des en-têtes de carte de Polaris (titre, puis actions alignées à droite).
withDefaults(
  defineProps<{ title: string; count?: number; to?: RouteLocationRaw; linkLabel?: string; level?: 2 | 3 }>(),
  { count: undefined, to: undefined, linkLabel: "Tout voir", level: 2 },
);
</script>

<template>
  <header class="card-head">
    <component
      :is="`h${level}`"
      class="card-head-title"
    >
      {{ title }}<span
        v-if="count !== undefined"
        class="card-head-count"
      > · {{ count }}</span>
    </component>
    <div
      v-if="to || $slots.default"
      class="card-head-actions"
    >
      <RouterLink
        v-if="to"
        :to="to"
        class="link"
        data-test="card-all"
      >
        {{ linkLabel }}
      </RouterLink>
      <slot />
    </div>
  </header>
</template>
