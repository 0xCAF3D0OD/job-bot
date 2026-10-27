<script setup lang="ts">
import type { FilterChip, OfferFilters } from "../composables/useOfferFilters";
import AppIcon from "./AppIcon.vue";

// Les filtres actifs sous la barre d'outils des Offres (1.6.55) : une pastille « Nom : valeur » par
// filtre, sa croix le retire ; « Tout effacer » les retire tous. Rien sans filtre actif.
defineProps<{ chips: FilterChip[] }>();
const emit = defineEmits<{ update: [patch: Partial<OfferFilters>]; reset: [] }>();
</script>

<template>
  <div
    v-if="chips.length"
    class="offers-chips"
    data-test="filter-chips"
  >
    <ul class="offers-chips-list">
      <li
        v-for="chip in chips"
        :key="chip.key"
        class="offers-chip"
        :data-test="`chip-${chip.key}`"
      >
        <span>{{ chip.label }}</span>
        <button
          type="button"
          class="offers-chip-remove"
          :aria-label="`Retirer le filtre ${chip.label}`"
          :data-test="`chip-remove-${chip.key}`"
          @click="emit('update', chip.patch)"
        >
          <AppIcon name="close" />
        </button>
      </li>
    </ul>
    <button
      type="button"
      class="link offers-chips-clear"
      data-test="chips-reset"
      @click="emit('reset')"
    >
      Tout effacer
    </button>
  </div>
</template>
