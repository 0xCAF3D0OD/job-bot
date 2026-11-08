<script setup lang="ts">
import type { RouteLocationRaw } from "vue-router";

import AppIcon from "./AppIcon.vue";

// Une ligne à flèche (D29, MODIFICATIONS du 8 novembre au soir, §2.1) : toute la ligne est le lien, un seul arrêt
// de tabulation ; le titre, le statut juste après (D31), les lignes secondaires coupées avec « … » ; à droite le
// cercle à contour, décoratif. `to` en fait un lien, sinon un bouton. `lead` : une image avant le texte.
withDefaults(
  defineProps<{ title: string; lines?: string[]; status?: { text: string; tone: "ok" | "todo" } | null; to?: RouteLocationRaw }>(),
  { lines: () => [], status: null, to: undefined },
);
defineEmits<{ click: [] }>();
</script>

<template>
  <component
    :is="to ? 'RouterLink' : 'button'"
    :to="to"
    :type="to ? undefined : 'button'"
    :class="['block-row', { small: !lines.length }]"
    @click="to ? undefined : $emit('click')"
  >
    <slot name="lead" />
    <span class="block-row-text">
      <span class="block-row-title">{{ title }}<span
        v-if="status"
        :class="['block-status', status.tone]"
      ><span class="visually-hidden">, </span>{{ status.text }}</span></span>
      <span
        v-for="line in lines"
        :key="line"
        class="block-row-line"
      ><span class="visually-hidden">, </span>{{ line }}</span>
    </span>
    <span
      class="arrow-circle"
      aria-hidden="true"
    ><AppIcon name="arrow-right" /></span>
  </component>
</template>
