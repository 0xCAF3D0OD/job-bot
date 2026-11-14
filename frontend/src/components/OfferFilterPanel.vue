<script setup lang="ts">
import { computed } from "vue";

import type { OfferFacets } from "../api/client";
import { basisChoices, DEFAULT_FILTERS, radioKey, type OfferFilters, type Sort, type View } from "../composables/useOfferFilters";
import AppIcon from "./AppIcon.vue";

// Le panneau « Filtres » de l'ordinateur (maquette du 8 novembre, CandidaturesOrdinateurB état « filtres », docs/143,
// D24) : il remplace la colonne liste (même largeur, toute la hauteur, entrée ja-slide-l), le détail reste à droite.
// En tête, « ‹ Retour à la liste » et le titre. Les choix restent si on le ferme d'un clic à l'extérieur. Statut, Trier, Correspondance minimale et Taux minimum en pastilles (aria-pressed), puis le
// télétravail et les offres écartées. Seul le milieu défile ; le pied reste en bas avec « Tout effacer » et
// « Afficher n offres », qui referme. Chaque choix s'applique tout de suite (comme la feuille du téléphone).
const props = defineProps<{ filters: OfferFilters; counts: Record<View, number>; facets: OfferFacets; total: number }>();
// « Note » (prompt du 10 novembre au soir, PR 26 ; filtres de CandidaturesOrdinateurB) : Toutes, Sûres · n,
// Provisoires · n, un seul choix (role="radio"), avec les nombres du serveur. La phrase d'explication n'est que dans la
// feuille du téléphone, comme dans les maquettes.
const bases = computed(() => basisChoices(props.facets));
const emit = defineEmits<{ update: [patch: Partial<OfferFilters>]; reset: []; close: [] }>();

const VIEWS: { label: string; value: View }[] = [
  { label: "À traiter", value: "pending" },
  { label: "À examiner", value: "to_review" },
  { label: "En préparation", value: "in_progress" },
  { label: "Gardées", value: "later" },
];
const SORTS: { label: string; value: Sort }[] = [
  { label: "Par jour", value: "day" },
  { label: "Par note", value: "score" },
];
// En préparation se trie par dernière action (docs/43) : le choix n'existe que là, et part avec elle.
const sorts = computed(() => (props.filters.view === "in_progress" ? [{ label: "Dernière action", value: "activity" as Sort }, ...SORTS] : SORTS));
function selectView(view: View): void {
  if (view === "in_progress") emit("update", { view, sort: "activity" });
  else if (props.filters.sort === "activity") emit("update", { view, sort: DEFAULT_FILTERS.sort });
  else emit("update", { view });
}
// La correspondance en mots (D3), mêmes seuils que la feuille du téléphone.
const SCORES: { label: string; min: number | null }[] = [
  { label: "Toutes", min: null },
  { label: "À creuser et +", min: 50 },
  { label: "Proche et +", min: 75 },
  { label: "Très proche", min: 85 },
];
const RATES: { label: string; value: number | null }[] = [
  { label: "Tous", value: null },
  { label: "60 %", value: 60 },
  { label: "80 %", value: 80 },
  { label: "100 %", value: 100 },
];
// Une adresse d'avant (?note=60-90) garde ses bornes, et aucun choix n'est marqué.
const scoreChoice = computed(() => (props.filters.maxScore === null ? props.filters.minScore : -1));
const showLabel = computed(() => (props.total <= 1 ? `Afficher ${props.total} offre` : `Afficher ${props.total} offres`));
</script>

<template>
  <section
    id="offers-filters"
    class="filter-panel"
    aria-labelledby="offers-filters-title"
    data-test="filters-dialog"
  >
    <div class="filter-panel-head">
      <button
        type="button"
        class="link filter-panel-back"
        data-test="close-filters"
        @click="emit('close')"
      >
        <AppIcon name="chevron-left" />Retour à la liste
      </button>
      <h2
        id="offers-filters-title"
        tabindex="-1"
      >
        Filtres
      </h2>
    </div>
    <div class="filter-panel-body">
      <div
        class="filter-panel-group"
        role="group"
        aria-labelledby="pop-view"
      >
        <span id="pop-view">Statut</span>
        <div>
          <button
            v-for="choice in VIEWS"
            :key="choice.value"
            type="button"
            :aria-pressed="filters.view === choice.value"
            :data-test="`pop-view-${choice.value}`"
            @click="selectView(choice.value)"
          >
            {{ choice.label }} · {{ counts[choice.value] }}
          </button>
        </div>
      </div>
      <hr>
      <div
        class="filter-panel-group"
        role="group"
        aria-labelledby="pop-sort"
      >
        <span id="pop-sort">Trier</span>
        <div>
          <button
            v-for="choice in sorts"
            :key="choice.value"
            type="button"
            :aria-pressed="filters.sort === choice.value"
            :data-test="`pop-sort-${choice.value}`"
            @click="emit('update', { sort: choice.value })"
          >
            {{ choice.label }}
          </button>
        </div>
      </div>
      <hr>
      <div
        class="filter-panel-group"
        role="group"
        aria-labelledby="pop-score"
      >
        <span id="pop-score">Correspondance minimale</span>
        <div>
          <button
            v-for="choice in SCORES"
            :key="choice.label"
            type="button"
            :aria-pressed="scoreChoice === choice.min"
            :data-test="`pop-score-${choice.min ?? 'all'}`"
            @click="emit('update', { minScore: choice.min, maxScore: null })"
          >
            {{ choice.label }}
          </button>
        </div>
      </div>
      <hr>
      <div class="filter-panel-group">
        <span id="pop-basis">Note</span>
        <div
          role="radiogroup"
          aria-labelledby="pop-basis"
          @keydown="radioKey"
        >
          <button
            v-for="choice in bases"
            :key="choice.value ?? 'all'"
            type="button"
            role="radio"
            :aria-checked="filters.basis === choice.value"
            :tabindex="filters.basis === choice.value ? 0 : -1"
            :data-test="`pop-basis-${choice.value ?? 'all'}`"
            @click="emit('update', { basis: choice.value })"
          >
            {{ choice.label }}
          </button>
        </div>
      </div>
      <hr>
      <div
        class="filter-panel-group"
        role="group"
        aria-labelledby="pop-rate"
      >
        <span id="pop-rate">Taux minimum</span>
        <div>
          <button
            v-for="choice in RATES"
            :key="choice.label"
            type="button"
            :aria-pressed="filters.minRate === choice.value"
            :data-test="`pop-rate-${choice.value ?? 'all'}`"
            @click="emit('update', { minRate: choice.value })"
          >
            {{ choice.label }}
          </button>
        </div>
      </div>
      <hr>
      <label class="filter-panel-switch">Télétravail au moins partiel<input
        type="checkbox"
        role="switch"
        :checked="filters.remote !== null"
        data-test="pop-remote"
        @change="emit('update', { remote: filters.remote === null ? 'partial' : null })"
      ></label>
      <label
        v-if="filters.view === 'pending'"
        class="filter-panel-switch"
      ><span>Masquer les offres écartées<small>Éteins ce réglage pour les voir</small></span><input
        type="checkbox"
        role="switch"
        :checked="!filters.showFilteredOut"
        data-test="pop-filtered-out"
        @change="emit('update', { showFilteredOut: !filters.showFilteredOut })"
      ></label>
    </div>
    <div class="filter-panel-foot">
      <button
        type="button"
        class="link"
        data-test="filters-reset"
        @click="emit('reset')"
      >
        Tout effacer
      </button>
      <button
        type="button"
        class="primary"
        data-test="filters-done"
        @click="emit('close')"
      >
        {{ showLabel }}
      </button>
    </div>
  </section>
