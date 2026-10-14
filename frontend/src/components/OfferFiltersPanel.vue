<script setup lang="ts">
import { computed, ref, watch } from "vue";

import type { FilterKey, OfferFacets, Source } from "../api/client";
import type { OfferFilters, Remote, Sort, View } from "../composables/useOfferFilters";
import { activeCount, DEFAULT_FILTERS } from "../composables/useOfferFilters";
import { sourceLabel } from "../format";
import ScoreCurve from "./ScoreCurve.vue";

const props = defineProps<{
  filters: OfferFilters;
  counts: Record<View, number>;
  facets: OfferFacets;
  // Offres affichées avec ces filtres, pour « Afficher N offres » (téléphone).
  total: number;
  // Filtres affichés (docs/10 §3) ; statut, recherche et tri le sont toujours.
  visible: FilterKey[];
}>();
const emit = defineEmits<{
  update: [patch: Partial<OfferFilters>];
  reset: [];
  visibility: [visible: FilterKey[]];
  done: [];
}>();

const FILTERS: { key: FilterKey; label: string }[] = [
  { key: "score", label: "Note" },
  { key: "remote", label: "Télétravail" },
  { key: "sources", label: "Sites" },
  { key: "cantons", label: "Cantons" },
  { key: "rate", label: "Taux minimum (%)" },
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
const REMOTE: { value: Remote | null; label: string }[] = [
  { value: null, label: "Tous" },
  { value: "partial", label: "Au moins partiel" },
  { value: "full", label: "Complet" },
];
const SORTS: { value: Sort; label: string }[] = [
  { value: "day", label: "Par jour" },
  { value: "score", label: "Note" },
  { value: "recent", label: "Récentes" },
  { value: "popular", label: "Populaires" },
];

// « Dernière action » n'a de sens que pour les offres en cours, où c'est le tri par défaut
// (docs/14 §3) ; en quittant cet onglet, on revient au tri ordinaire.
const sorts = computed(() =>
  props.filters.view === "in_progress"
    ? [{ value: "activity" as Sort, label: "Dernière action" }, ...SORTS]
    : SORTS,
);

function selectView(view: View): void {
  if (view === "in_progress") emit("update", { view, sort: "activity" });
  else if (props.filters.sort === "activity") emit("update", { view, sort: DEFAULT_FILTERS.sort });
  else emit("update", { view });
}

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

function onScore(min: number | null, max: number | null): void {
  emit("update", { minScore: min, maxScore: max });
}

// Cartes (docs/27) : une ligne par filtre, « nom · valeur · › » ; un clic ouvre le choix
// dans le même panneau, « ‹ Retour » y revient.
type Page = "view" | "sort" | "remote" | "rate" | "sources" | "cantons";
const page = ref<Page | null>(null);
const PAGE_TITLES: Record<Page, string> = {
  view: "Statut",
  sort: "Tri",
  remote: "Télétravail",
  rate: "Taux minimum (%)",
  sources: "Sites",
  cantons: "Cantons",
};

function open(next: Page): void {
  page.value = next;
}

function choose(patch: Partial<OfferFilters>): void {
  emit("update", patch);
  page.value = null;
}

function chooseView(view: View): void {
  selectView(view);
  page.value = null;
}

const viewValue = computed(() => {
  const entry = VIEWS.find((v) => v.value === props.filters.view);
  return `${entry?.label ?? ""} · ${props.counts[props.filters.view]}`;
});
const sortValue = computed(() => sorts.value.find((s) => s.value === props.filters.sort)?.label ?? "");
const remoteValue = computed(() => REMOTE.find((r) => r.value === props.filters.remote)?.label ?? "Tous");
const sourcesValue = computed(() =>
  props.filters.sources.length
    ? props.filters.sources.map((s) => sourceLabel[s] ?? s).join(", ")
    : "tous",
);
const cantonsValue = computed(() => (props.filters.cantons.length ? props.filters.cantons.join(", ") : "tous"));
const showPost = computed(() => ["remote", "rate", "external"].some((k) => props.visible.includes(k as FilterKey)));
const showOrigin = computed(() => ["sources", "cantons"].some((k) => props.visible.includes(k as FilterKey)));
</script>

<template>
  <div
    class="filters-panel"
    data-test="filters"
  >
    <template v-if="page === null">
      <input
        id="offer-search"
        v-model="search"
        class="filters-search"
        type="search"
        aria-label="Recherche"
        placeholder="Titre, entreprise, mot-clé…"
        data-test="search"
      >

      <div class="filter-card">
        <button
          type="button"
          class="filter-row"
          data-test="row-view"
          @click="open('view')"
        >
          <span>Statut</span><span class="filter-row-value">{{ viewValue }}</span>
        </button>
        <button
          type="button"
          class="filter-row"
          data-test="row-sort"
          @click="open('sort')"
        >
          <span>Tri</span><span class="filter-row-value">{{ sortValue }}</span>
        </button>
      </div>

      <div
        v-if="visible.includes('score')"
        class="filter-card filter-card-body"
      >
        <span class="filter-card-title">Note</span>
        <ScoreCurve
          :bins="facets.scores ?? []"
          :min="filters.minScore"
          :max="filters.maxScore"
          :unscored="facets.unscored ?? 0"
          @change="onScore"
        />
      </div>

      <div
        v-if="showPost"
        class="filter-card"
      >
        <button
          v-if="visible.includes('remote')"
          type="button"
          class="filter-row"
          data-test="row-remote"
          @click="open('remote')"
        >
          <span>Télétravail</span><span class="filter-row-value">{{ remoteValue }}</span>
        </button>
        <button
          v-if="visible.includes('rate')"
          type="button"
          class="filter-row"
          data-test="row-rate"
          @click="open('rate')"
        >
          <span>Taux minimum (%)</span><span class="filter-row-value">{{ filters.minRate ?? "tous" }}</span>
        </button>
        <label
          v-if="visible.includes('external')"
          class="filter-row filter-switch"
        >
          <span>Chez l'employeur uniquement</span>
          <input
            type="checkbox"
            role="switch"
            :checked="filters.externalOnly"
            data-test="external-only"
            @change="emit('update', { externalOnly: !filters.externalOnly })"
          >
        </label>
      </div>

      <div
        v-if="showOrigin"
        class="filter-card"
      >
        <button
          v-if="visible.includes('sources')"
          type="button"
          class="filter-row"
          data-test="row-sources"
          @click="open('sources')"
        >
          <span>Sites</span><span class="filter-row-value">{{ sourcesValue }}</span>
        </button>
        <button
          v-if="visible.includes('cantons')"
          type="button"
          class="filter-row"
          data-test="row-cantons"
          @click="open('cantons')"
        >
          <span>Cantons</span><span class="filter-row-value">{{ cantonsValue }}</span>
        </button>
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
    </template>

    <template v-else>
      <div class="filter-page-head">
        <button
          type="button"
          class="link"
          data-test="filter-back"
          @click="page = null"
        >
          ‹ Retour
        </button>
        <strong>{{ PAGE_TITLES[page] }}</strong>
      </div>

      <div class="filter-card">
        <template v-if="page === 'view'">
          <button
            v-for="entry in VIEWS"
            :key="entry.value"
            type="button"
            class="filter-row filter-option"
            role="radio"
            :aria-checked="filters.view === entry.value"
            :data-test="`view-${entry.value}`"
            @click="chooseView(entry.value)"
          >
            <span>{{ entry.label }}</span><span class="facet-count">{{ counts[entry.value] }}</span>
          </button>
        </template>
        <template v-else-if="page === 'sort'">
          <button
            v-for="entry in sorts"
            :key="entry.value"
            type="button"
            class="filter-row filter-option"
            role="radio"
            :aria-checked="filters.sort === entry.value"
            :data-test="`sort-${entry.value}`"
            @click="choose({ sort: entry.value })"
          >
            <span>{{ entry.label }}</span>
          </button>
        </template>
        <template v-else-if="page === 'remote'">
          <button
            v-for="entry in REMOTE"
            :key="String(entry.value)"
            type="button"
            class="filter-row filter-option"
            role="radio"
            :aria-checked="filters.remote === entry.value"
            :data-test="`remote-${entry.value ?? 'all'}`"
            @click="choose({ remote: entry.value })"
          >
            <span>{{ entry.label }}</span>
          </button>
        </template>
        <div
          v-else-if="page === 'rate'"
          class="filter-card-body"
        >
          <span class="filter-card-title">{{ filters.minRate ?? "tous" }}</span>
          <input
            id="offer-rate"
            type="range"
            min="0"
            max="100"
            step="10"
            aria-label="Taux minimum en pour cent"
            :value="filters.minRate ?? 0"
            data-test="min-rate"
            @change="onRate"
          >
          <span class="hint">Les offres sans taux indiqué restent visibles.</span>
        </div>
        <template v-else-if="page === 'sources' || page === 'cantons'">
          <button
            type="button"
            class="filter-row filter-option-clear"
            :disabled="page === 'sources' ? !filters.sources.length : !filters.cantons.length"
            @click="emit('update', page === 'sources' ? { sources: [] } : { cantons: [] })"
          >
            <span class="link">Tout décocher</span>
          </button>
          <template v-if="page === 'sources'">
            <label
              v-for="facet in facets.sources"
              :key="facet.value"
              class="filter-row filter-check"
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
          </template>
          <template v-else>
            <label
              v-for="facet in facets.cantons"
              :key="facet.value"
              class="filter-row filter-check"
            >
              <input
                type="checkbox"
                :checked="filters.cantons.includes(facet.value)"
                :data-test="`canton-${facet.value}`"
                @change="emit('update', { cantons: toggle(filters.cantons, facet.value) })"
              >
              <span>{{ facet.value }}</span>
              <span class="facet-count">{{ facet.count }}</span>
            </label>
          </template>
        </template>
      </div>
    </template>

    <div class="filters-footer">
      <button
        type="button"
        class="filters-clear"
        :disabled="!activeCount(filters)"
        data-test="reset"
        @click="emit('reset')"
      >
        Effacer tout ({{ activeCount(filters) }})
      </button>
      <button
        type="button"
        class="filters-done"
        data-test="filters-done"
        @click="emit('done')"
      >
        Afficher {{ total }} offre{{ total > 1 ? "s" : "" }}
      </button>
    </div>
  </div>
</template>
