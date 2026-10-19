<script setup lang="ts">
import { computed, ref, watch } from "vue";

import type { FilterKey, OfferFacets, Source } from "../api/client";
import type { OfferFilters, Remote, Sort, View } from "../composables/useOfferFilters";
import { activeCount, DEFAULT_FILTERS } from "../composables/useOfferFilters";
import { sourceLabel } from "../format";
import AppIcon from "./AppIcon.vue";
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
  { key: "doubtful", label: "Offres à vérifier" },
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

// Cartes (docs/27) : une ligne par filtre, « nom · valeur », la flèche qui tourne ; un clic déplie le choix
// sous la ligne, un seul à la fois : ouvrir un autre filtre (ou recliquer) referme le premier.
type Page = "view" | "sort" | "remote" | "rate" | "sources" | "cantons";
const page = ref<Page | null>(null);

function open(next: Page): void {
  page.value = page.value === next ? null : next;
}

function choose(patch: Partial<OfferFilters>): void {
  emit("update", patch);
}

function chooseView(view: View): void {
  selectView(view);
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
const showPost = computed(() =>
  ["remote", "rate", "external", "doubtful"].some((k) => props.visible.includes(k as FilterKey)),
);
const showOrigin = computed(() => ["sources", "cantons"].some((k) => props.visible.includes(k as FilterKey)));

// « Plus de filtres » (docs/73 §6) : la recherche, le statut, le tri et la note restent
// visibles ; le reste est replié, avec le nombre de filtres actifs. Déplié d'office s'il y en a.
const secondaryActive = computed(
  () =>
    Number(props.filters.remote !== null) +
    Number(props.filters.minRate !== null) +
    Number(props.filters.externalOnly) +
    Number(props.filters.hideDoubtful) +
    props.filters.sources.length +
    props.filters.cantons.length,
);
const more = ref(secondaryActive.value > 0);
</script>

<template>
  <div
    class="filters-panel"
    data-test="filters"
  >
    <!-- Recherche : loupe devant, libellé lu par les lecteurs d'écran (docs/29 §5). -->
    <span class="filters-search-wrap">
      <AppIcon name="search" />
      <input
        id="offer-search"
        v-model="search"
        class="filters-search"
        type="search"
        aria-label="Recherche"
        placeholder="Titre, entreprise, mot-clé…"
        data-test="search"
      >
    </span>

    <div class="filter-card">
      <button
        type="button"
        class="filter-row"
        :aria-expanded="page === 'view'"
        data-test="row-view"
        @click="open('view')"
      >
        <span class="with-icon"><AppIcon name="list-check" />Statut</span><span class="filter-row-value">{{ viewValue }}</span>
      </button>
      <div
        v-if="page === 'view'"
        class="filter-drop"
      >
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
      </div>
      <button
        type="button"
        class="filter-row"
        :aria-expanded="page === 'sort'"
        data-test="row-sort"
        @click="open('sort')"
      >
        <span class="with-icon"><AppIcon name="arrow-down" />Tri</span><span class="filter-row-value">{{ sortValue }}</span>
      </button>
      <div
        v-if="page === 'sort'"
        class="filter-drop"
      >
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
      </div>
    </div>

    <div
      v-if="visible.includes('score')"
      class="filter-card filter-card-body"
    >
      <span class="filter-card-title with-icon"><AppIcon name="star" />Note</span>
      <ScoreCurve
        :bins="facets.scores ?? []"
        :min="filters.minScore"
        :max="filters.maxScore"
        :unscored="facets.unscored ?? 0"
        @change="onScore"
      />
    </div>

    <button
      type="button"
      class="filter-more link"
      :aria-expanded="more"
      data-test="more-filters"
      @click="more = !more"
    >
      <span class="with-icon"><AppIcon name="filter" />{{ more ? "Moins de filtres" : "Plus de filtres" }}<template v-if="secondaryActive">
        ({{ secondaryActive }})
      </template></span>
    </button>

    <div
      v-if="more && showPost"
      class="filter-card"
    >
      <template v-if="visible.includes('remote')">
        <button
          type="button"
          class="filter-row"
          :aria-expanded="page === 'remote'"
          data-test="row-remote"
          @click="open('remote')"
        >
          <span class="with-icon"><AppIcon name="home" />Télétravail</span><span class="filter-row-value">{{ remoteValue }}</span>
        </button>
        <div
          v-if="page === 'remote'"
          class="filter-drop"
        >
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
        </div>
      </template>
      <template v-if="visible.includes('rate')">
        <button
          type="button"
          class="filter-row"
          :aria-expanded="page === 'rate'"
          data-test="row-rate"
          @click="open('rate')"
        >
          <span class="with-icon"><AppIcon name="rate" />Taux minimum (%)</span><span class="filter-row-value">{{ filters.minRate ?? "tous" }}</span>
        </button>
        <div
          v-if="page === 'rate'"
          class="filter-drop filter-card-body"
        >
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
        </div>
      </template>
      <label
        v-if="visible.includes('external')"
        class="filter-row filter-switch"
      >
        <span class="with-icon"><AppIcon name="building" />Chez l'employeur uniquement</span>
        <input
          type="checkbox"
          role="switch"
          :checked="filters.externalOnly"
          data-test="external-only"
          @change="emit('update', { externalOnly: !filters.externalOnly })"
        >
      </label>
      <label
        v-if="visible.includes('doubtful')"
        class="filter-row filter-switch"
      >
        <span class="with-icon"><AppIcon name="alert" />Masquer les offres à vérifier</span>
        <input
          type="checkbox"
          role="switch"
          :checked="filters.hideDoubtful"
          data-test="hide-doubtful"
          @change="emit('update', { hideDoubtful: !filters.hideDoubtful })"
        >
      </label>
    </div>

    <div
      v-if="more && showOrigin"
      class="filter-card"
    >
      <template v-if="visible.includes('sources')">
        <button
          type="button"
          class="filter-row"
          :aria-expanded="page === 'sources'"
          data-test="row-sources"
          @click="open('sources')"
        >
          <span class="with-icon"><AppIcon name="globe" />Sites</span><span class="filter-row-value">{{ sourcesValue }}</span>
        </button>
        <div
          v-if="page === 'sources'"
          class="filter-drop"
        >
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
        </div>
      </template>
      <template v-if="visible.includes('cantons')">
        <button
          type="button"
          class="filter-row"
          :aria-expanded="page === 'cantons'"
          data-test="row-cantons"
          @click="open('cantons')"
        >
          <span class="with-icon"><AppIcon name="pin" />Cantons</span><span class="filter-row-value">{{ cantonsValue }}</span>
        </button>
        <div
          v-if="page === 'cantons'"
          class="filter-drop"
        >
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
        </div>
      </template>
    </div>

    <div
      v-if="more"
      class="filter-customize"
    >
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
          Filtres affichés
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

    <div class="filters-footer">
      <!-- Masqué tant qu'aucun filtre n'est actif (docs/43 n° 13). -->
      <button
        v-if="activeCount(filters)"
        type="button"
        class="filters-clear"
        data-test="reset"
        @click="emit('reset')"
      >
        <span class="with-icon"><AppIcon name="close" />Effacer tout ({{ activeCount(filters) }})</span>
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
