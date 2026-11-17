<script setup lang="ts">
import { computed } from "vue";

import { SENT_FILTERS, type SentFilter, type SentSort } from "../sentFilters";
import { useFilterEntry } from "../filterHistory";
import AppIcon from "./AppIcon.vue";
import "../filterPanel.css";

// Le volet « Filtres » des Envoyées sur ordinateur (maquette du 14 novembre, §3 et §6 ; décision de Kevin du 14.11) :
// le même volet que les Offres, à la place de la colonne liste. Les statuts (avec leur nombre) et le tri y passent :
// « À relancer d’abord » (par défaut), « Plus récentes d’abord », et « Plus anciennes d’abord », gardé de main.
const props = defineProps<{ filter: SentFilter; sort: SentSort; counts: Record<SentFilter, number>; total: number }>();
const emit = defineEmits<{ "update:filter": [value: SentFilter]; "update:sort": [value: SentSort]; reset: []; close: [] }>();
// Une entrée d’historique par application ; retour pendant l’ouverture ferme sans appliquer (Kevin, 17.11).
useFilterEntry(() => emit("close"));

const SORTS: { value: SentSort; label: string }[] = [
  { value: "relancer", label: "À relancer d’abord" },
  { value: "recentes", label: "Plus récentes d’abord" },
  { value: "anciennes", label: "Plus anciennes d’abord" },
];
// Un statut à 0 est masqué, sauf celui qui est choisi (pour pouvoir le quitter).
const shown = computed(() => SENT_FILTERS.filter((f) => f.value === "toutes" || props.counts[f.value] > 0 || f.value === props.filter));
const showLabel = computed(() => `Afficher ${props.total} ${props.total > 1 ? "candidatures" : "candidature"}`);
</script>

<template>
  <section
    id="sent-filters-panel"
    class="filter-panel sent-filter-panel"
    aria-labelledby="sent-filters-title"
    data-test="sent-filters-panel"
  >
    <div class="filter-panel-head">
      <button
        type="button"
        class="link filter-panel-back"
        data-test="sent-filters-close"
        @click="emit('close')"
      >
        <AppIcon name="chevron-left" />Retour à la liste
      </button>
      <h2
        id="sent-filters-title"
        tabindex="-1"
      >
        Filtres
      </h2>
    </div>
    <div class="filter-panel-body">
      <div
        class="filter-panel-group"
        role="group"
        aria-labelledby="sent-pop-status"
      >
        <span id="sent-pop-status">Statut</span>
        <div>
          <button
            v-for="choice in shown"
            :key="choice.value"
            type="button"
            :aria-pressed="filter === choice.value"
            :data-test="`sent-status-${choice.value}`"
            @click="emit('update:filter', choice.value)"
          >
            {{ choice.label }} · {{ counts[choice.value] }}
          </button>
        </div>
      </div>
      <hr>
      <div
        class="filter-panel-group"
        role="group"
        aria-labelledby="sent-pop-sort"
      >
        <span id="sent-pop-sort">Trier</span>
        <div>
          <button
            v-for="choice in SORTS"
            :key="choice.value"
            type="button"
            :aria-pressed="sort === choice.value"
            :data-test="`sent-sort-${choice.value}`"
            @click="emit('update:sort', choice.value)"
          >
            {{ choice.label }}
          </button>
        </div>
      </div>
    </div>
    <div class="filter-panel-foot">
      <button
        type="button"
        class="link"
        data-test="sent-filters-reset"
        @click="emit('reset')"
      >
        Tout effacer
      </button>
      <button
        type="button"
        class="primary"
        data-test="sent-filters-done"
        @click="emit('close')"
      >
        {{ showLabel }}
      </button>
    </div>
  </section>
</template>

<style>
/* Sorti de style.css (allègement du 16.11, issue #797) : ces règles ne servent qu'ici, chargées avec ce composant. */
@media (min-width: 1024px) {
.sent-columns > .sent-filter-panel { position: sticky; top: var(--space-4); height: auto; max-height: calc(100dvh - 12rem); }
}
</style>
