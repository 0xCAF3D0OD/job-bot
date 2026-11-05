<script setup lang="ts">
import { computed } from "vue";

import type { OfferFacets, Source } from "../api/client";
import { sourceLabel } from "../format";
import type { OfferFilters, Sort } from "../composables/useOfferFilters";
import BottomSheet from "./BottomSheet.vue";
import GroupedList from "./GroupedList.vue";
import GroupedRow from "./GroupedRow.vue";
import SegmentedControl, { type SegmentOption } from "./SegmentedControl.vue";

// La feuille « Filtres » du téléphone (maquette Filtres, docs/139 étape 5c ; C5 validé le 2026-11-02) :
// la correspondance en mots (D3), le taux minimum (un seul choix, 5e), le tri (C8), « Afficher aussi »
// (Écartées, Expirées : 5e, à la place de la vue « Toutes ») ; puis les filtres d'avant (télétravail,
// employeur, offres à vérifier, sites, cantons). Contrat et Distance attendent le
// serveur (issue 468). Chaque choix s'applique tout de suite ; « Afficher N offres » referme.
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

function toggle<T extends string>(values: T[], value: T): T[] {
  return values.includes(value) ? values.filter((v) => v !== value) : [...values, value];
}
const showLabel = computed(() => (props.total === 1 ? "Afficher 1 offre" : `Afficher ${props.total} offres`));
</script>

<template>
  <BottomSheet
    :open="open"
    title="Filtres"
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

      <!-- « Afficher aussi » (5e) : les deux allumés, c'est l'ancienne vue « Toutes ». -->
      <GroupedList
        v-if="filters.view === 'pending'"
        :level="3"
        title="Afficher aussi"
        data-test="sheet-show-also"
      >
        <GroupedRow
          title="Écartées"
          label
          data-test="sheet-filtered-out"
        >
          <template #end>
            <input
              type="checkbox"
              role="switch"
              :checked="filters.showFilteredOut"
              @change="emit('update', { showFilteredOut: !filters.showFilteredOut })"
            >
          </template>
        </GroupedRow>
        <GroupedRow
          title="Expirées"
          label
          data-test="sheet-expired"
        >
          <template #end>
            <input
              type="checkbox"
              role="switch"
              :checked="filters.showExpired"
              @change="emit('update', { showExpired: !filters.showExpired })"
            >
          </template>
        </GroupedRow>
      </GroupedList>
      <GroupedList :level="3">
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
        <GroupedRow
          title="Candidature chez l'employeur"
          label
          data-test="sheet-external"
        >
          <template #end>
            <input
              type="checkbox"
              role="switch"
              :checked="filters.externalOnly"
              @change="emit('update', { externalOnly: !filters.externalOnly })"
            >
          </template>
        </GroupedRow>
        <GroupedRow
          title="Sans les offres à vérifier"
          label
          data-test="sheet-doubtful"
        >
          <template #end>
            <input
              type="checkbox"
              role="switch"
              :checked="filters.hideDoubtful"
              @change="emit('update', { hideDoubtful: !filters.hideDoubtful })"
            >
          </template>
        </GroupedRow>
      </GroupedList>

      <GroupedList
        v-if="facets.sources.length"
        title="Sites"
        :level="3"
      >
        <GroupedRow
          v-for="facet in facets.sources"
          :key="facet.value"
          :title="sourceLabel[facet.value] ?? facet.value"
          :value="String(facet.count)"
          label
          :data-test="`sheet-source-${facet.value}`"
        >
          <template #start>
            <input
              type="checkbox"
              :checked="filters.sources.includes(facet.value as Source)"
              @change="emit('update', { sources: toggle(filters.sources, facet.value as Source) })"
            >
          </template>
        </GroupedRow>
      </GroupedList>

      <GroupedList
        v-if="facets.cantons.length"
        title="Cantons"
        :level="3"
      >
        <GroupedRow
          v-for="facet in facets.cantons"
          :key="facet.value"
          :title="facet.value"
          :value="String(facet.count)"
          label
          :data-test="`sheet-canton-${facet.value}`"
        >
          <template #start>
            <input
              type="checkbox"
              :checked="filters.cantons.includes(facet.value)"
              @change="emit('update', { cantons: toggle(filters.cantons, facet.value) })"
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
        class="primary"
        data-test="sheet-show"
        @click="emit('close')"
      >
        {{ showLabel }}
      </button>
    </template>
  </BottomSheet>
</template>
