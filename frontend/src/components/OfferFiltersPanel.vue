<script setup lang="ts">
import { ref, watch } from "vue";

import type { FilterKey, OfferFacets, Source } from "../api/client";
import type { OfferFilters, Sort, View } from "../composables/useOfferFilters";
import { activeCount } from "../composables/useOfferFilters";
import { sourceLabel } from "../format";

const props = defineProps<{
  filters: OfferFilters;
  counts: Record<View, number>;
  facets: OfferFacets;
  // Filtres affichés (docs/10 §3) ; statut, recherche et tri le sont toujours.
  visible: FilterKey[];
}>();
const emit = defineEmits<{
  update: [patch: Partial<OfferFilters>];
  reset: [];
  visibility: [visible: FilterKey[]];
}>();

const FILTERS: { key: FilterKey; label: string }[] = [
  { key: "score", label: "Note minimale" },
  { key: "sources", label: "Sites" },
  { key: "cantons", label: "Cantons" },
  { key: "rate", label: "Taux minimum" },
  { key: "external", label: "Candidature chez l'employeur" },
];
const customizing = ref(false);

function toggleVisible(key: FilterKey): void {
  const next = props.visible.includes(key) ? props.visible.filter((k) => k !== key) : [...props.visible, key];
  emit("visibility", next);
}

const VIEWS: { value: View; label: string }[] = [
  { value: "to_review", label: "À examiner" },
  { value: "in_progress", label: "En cours" },
  { value: "later", label: "Plus tard" },
  { value: "filtered_out", label: "Écartées" },
  { value: "expired", label: "Expirées" },
  { value: "all", label: "Toutes" },
];
const SORTS: { value: Sort; label: string }[] = [
  { value: "score", label: "Note" },
  { value: "recent", label: "Récentes" },
  { value: "popular", label: "Populaires" },
];

// Recherche : appliquée 300 ms après la dernière frappe.
const search = ref(props.filters.q);
let timer: ReturnType<typeof setTimeout> | undefined;
watch(search, (value) => {
  clearTimeout(timer);
  timer = setTimeout(() => emit("update", { q: value }), 300);
});
watch(
  () => props.filters.q,
  (value) => {
    if (value !== search.value.trim()) search.value = value;
  },
);

function toggle<T extends string>(values: T[], value: T): T[] {
  return values.includes(value) ? values.filter((v) => v !== value) : [...values, value];
}

function onRate(event: Event): void {
  const value = Number((event.target as HTMLInputElement).value);
  emit("update", { minRate: value > 0 ? value : null });
}

function onScore(event: Event): void {
  const value = Number((event.target as HTMLInputElement).value);
  emit("update", { minScore: value > 0 ? value : null });
}
</script>