</template>

<style>
/* Valeurs du HTML de la maquette : la colonne liste (560 px), toute la hauteur, coins --radius-card ; pastilles de
   36 px aux bords de 1,5 px ; pied de 14/24/18 sous un filet. */
.filter-panel {
  --pop-pill: 36px; --pop-14: 14px; --pop-6: 6px; --pop-15: 15px; --pop-18: 18px; --pop-2: 2px;
  box-sizing: border-box; display: flex; flex-direction: column; flex: 1 1 auto; width: 100%; height: 100%; overflow: hidden;
  background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius-card);
}
@media (prefers-reduced-motion: no-preference) { .filter-panel { animation: ja-slide-l 200ms cubic-bezier(.05,.7,.1,1); } }
.filter-panel-head { flex: none; display: flex; align-items: center; justify-content: space-between; gap: var(--space-3); margin: 0 var(--space-6); padding: var(--pop-18) 0 var(--space-3); border-bottom: 1px solid var(--line-soft); }
.filter-panel-head h2 { margin: 0; font-size: var(--font-title); font-weight: var(--weight-heavy); outline: none; }
.filter-panel-back { display: inline-flex; align-items: center; gap: var(--space-1); min-height: var(--target-min); padding: 0; font-size: var(--pop-15); font-weight: var(--weight-bold); }
.filter-panel-back .icon { width: 18px; height: 18px; }
.filter-panel-body {
  flex: 1; min-height: 0; overflow-y: auto; display: flex; flex-direction: column; gap: var(--pop-14);
  padding: var(--space-2) var(--space-6) var(--space-4); margin-right: var(--space-1);
}
.filter-panel-body hr { margin: 0; border: 0; border-top: 1px solid var(--line-soft); }
.filter-panel-group { display: flex; flex-direction: column; gap: var(--space-2); padding: var(--space-1) 0 var(--pop-2); }
.filter-panel-group > span { font-size: var(--label-caps); font-weight: var(--weight-bold); color: var(--text-secondary); }
.filter-panel-group > div { display: flex; flex-wrap: wrap; gap: var(--pop-6); }
.filter-panel-group button {
  height: var(--pop-pill); min-height: 0; padding: 0 var(--pop-14); border: 1.5px solid color-mix(in srgb, var(--line) 90%, var(--text-secondary));
  border-radius: var(--radius-pill); background: var(--surface); color: var(--text); font-size: var(--font-small); font-weight: var(--weight-semibold);
}
.filter-panel-group button:is([aria-pressed="true"], [aria-checked="true"]) { border-color: var(--primary-graphic); background: var(--primary-soft); color: var(--primary-text); }
.filter-panel-switch {
  display: flex; align-items: center; justify-content: space-between; gap: var(--space-3); min-height: var(--btn-tertiary);
  font-size: var(--pop-15); font-weight: var(--weight-semibold);
}
.filter-panel-switch small { display: block; font-size: var(--label-caps); font-weight: var(--weight-regular); color: var(--text-secondary); }
.filter-panel-foot { flex: none; display: flex; align-items: center; justify-content: space-between; padding: var(--pop-14) var(--space-6) var(--pop-18); border-top: 1px solid var(--line); }
.filter-panel-foot .link { min-height: var(--target-min); padding: 0 var(--space-1); font-size: var(--pop-15); font-weight: var(--weight-bold); }
.filter-panel-foot .primary { min-height: var(--btn-tertiary); padding: 0 var(--space-6); border-radius: var(--radius-pill); font-size: var(--font-body); font-weight: var(--weight-bold); }
</style>
