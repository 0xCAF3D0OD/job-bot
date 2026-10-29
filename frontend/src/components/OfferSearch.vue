<script setup lang="ts">
import { ref, watch } from "vue";

import AppIcon from "./AppIcon.vue";

// La recherche des offres (1.6.55) : dans la barre d'outils sur ordinateur, en tête de la feuille
// « Filtres » sur téléphone. Appliquée 300 ms après la dernière frappe.
const props = defineProps<{ value: string }>();
const emit = defineEmits<{ search: [value: string] }>();

const search = ref(props.value);
let timer: ReturnType<typeof setTimeout> | undefined;
watch(search, (value) => {
  clearTimeout(timer);
  timer = setTimeout(() => emit("search", value), 300);
});
watch(
  () => props.value,
  (value) => {
    if (value !== search.value.trim()) search.value = value;
  },
);
</script>

<template>
  <!-- Loupe devant, libellé lu par les lecteurs d'écran (docs/29 §5). -->
  <span class="filters-search-wrap">
    <AppIcon name="search" />
    <input
      v-model="search"
      class="field-compact filters-search"
      type="search"
      aria-label="Recherche"
      placeholder="Titre, entreprise, mot-clé…"
      data-test="search"
    >
  </span>
</template>
