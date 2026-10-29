<script setup lang="ts">
import { computed } from "vue";

import type { OfferFacets, Source } from "../api/client";
import { sourceLabel } from "../format";
import type { OfferFilters, View } from "../composables/useOfferFilters";
import BottomSheet from "./BottomSheet.vue";
import GroupedList from "./GroupedList.vue";
import GroupedRow from "./GroupedRow.vue";

// Les filtres des Offres sous 600 px (planche « Structure téléphone », 248:306) : une feuille du bas.
// Statut en radios, note en cases, télétravail en interrupteur, taux en ligne avec sa valeur ; puis
// les sites et les cantons. Chaque choix s'applique tout de suite ; « Afficher N offres » referme.
const props = defineProps<{ open: boolean; filters: OfferFilters; facets: OfferFacets; total: number }>();
const emit = defineEmits<{ update: [patch: Partial<OfferFilters>]; reset: []; close: [] }>();

const VIEWS: { value: View; label: string }[] = [
  { value: "to_review", label: "À examiner" },
  { value: "in_progress", label: "En cours" },
  { value: "later", label: "Plus tard" },
  { value: "filtered_out", label: "Écartées" },
  { value: "expired", label: "Expirées" },
  { value: "all", label: "Toutes" },
];

// Les quatre mots de la note (format.ts, scoreWord) et leurs bornes. Le filtre est un intervalle :
// cocher deux mots qui ne se suivent pas coche aussi celui du milieu.
const BANDS = [
  { label: "Très proche", min: 85, max: 100 },
  { label: "Proche", min: 70, max: 84 },
  { label: "À creuser", min: 50, max: 69 },
  { label: "Loin", min: 0, max: 49 },
];
const range = computed(() =>
  props.filters.minScore === null && props.filters.maxScore === null
    ? null
    : { low: props.filters.minScore ?? 0, high: props.filters.maxScore ?? 100 },
);
function checked(band: (typeof BANDS)[number]): boolean {
  const r = range.value;
  return !!r && band.min >= r.low && band.max <= r.high;
}
function toggleBand(band: (typeof BANDS)[number]): void {
  const chosen = BANDS.filter((b) => (b === band ? !checked(b) : checked(b)));
  if (!chosen.length) return emit("update", { minScore: null, maxScore: null });
  const low = Math.min(...chosen.map((b) => b.min));
  const high = Math.max(...chosen.map((b) => b.max));
  emit("update", { minScore: low > 0 ? low : null, maxScore: high < 100 ? high : null });
}

const RATES = [null, 50, 60, 70, 80, 90, 100];
function onRate(event: Event): void {
  const value = Number((event.target as HTMLSelectElement).value);
  emit("update", { minRate: value > 0 ? value : null });
}

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
      <GroupedList
        title="Statut"
        :level="3"
      >
        <GroupedRow
          v-for="view in VIEWS"
          :key="view.value"
          :title="view.label"
          label
          :data-test="`sheet-view-${view.value}`"
        >
          <template #start>
            <input
              type="radio"
              name="sheet-view"
              :checked="filters.view === view.value"
              @change="emit('update', { view: view.value })"
            >
          </template>
        </GroupedRow>
      </GroupedList>

      <GroupedList
        title="Note"
        :level="3"
      >
        <GroupedRow
          v-for="band in BANDS"
          :key="band.label"
          :title="band.label"
          label
          :data-test="`sheet-score-${band.min}`"
        >
          <template #start>
            <input
              type="checkbox"
              :checked="checked(band)"
              @change="toggleBand(band)"
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
          title="Taux minimum"
          label
          data-test="sheet-rate"
        >
          <template #end>
            <select
              class="field-compact"
              :value="filters.minRate ?? ''"
              @change="onRate"
            >
              <option
                v-for="rate in RATES"
                :key="rate ?? 'tous'"
                :value="rate ?? ''"
              >
                {{ rate === null ? "Tous" : `${rate} %` }}
              </option>
            </select>
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
        class="secondary"
        data-test="sheet-reset"
        @click="emit('reset')"
      >
        Réinitialiser
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