<template>
  <div
    class="filters-panel"
    data-test="filters"
  >
    <div class="filter-group">
      <label
        class="filter-title"
        for="offer-search"
      >Recherche</label>
      <input
        id="offer-search"
        v-model="search"
        type="search"
        placeholder="Titre, entreprise, mot-clé…"
        data-test="search"
      >
    </div>

    <div class="filter-customize">
      <button
        type="button"
        class="link"
        :aria-expanded="customizing"
        data-test="customize"
        @click="customizing = !customizing"
      >
        {{ customizing ? "Terminer" : "Personnaliser les filtres" }}
      </button>
      <fieldset
        v-if="customizing"
        class="customize-list"
        data-test="customize-list"
      >
        <legend class="hint">
          Filtres affichés (statut, recherche et tri le sont toujours)
        </legend>
        <label
          v-for="entry in FILTERS"
          :key="entry.key"
          class="check"
        >
          <input
            type="checkbox"
            :checked="visible.includes(entry.key)"
            :data-test="`show-${entry.key}`"
            @change="toggleVisible(entry.key)"
          >
          {{ entry.label }}
        </label>
      </fieldset>
    </div>

    <div class="filter-group">
      <span class="filter-title">Statut</span>
      <div
        class="status-list"
        role="radiogroup"
        aria-label="Statut"
      >
        <button
          v-for="entry in VIEWS"
          :key="entry.value"
          type="button"
          role="radio"
          :aria-checked="filters.view === entry.value"
          :data-test="`view-${entry.value}`"
          @click="emit('update', { view: entry.value })"
        >
          <span>{{ entry.label }}</span>
          <span class="facet-count">{{ counts[entry.value] }}</span>
        </button>
      </div>
    </div>

    <div class="filter-group">
      <span class="filter-title">Tri</span>
      <div
        class="segmented"
        role="radiogroup"
        aria-label="Tri"
      >
        <button
          v-for="entry in SORTS"
          :key="entry.value"
          type="button"
          role="radio"
          :aria-checked="filters.sort === entry.value"
          :data-test="`sort-${entry.value}`"
          @click="emit('update', { sort: entry.value })"
        >
          {{ entry.label }}
        </button>
      </div>
    </div>

    <div
      v-if="visible.includes('score')"
      class="filter-group"
    >
      <label
        class="filter-title"
        for="offer-score"
      >
        Note minimale <span class="filter-value">{{ filters.minScore ? `${filters.minScore} / 100` : "toutes" }}</span>
      </label>
      <input
        id="offer-score"
        type="range"
        min="0"
        max="90"
        step="10"
        :value="filters.minScore ?? 0"
        data-test="min-score"
        @change="onScore"
      >
      <span
        v-if="filters.minScore"
        class="hint"
      >Les offres pas encore notées sont masquées.</span>
    </div>

    <div
      v-if="visible.includes('sources')"
      class="filter-group"
    >
      <span class="filter-title">Sites</span>
      <label
        v-for="facet in facets.sources"
        :key="facet.value"
        class="check facet"
      >
        <input
          type="checkbox"
          :checked="filters.sources.includes(facet.value as Source)"
          :data-test="`source-${facet.value}`"
          @change="emit('update', { sources: toggle(filters.sources, facet.value as Source) })"
        >
        <span>{{ sourceLabel[facet.value as Source] ?? facet.value }}</span>
        <span class="facet-count">{{ facet.count }}</span>
      </label>
    </div>

    <div
      v-if="visible.includes('cantons')"
      class="filter-group"
    >
      <span class="filter-title">Cantons</span>
      <div class="facet-chips">
        <button
          v-for="facet in facets.cantons"
          :key="facet.value"
          type="button"
          :class="['chip', { on: filters.cantons.includes(facet.value) }]"
          :aria-pressed="filters.cantons.includes(facet.value)"
          :data-test="`canton-${facet.value}`"
          @click="emit('update', { cantons: toggle(filters.cantons, facet.value) })"
        >
          {{ facet.value }} <span class="facet-count">{{ facet.count }}</span>
        </button>
      </div>
    </div>

    <div
      v-if="visible.includes('rate')"
      class="filter-group"
    >
      <label
        class="filter-title"
        for="offer-rate"
      >
        Taux minimum <span class="filter-value">{{ filters.minRate ? `${filters.minRate} %` : "tous" }}</span>
      </label>
      <input
        id="offer-rate"
        type="range"
        min="0"
        max="100"
        step="10"
        :value="filters.minRate ?? 0"
        data-test="min-rate"
        @change="onRate"
      >
      <span class="hint">Les offres sans taux indiqué restent visibles.</span>
    </div>

    <div
      v-if="visible.includes('external')"
      class="filter-group"
    >
      <span class="filter-title">Candidature</span>
      <label class="check facet">
        <input
          type="checkbox"
          :checked="filters.externalOnly"
          data-test="external-only"
          @change="emit('update', { externalOnly: !filters.externalOnly })"
        >
        <span>Chez l'employeur uniquement</span>
      </label>
    </div>

    <button
      v-if="activeCount(filters)"
      type="button"
      class="secondary small"
      data-test="reset"
      @click="emit('reset')"
    >
      Effacer les filtres ({{ activeCount(filters) }})
    </button>
  </div>
</template>
