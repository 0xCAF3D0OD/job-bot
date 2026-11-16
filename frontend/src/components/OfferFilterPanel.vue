<script setup lang="ts">
import { computed } from "vue";

import type { OfferFacets } from "../api/client";
import {
  BASIS_HELP,
  basisChoices,
  DEFAULT_FILTERS,
  radioKey,
  RATE_CHOICES,
  REMOTE_LABEL,
  SCORE_CHOICES,
  SCORE_HELP,
  type OfferFilters,
  type Sort,
  type View,
} from "../composables/useOfferFilters";
import AppIcon from "./AppIcon.vue";
import "../filterPanel.css";

// Le panneau « Filtres » de l'ordinateur (maquette du 8 novembre, CandidaturesOrdinateurB état « filtres », docs/143,
// D24) : il remplace la colonne liste (même largeur, toute la hauteur, entrée ja-slide-l), le détail reste à droite.
// En tête, « ‹ Retour à la liste » et le titre. Les choix restent si on le ferme d'un clic à l'extérieur. Statut, Trier, Note minimale et Taux d'activité en pastilles (aria-pressed), puis le
// télétravail et les offres écartées. Seul le milieu défile ; le pied reste en bas avec « Tout effacer » et
// « Afficher n offres », qui referme. Chaque choix s'applique tout de suite (comme la feuille du téléphone).
const props = defineProps<{ filters: OfferFilters; counts: Record<View, number>; facets: OfferFacets; total: number }>();
// « Type de note » (PR 26 ; section 31 du 16.11) : Toutes, Définitives · n, Provisoires · n, un seul choix
// (role="radio"), avec les nombres du serveur, et dessous la phrase qui dit ce qu'est une note provisoire (comme au
// téléphone). Les libellés sont ceux de la section 31 : des mots compris sans connaître jobA1.
const bases = computed(() => basisChoices(props.facets));
const emit = defineEmits<{ update: [patch: Partial<OfferFilters>]; reset: []; close: [] }>();

// Statut (section 38 du 16.11) : l'ordre du parcours d'une offre ; « Toutes » (les offres pas encore envoyées)
// reste le choix par défaut, même en dernier.
const VIEWS: { label: string; value: View }[] = [
  { label: "Nouvelles", value: "to_review" },
  { label: "Gardées", value: "later" },
  { label: "En préparation", value: "in_progress" },
  { label: "Toutes", value: "pending" },
];
const SORTS: { label: string; value: Sort }[] = [
  { label: "Par date", value: "day" },
  { label: "Par note", value: "score" },
];
// En préparation se trie par dernière action (docs/43) : le choix n'existe que là, et part avec elle.
const sorts = computed(() => (props.filters.view === "in_progress" ? [{ label: "Dernière action", value: "activity" as Sort }, ...SORTS] : SORTS));
function selectView(view: View): void {
  if (view === "in_progress") emit("update", { view, sort: "activity" });
  else if (props.filters.sort === "activity") emit("update", { view, sort: DEFAULT_FILTERS.sort });
  else emit("update", { view });
}
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
      <div class="filter-panel-group">
        <span id="pop-score">Note minimale, sur 100</span>
        <div
          role="group"
          aria-labelledby="pop-score"
        >
          <button
            v-for="choice in SCORE_CHOICES"
            :key="choice.label"
            type="button"
            aria-describedby="pop-score-help"
            :aria-pressed="scoreChoice === choice.min"
            :data-test="`pop-score-${choice.min ?? 'all'}`"
            @click="emit('update', { minScore: choice.min, maxScore: null })"
          >
            {{ choice.label }}
          </button>
        </div>
        <p
          id="pop-score-help"
          class="filter-choices-help"
        >
          {{ SCORE_HELP }}
        </p>
      </div>
      <hr>
      <div class="filter-panel-group">
        <span id="pop-basis">Type de note</span>
        <div
          role="radiogroup"
          aria-labelledby="pop-basis"
          aria-describedby="pop-basis-help"
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
        <p
          id="pop-basis-help"
          class="filter-choices-help"
        >
          {{ BASIS_HELP }}
        </p>
      </div>
      <hr>
      <div
        class="filter-panel-group"
        role="group"
        aria-labelledby="pop-rate"
      >
        <span id="pop-rate">Taux d’activité</span>
        <div>
          <button
            v-for="choice in RATE_CHOICES"
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
      <label class="filter-panel-switch">{{ REMOTE_LABEL }}<input
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
