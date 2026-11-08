<script setup lang="ts">
import { ref, watch } from "vue";

import AppIcon from "./AppIcon.vue";
import type { IconName } from "../icons";

// La recherche des offres (1.6.55) : dans la barre d'outils ; sur téléphone, au-dessus des vues de
// Candidatures (docs/139 étape 5a, C4). Appliquée 300 ms après la dernière frappe.
// `icon` : l'entonnoir de l'ordinateur (maquette du 8 novembre : « Filtrer par titre ou entreprise », la recherche
// globale étant dans l'en-tête, pas de seconde loupe).
const props = defineProps<{ value: string; placeholder?: string; icon?: IconName }>();
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
    <AppIcon :name="icon ?? 'search'" />
    <input
      v-model="search"
      class="field-compact filters-search"
      type="search"
      :aria-label="icon === 'filter' ? 'Filtrer par titre ou entreprise' : 'Rechercher une offre'"
      :placeholder="placeholder ?? 'Titre, entreprise, mot-clé…'"
      data-test="search"
    >
  </span>
</template>
