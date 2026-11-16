<script setup lang="ts">
import { ref, watch } from "vue";

import AppIcon from "./AppIcon.vue";
import type { IconName } from "../icons";

// La recherche des offres (1.6.55) : dans la barre d'outils ; sur téléphone, au-dessus des vues de
// Candidatures (docs/139 étape 5a, C4). Appliquée 300 ms après la dernière frappe.
// `icon` : l'entonnoir de l'ordinateur (maquette du 8 novembre : « Filtrer par titre ou entreprise », la recherche
// globale étant dans l'en-tête, pas de seconde loupe).
// `label` : le nom lu par les lecteurs d'écran, quand le texte visible est le même partout (« Poste, entreprise, lieu ») :
// « Rechercher une candidature », « Rechercher un rendez-vous » (décision de Kevin du 14.11).
const props = defineProps<{ value: string; placeholder?: string; icon?: IconName; label?: string }>();
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
      :aria-label="label ?? (icon === 'filter' ? 'Filtrer par titre ou entreprise' : 'Rechercher une offre')"
      :placeholder="placeholder ?? 'Titre, entreprise, mot-clé…'"
      data-test="search"
    >
  </span>
</template>

<style>
/* Sorti de style.css (allègement du 16.11, issue #797) : ces règles ne servent qu'ici, chargées avec ce composant. */
@media (min-width: 1024px) {
.offers-list-tools .offers-toolbar .filters-search:focus { border-color: var(--field-border); box-shadow: none; outline: 2px solid var(--primary-graphic); outline-offset: 1px; }
}
/* Téléphone, maquette du 14 novembre (§6, planches Candidatures, Envoyees, RendezVous) : le champ « Poste, entreprise, lieu »
   au-dessus des onglets : 48 px, coins de 14, bord --line, fond blanc, loupe de 20 à 14 px, 16 px à droite (grille de 4). */
@media (max-width: 820px) {
  .jobs-tools .filters-search-wrap { --search-14: 14px; --search-icon: 20px; --search-gap: 10px; display: block; }
  .jobs-tools .filters-search-wrap .filters-search { box-sizing: border-box; height: var(--field-h); padding: 0 var(--space-4) 0 calc(var(--search-14) + var(--search-icon) + var(--search-gap)); border: 1px solid var(--line); border-radius: var(--search-14); background-color: var(--surface); font-size: var(--font-body); }
  .jobs-tools .filters-search-wrap > .icon { left: var(--search-14); width: var(--search-icon); height: var(--search-icon); color: var(--text-secondary); }
}
</style>
