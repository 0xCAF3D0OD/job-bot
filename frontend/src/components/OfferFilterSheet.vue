<script setup lang="ts">
import { computed } from "vue";

import type { OfferFacets } from "../api/client";
import {
  BASIS_HELP_PHONE,
  basisChoices,
  choiceCount,
  radioKey,
  rateCount,
  RATE_CHOICES,
  REMOTE_LABEL,
  SCORE_CHOICES,
  SCORE_HELP_PHONE,
  scoreCount,
  viewPatch,
  type OfferFilters,
  type Sort,
  type View,
} from "../composables/useOfferFilters";
import AppIcon from "./AppIcon.vue";
import BottomSheet from "./BottomSheet.vue";
import GroupedList from "./GroupedList.vue";
import GroupedRow from "./GroupedRow.vue";
import SegmentedControl, { type SegmentOption } from "./SegmentedControl.vue";

// La feuille « Filtres » du téléphone (maquette Filtres, docs/139 étape 5c ; C5 validé le 2026-11-02 ;
// décisions de Kevin du 2026-11-06 ; section 31 du 16.11) : la note minimale sur 100, le taux d'activité (un seul choix, 5e),
// le tri (C8), « Masquer les offres écartées », le télétravail. Sites et cantons se règlent dans Compte ;
// Contrat et Distance attendent le serveur (issue 468). Chaque choix s'applique tout de suite ;
// « Afficher N offres » referme. La feuille s'arrête sous les onglets (690 px sur 844 dans la maquette).
// `far` : les offres « Loin » que la liste cache (0 si elles se voient). Tant qu'elles sont cachées, les nombres des
// choix les retirent aussi (`facets.near` du serveur) : le choix actif égale toujours « Afficher n offres » (Kevin,
// 18.11, choix a).
const props = defineProps<{ open: boolean; filters: OfferFilters; facets: OfferFacets; total: number; counts: Record<View, number>; far?: number }>();
const near = computed(() => ((props.far ?? 0) > 0 ? props.facets.near ?? null : null));
const shownFacets = computed<OfferFacets>(() =>
  near.value ? { ...props.facets, sure: near.value.sure, provisional: near.value.provisional, rates: near.value.rates } : props.facets,
);
const shownCounts = computed<Record<View, number>>(() => {
  if (!near.value) return props.counts;
  const views = Object.fromEntries(near.value.views.map((f) => [f.value, f.count]));
  return { ...props.counts, ...views };
});
const emit = defineEmits<{ update: [patch: Partial<OfferFilters>]; reset: []; close: [] }>();

// « Statut » en tête (Kevin, 17.11 0 h 33, docs/decisions/2026-11-16-1644-filtres-gardes.md) : un seul choix, les mêmes
// nombres que l'ordinateur, le même filtre que lui (gardé dans l'adresse et l'onglet) ; « Tout effacer » remet Toutes.
const VIEWS: { label: string; value: View }[] = [
  { label: "Toutes", value: "pending" },
  { label: "Nouvelles", value: "to_review" },
  { label: "Gardées", value: "later" },
  { label: "En préparation", value: "in_progress" },
];

// « Type de note » (PR 26 ; section 31 du 16.11) : Toutes, Définitives · n, Provisoires · n, un seul
// choix (role="radio"), les nombres du serveur, et la phrase qui dit ce qu'est une note provisoire.
const bases = computed(() => basisChoices(shownFacets.value));

// « Note minimale, sur 100 » (section 31 du 16.11) : un contrôle segmenté à 4 cases, un seul choix, mêmes seuils que
// l'ordinateur. Une adresse d'avant (?note=60-90) garde ses bornes, et aucune case n'est marquée.
// Sous chaque choix, son nombre d'offres (§65 du 17.11).
const SCORES = computed<SegmentOption[]>(() =>
  SCORE_CHOICES.map((c) => {
    // « Toutes » : sans les offres « Loin » tant qu'elles sont cachées ; les autres seuils les excluent déjà.
    const n = scoreCount(props.facets, c.min) - (c.min === null ? (props.far ?? 0) : 0);
    return { value: String(c.min ?? "all"), label: c.label, test: `sheet-score-${c.min ?? "all"}`, sub: choiceCount(n), empty: n === 0 };
  }),
);
const score = computed({
  get: () => (props.filters.maxScore !== null ? "" : String(props.filters.minScore ?? "all")),
  set: (value: string) => emit("update", { minScore: value === "all" ? null : Number(value), maxScore: null }),
});
// Le taux d'activité, un seul choix (5e) : le serveur garde une offre dont le taux maximum l'atteint, ou au
// taux inconnu. Un contrôle segmenté, pas des puces qui ont l'air de se cumuler.
const RATES = computed<SegmentOption[]>(() =>
  RATE_CHOICES.map((c) => {
    const n = rateCount(shownFacets.value, c.value);
    return { value: String(c.value ?? "all"), label: c.label, test: `sheet-rate-${c.value ?? "all"}`, sub: choiceCount(n), empty: n === 0 };
  }),
);
const rate = computed({
  get: () => (props.filters.minRate === null ? "all" : String(props.filters.minRate)),
  set: (value: string) => emit("update", { minRate: value === "all" ? null : Number(value) }),
});
const SORTS: { label: string; value: Sort }[] = [
  { label: "Par date", value: "day" },
  { label: "Note", value: "score" },
  { label: "Récentes", value: "recent" },
];

const showLabel = computed(() => (props.total <= 1 ? `Afficher ${props.total} offre` : `Afficher ${props.total} offres`));
</script>

