<script setup lang="ts">
import { computed } from "vue";

import type { OfferFacets } from "../api/client";
import {
  BASIS_HELP,
  basisChoices,
  choiceCount,
  CONTRACT_CHOICES,
  contractCount,
  DISTANCE_CHOICES,
  distanceCount,
  radioKey,
  rateCount,
  RATE_CHOICES,
  REMOTE_LABEL,
  SCORE_CHOICES,
  SCORE_HELP,
  scoreCount,
  toggleContract,
  UNKNOWN_PLACE_LABEL,
  viewPatch,
  type OfferFilters,
  type Sort,
  type View,
} from "../composables/useOfferFilters";
import { useFilterEntry } from "../filterHistory";
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
// Une entrée d’historique par application ; retour pendant l’ouverture ferme sans appliquer (Kevin, 17.11).
useFilterEntry(() => emit("close"));

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
  emit("update", viewPatch(view, props.filters.sort));
}
// Une adresse d'avant (?note=60-90) garde ses bornes, et aucun choix n'est marqué.
const scoreChoice = computed(() => (props.filters.maxScore === null ? props.filters.minScore : -1));
// Sous chaque choix de Note et de Taux, son nombre d'offres, avec les autres filtres actifs : le même calcul que la
// feuille du téléphone, donc le choix actif montre le nombre de « Afficher n offres » (Kevin, 18.11). À 0, le choix
// reste cliquable, grisé.
const scores = computed(() => SCORE_CHOICES.map((c) => ({ ...c, count: scoreCount(props.facets, c.min) })));
const rates = computed(() => RATE_CHOICES.map((c) => ({ ...c, count: rateCount(props.facets, c.value) })));
// Contrat (issue 468, Kevin 18.11) : plusieurs choix, « CDI · 120 » comme Statut.
const contracts = computed(() => CONTRACT_CHOICES.map((c) => ({ ...c, count: contractCount(props.facets, c.value) })));
// Distance (issue 468, Kevin 18.11) : un seul choix, le nombre sous chaque choix comme Taux ; « Lieu non précisé · n »
// pour les offres sans lieu reconnu. Absent sans commune connue.
const distances = computed(() => [
  ...DISTANCE_CHOICES.map((c) => ({ ...c, count: distanceCount(props.facets, c.value), counted: true })),
  { label: UNKNOWN_PLACE_LABEL, value: "unknown" as const, count: distanceCount(props.facets, "unknown"), counted: false },
]);
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
            :class="{ 'choice-empty': counts[choice.value] === 0 }"
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
            v-for="choice in scores"
            :key="choice.label"
            type="button"
            :class="['filter-panel-counted', { 'choice-empty': choice.count === 0 }]"
            aria-describedby="pop-score-help"
            :aria-pressed="scoreChoice === choice.min"
            :data-test="`pop-score-${choice.min ?? 'all'}`"
            @click="emit('update', { minScore: choice.min, maxScore: null })"
          >
            <span class="filter-panel-label">{{ choice.label }}</span><span class="filter-panel-sub">{{ choiceCount(choice.count) }}</span>
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
            :class="{ 'choice-empty': choice.count === 0 }"
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
            v-for="choice in rates"
            :key="choice.label"
            type="button"
            :class="['filter-panel-counted', { 'choice-empty': choice.count === 0 }]"
            :aria-pressed="filters.minRate === choice.value"
            :data-test="`pop-rate-${choice.value ?? 'all'}`"
            @click="emit('update', { minRate: choice.value })"
          >
            <span class="filter-panel-label">{{ choice.label }}</span><span class="filter-panel-sub">{{ choiceCount(choice.count) }}</span>
          </button>
        </div>
      </div>
      <hr>
      <div
        class="filter-panel-group"
        role="group"
        aria-labelledby="pop-contract"
      >
        <span id="pop-contract">Contrat</span>
        <div>
          <button
            v-for="choice in contracts"
            :key="choice.value"
            type="button"
            :class="{ 'choice-empty': choice.count === 0 }"
            :aria-pressed="filters.contracts.includes(choice.value)"
            :data-test="`pop-contract-${choice.value}`"
            @click="emit('update', { contracts: toggleContract(filters.contracts, choice.value) })"
          >
            {{ choice.label }} · {{ choiceCount(choice.count) }}
          </button>
        </div>
      </div>
      <template v-if="facets.distance_from && facets.distances?.length">
        <hr>
        <div
          class="filter-panel-group"
          role="group"
          aria-labelledby="pop-distance"
        >
          <span id="pop-distance">{{ `Distance depuis ${facets.distance_from}` }}</span>
          <div>
            <button
              v-for="choice in distances"
              :key="choice.value ?? 'all'"
              type="button"
              :class="{ 'filter-panel-counted': choice.counted, 'choice-empty': choice.count === 0 }"
              :aria-pressed="filters.distance === choice.value"
              :data-test="`pop-distance-${choice.value ?? 'all'}`"
              @click="emit('update', { distance: choice.value })"
            >
              <template v-if="choice.counted">
                <span class="filter-panel-label">{{ choice.label }}</span><span class="filter-panel-sub">{{ choiceCount(choice.count) }}</span>
              </template>
              <template v-else>
                {{ choice.label }} · {{ choiceCount(choice.count) }}
              </template>
            </button>
          </div>
        </div>
      </template>
      <hr>
      <label class="filter-panel-switch">{{ REMOTE_LABEL }}<input
        type="checkbox"
        role="switch"
        :checked="filters.remote !== null"
        data-test="pop-remote"
        @change="emit('update', { remote: filters.remote === null ? 'partial' : null })"
      ></label>
      <!-- Section 35 du 16.11 (CandidaturesOrdinateurAgence, panneau Filtres) : sous Télétravail. -->
      <label class="filter-panel-switch">Masquer les agences de placement<input
        type="checkbox"
        role="switch"
        :checked="filters.hideAgencies"
        data-test="pop-agencies"
        @change="emit('update', { hideAgencies: !filters.hideAgencies })"
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
