<script setup lang="ts">
import AppIcon from "./AppIcon.vue";

// Ce qui se déplie sur place, en bas d'une carte : « Afficher plus (4) », puis « Afficher moins »
// (règles §4). « Tout voir » est réservé au lien qui mène à la page. Inspiré du « Show more » de
// GOV.UK et de Polaris.
defineProps<{ hidden: number; testId?: string }>();
const open = defineModel<boolean>({ default: false });
</script>

<template>
  <button
    type="button"
    class="link show-more"
    :aria-expanded="open"
    :data-test="testId ?? 'show-more'"
    @click="open = !open"
  >
    <span class="with-icon"><AppIcon name="chevron-down" />{{ open ? "Afficher moins" : `Afficher plus (${hidden})` }}</span>
  </button>
</template>