<template>
  <BottomSheet
    :open="open"
    title="Filtres"
    size="large"
    class="filters-dialog"
    data-test="filters-sheet"
    @close="emit('close')"
  >
    <div class="filter-sheet">
      <fieldset class="filter-choices filter-status">
        <legend id="sheet-view-title">
          Statut
        </legend>
        <div
          class="filter-choices-row"
          role="radiogroup"
          aria-labelledby="sheet-view-title"
          @keydown="radioKey"
        >
          <button
            v-for="choice in VIEWS"
            :key="choice.value"
            type="button"
            :class="['filter-choice', { 'choice-empty': shownCounts[choice.value] === 0 }]"
            role="radio"
            :aria-checked="filters.view === choice.value"
            :tabindex="filters.view === choice.value ? 0 : -1"
            :data-test="`sheet-view-${choice.value}`"
            @click="emit('update', viewPatch(choice.value, filters.sort))"
          >
            <AppIcon
              v-if="filters.view === choice.value"
              name="tick"
            />{{ choice.label }} · {{ shownCounts[choice.value] }}
          </button>
        </div>
      </fieldset>

      <div class="filter-choices">
        <h3 id="sheet-score-title">
          Note minimale, sur 100
        </h3>
        <SegmentedControl
          v-model="score"
          :options="SCORES"
          label="Note minimale, sur 100"
          aria-labelledby="sheet-score-title"
          aria-describedby="sheet-score-help"
          full
        />
        <p
          id="sheet-score-help"
          class="filter-choices-help"
        >
          {{ SCORE_HELP_PHONE }}
        </p>
      </div>

      <div class="filter-choices">
        <h3 id="sheet-basis-title">
          Type de note
        </h3>
        <div
          class="filter-choices-row"
          role="radiogroup"
          aria-labelledby="sheet-basis-title"
          aria-describedby="sheet-basis-help"
          @keydown="radioKey"
        >
          <button
            v-for="choice in bases"
            :key="choice.value ?? 'all'"
            type="button"
            :class="['filter-choice', { 'choice-empty': choice.count === 0 }]"
            role="radio"
            :aria-checked="filters.basis === choice.value"
            :tabindex="filters.basis === choice.value ? 0 : -1"
            :data-test="`sheet-basis-${choice.value ?? 'all'}`"
            @click="emit('update', { basis: choice.value })"
          >
            <AppIcon
              v-if="filters.basis === choice.value"
              name="tick"
            />{{ choice.label }}
          </button>
        </div>
        <p
          id="sheet-basis-help"
          class="filter-choices-help"
        >
          {{ BASIS_HELP_PHONE }}
        </p>
      </div>

      <div class="filter-choices">
        <h3 id="sheet-rate-title">
          Taux d’activité
        </h3>
        <SegmentedControl
          v-model="rate"
          :options="RATES"
          label="Taux d’activité"
          aria-labelledby="sheet-rate-title"
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
          :title="REMOTE_LABEL"
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
        <!-- Section 35 du 16.11 (Filtres) : en dernier, après le télétravail (Kevin, section 31), avec « Seulement les employeurs directs ». -->
        <GroupedRow
          title="Masquer les agences de placement"
          description="Seulement les employeurs directs"
          label
          data-test="sheet-agencies"
        >
          <template #end>
            <input
              type="checkbox"
              role="switch"
              :checked="filters.hideAgencies"
              @change="emit('update', { hideAgencies: !filters.hideAgencies })"
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
/* « Statut » : un fieldset sans cadre, sa légende comme le titre des autres groupes. */
.filter-status { min-width: 0; margin: 0; padding: 0; border: 0; }
.filter-status > legend { float: left; width: 100%; padding: 0; }
/* Titres de groupe et aide (planche Filtres du 17.11, docs/design/regles.md §4) : libellés en capitales, 13 px,
   graisse 700, gris ; l'aide en pastille douce, comme sur la planche. */
.filter-status > legend, .filter-choices > h3 { font-size: var(--panel-caps-size); font-weight: var(--weight-bold); letter-spacing: .05em; text-transform: uppercase; color: var(--text-secondary); }
/* Le contour des puces non choisies : 1,5 px, gris des boutons secondaires (planche Filtres, --button-outline). */
.filter-choice { border-width: 1.5px; }
.filter-choice:not([aria-checked="true"], [aria-pressed="true"]) { border-color: var(--button-outline); }
.filter-choices-help { justify-self: start; padding: var(--space-1) 10px; border-radius: var(--radius-pill); background: var(--line-soft); color: var(--text-lead); font-size: var(--panel-caps-size); line-height: 18px; font-weight: var(--weight-semibold); }
/* Le pied (maquette Filtres) : un trait au-dessus, « Afficher N offres » en pilule de 54 px. */
.filters-dialog :deep(.sheet-actions) { margin: 0 calc(var(--space-4) * -1); padding: var(--space-3) var(--space-5) 0; border-top: 1px solid var(--line); }
.filters-clear { min-height: var(--btn-secondary); padding: 0 var(--space-4); font-size: var(--font-body); font-weight: var(--weight-bold); }
/* Un nombre sous le libellé (planche Filtres, §65) : segment de 56 px, libellé et nombre l'un sous l'autre. Ici
   plutôt que dans style.css : la feuille est seule à en montrer. */
:deep(.segmented > button:has(.segmented-sub)) { flex-direction: column; gap: 1px; min-height: 3.5rem; line-height: var(--leading-tight); }
:deep(.segmented-sub) { font-size: var(--font-caption); font-weight: var(--weight-medium); color: var(--text-secondary); }
/* Un choix à 0 offre reste visible et cliquable, grisé sur le même fond (Kevin, 18.11) ; le choix actif garde son style. */
:deep(.choice-empty:not([aria-checked="true"])) { color: var(--text-secondary); }
.filters-show { min-height: 3.375rem; border-radius: var(--radius-pill); font-size: var(--font-body); font-weight: var(--weight-bold); }
</style>
