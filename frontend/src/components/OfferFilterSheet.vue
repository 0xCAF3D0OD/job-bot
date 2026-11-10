<script setup lang="ts">
import { computed } from "vue";

import type { OfferFacets } from "../api/client";
import type { OfferFilters, Sort } from "../composables/useOfferFilters";
import BottomSheet from "./BottomSheet.vue";
import GroupedList from "./GroupedList.vue";
import GroupedRow from "./GroupedRow.vue";
import SegmentedControl, { type SegmentOption } from "./SegmentedControl.vue";

// La feuille « Filtres » du téléphone (maquette Filtres, docs/139 étape 5c ; C5 validé le 2026-11-02 ;
// décisions de Kevin du 2026-11-06) : la correspondance en mots (D3), le taux minimum (un seul choix, 5e),
// le tri (C8), « Masquer les offres écartées », le télétravail. Sites et cantons se règlent dans Compte ;
// Contrat et Distance attendent le serveur (issue 468). Chaque choix s'applique tout de suite ;
// « Afficher N offres » referme. La feuille s'arrête sous les onglets (690 px sur 844 dans la maquette).
const props = defineProps<{ open: boolean; filters: OfferFilters; facets: OfferFacets; total: number }>();
const emit = defineEmits<{ update: [patch: Partial<OfferFilters>]; reset: []; close: [] }>();

// La correspondance avec les mots de la note (D3), pas en chiffres.
const SCORES: { label: string; min: number | null }[] = [
  { label: "Tous", min: null },
  { label: "À creuser et +", min: 50 },
  { label: "Proche et +", min: 75 },
  { label: "Très proche", min: 85 },
];
// Une adresse d'avant (?note=60-90) garde ses bornes, et aucun choix n'est marqué.
const scoreChoice = computed(() => (props.filters.maxScore === null ? props.filters.minScore : -1));
// Le taux minimum, un seul choix (5e) : le serveur garde une offre dont le taux maximum l'atteint, ou au
// taux inconnu. Un contrôle segmenté, pas des puces qui ont l'air de se cumuler.
const RATES: SegmentOption[] = [
  { value: "all", label: "Tous", test: "sheet-rate-all" },
  { value: "60", label: "60 %", test: "sheet-rate-60" },
  { value: "80", label: "80 %", test: "sheet-rate-80" },
  { value: "100", label: "100 %", test: "sheet-rate-100" },
];
const rate = computed({
  get: () => (props.filters.minRate === null ? "all" : String(props.filters.minRate)),
  set: (value: string) => emit("update", { minRate: value === "all" ? null : Number(value) }),
});
const SORTS: { label: string; value: Sort }[] = [
  { label: "Par jour", value: "day" },
  { label: "Note", value: "score" },
  { label: "Récentes", value: "recent" },
];

const showLabel = computed(() => (props.total <= 1 ? `Afficher ${props.total} offre` : `Afficher ${props.total} offres`));
</script>

<template>
  <BottomSheet
    :open="open"
    title="Filtres"
    class="filters-dialog"
    data-test="filters-sheet"
    @close="emit('close')"
  >
    <div class="filter-sheet">
      <div
        class="filter-choices"
        role="group"
        aria-labelledby="sheet-score-title"
      >
        <h3 id="sheet-score-title">
          Correspondance minimale
        </h3>
        <div class="filter-choices-row">
          <button
            v-for="choice in SCORES"
            :key="choice.label"
            type="button"
            class="filter-choice"
            :aria-pressed="scoreChoice === choice.min"
            :data-test="`sheet-score-${choice.min ?? 'all'}`"
            @click="emit('update', { minScore: choice.min, maxScore: null })"
          >
            {{ choice.label }}
          </button>
        </div>
      </div>

      <div class="filter-choices">
        <h3 id="sheet-rate-title">
          Taux minimum
        </h3>
        <SegmentedControl
          v-model="rate"
          :options="RATES"
          label="Taux minimum"
          full
        />
      </div>

      <div
        class="filter-choices"
        role="group"
        aria-labelledby="sheet-sort-title"
      >
        <h3 id="sheet-sort-title">
          Trier
        </h3>
        <div class="filter-choices-row">
          <button
            v-for="choice in SORTS"
            :key="choice.value"
            type="button"
            class="filter-choice"
            :aria-pressed="filters.sort === choice.value"
            :data-test="`sheet-sort-${choice.value}`"
            @click="emit('update', { sort: choice.value })"
          >
            {{ choice.label }}
          </button>
        </div>
      </div>

      <!-- Les offres écartées (Kevin, 6.11) : un interrupteur « Masquer », allumé par défaut, comme la maquette ;
           Télétravail reste. Sites et cantons se règlent dans Compte (critères de recherche, sites suivis). -->
      <GroupedList :level="3">
        <GroupedRow
          v-if="filters.view === 'pending'"
          title="Masquer les offres écartées"
          description="Éteins ce réglage pour les voir dans la liste"
          label
          data-test="sheet-filtered-out"
        >
          <template #end>
            <input
              type="checkbox"
              role="switch"
              :checked="!filters.showFilteredOut"
              @change="emit('update', { showFilteredOut: !filters.showFilteredOut })"
            >
          </template>
        </GroupedRow>
        <GroupedRow
          title="Télétravail au moins partiel"
          label
          data-test="sheet-remote"
        >
          <template #end>
            <input
              type="checkbox"
              role="switch"
              :checked="filters.remote !== null"
              @change="emit('update', { remote: filters.remote === null ? 'partial' : null })"
            >
          </template>
        </GroupedRow>
      </GroupedList>
    </div>

    <template #actions>
      <button
        type="button"
        class="link filters-clear"
        data-test="sheet-reset"
        @click="emit('reset')"
      >
        Tout effacer
      </button>
      <button
        type="button"
        class="primary filters-show"
        data-test="sheet-show"
        @click="emit('close')"
      >
        {{ showLabel }}
      </button>
    </template>
  </BottomSheet>
</template>

<style scoped>
.filters-dialog { max-height: calc(100dvh - 9.625rem); }
/* Le pied (maquette Filtres) : un trait au-dessus, « Afficher N offres » en pilule de 54 px. */
.filters-dialog :deep(.sheet-actions) { margin: 0 calc(var(--space-4) * -1); padding: var(--space-3) var(--space-5) 0; border-top: 1px solid var(--line); }
.filters-clear { min-height: var(--btn-secondary); padding: 0 var(--space-4); font-size: var(--font-body); font-weight: var(--weight-bold); }
.filters-show { min-height: 3.375rem; border-radius: var(--radius-pill); font-size: var(--font-body); font-weight: var(--weight-bold); }
</style>
