<script setup lang="ts">
import { computed, ref } from "vue";

import AppIcon from "./AppIcon.vue";
import BottomSheet from "./BottomSheet.vue";
import CountBadge from "./CountBadge.vue";
import OfferSearch from "./OfferSearch.vue";
import { radioKey } from "../radioKey";
import { plural } from "../format";
import { SENT_FILTERS, type SentFilter, type SentSort } from "../sentFilters";

// Les filtres des Envoyées sur téléphone (maquette du 14 novembre, Envoyees, §3 et §6 de docs/design/regles.md) :
// - le champ « Poste, entreprise, lieu » sous l'en-tête Candidatures, au-dessus des onglets (#jobs-tools), à la même
//   place que sur Offres ; lu « Rechercher une candidature » (décision de Kevin du 14.11) ;
// - l'icône Filtres dans l'en-tête, à côté d'« Alertes », qui ouvre la feuille Filtres ;
// - dans la feuille : les statuts (avant en puces sous la recherche) et le tri, « À relancer d'abord » par défaut ou
//   « Plus récentes d'abord » (décision de Kevin du 14.11) ; « Tout effacer » et « Afficher N candidatures » en bas.
// Alignée sur la planche FiltresEnvoyees (§10, paquet du 15 novembre ; décision de Kevin du 15.11 ; visuel refait d'après
// la planche du 18.11) : titre « Filtres des envoyées », statut choisi coché. Le tri a trois choix (décision de Kevin du 15.11) : en contrôle segmenté, « Plus anciennes
// d’abord » était coupé en 390 px ; il prend donc les mêmes choix cochés que le statut, qui passent à la ligne.
// La logique (mots, statut et tri gardés dans l'adresse) reste dans ApplicationsView.
const props = defineProps<{ words: string; filter: SentFilter; sort: SentSort; counts: Record<SentFilter, number>; total: number }>();
const emit = defineEmits<{ "update:words": [value: string]; "update:filter": [value: SentFilter]; "update:sort": [value: SentSort]; reset: [] }>();

const open = ref(false);
// Un statut à 0 est masqué, sauf celui qui est choisi (pour pouvoir le quitter), comme sur ordinateur.
const shown = computed(() => SENT_FILTERS.filter((f) => f.value === "toutes" || props.counts[f.value] > 0 || f.value === props.filter));
const SORTS: { value: SentSort; label: string; test: string }[] = [
  { value: "relancer", label: "À relancer d’abord", test: "sent-sort-relancer" },
  { value: "recentes", label: "Plus récentes d’abord", test: "sent-sort-recentes" },
  { value: "anciennes", label: "Plus anciennes d’abord", test: "sent-sort-anciennes" },
];
const active = computed(() => (props.filter !== "toutes" ? 1 : 0) + (props.sort !== "relancer" ? 1 : 0));
const toggleLabel = computed(() => (active.value ? `Filtres, ${active.value} actif${active.value > 1 ? "s" : ""}` : "Filtres"));
const showLabel = computed(() => `Afficher ${plural(props.total, "candidature", "candidatures")}`);
</script>

<template>
  <Teleport
    to="#jobs-tools"
    defer
  >
    <OfferSearch
      class="sent-phone-search"
      :value="words"
      placeholder="Poste, entreprise, lieu"
      label="Rechercher une candidature"
      @search="emit('update:words', $event)"
    />
  </Teleport>
  <Teleport
    to="#topbar-page-tools"
    defer
  >
    <button
      type="button"
      class="icon-button offers-filter-icon"
      :aria-label="toggleLabel"
      :aria-expanded="open"
      data-test="sent-filters-toggle"
      @click="open = true"
    >
      <AppIcon name="settings" />
      <CountBadge
        v-if="active"
        aria-hidden="true"
        :count="active"
      />
    </button>
  </Teleport>
  <BottomSheet
    :open="open"
    title="Filtres des envoyées"
    size="large"
    class="filters-dialog"
    data-test="sent-filters-sheet"
    @close="open = false"
  >
    <div class="filter-sheet">
      <div class="filter-choices">
        <h3 id="sent-sheet-status">
          Statut
        </h3>
        <div
          class="filter-choices-row"
          role="radiogroup"
          aria-labelledby="sent-sheet-status"
          @keydown="radioKey"
        >
          <button
            v-for="choice in shown"
            :key="choice.value"
            type="button"
            class="filter-choice"
            role="radio"
            :aria-checked="filter === choice.value"
            :tabindex="filter === choice.value ? 0 : -1"
            :data-test="`sent-status-${choice.value}`"
            @click="emit('update:filter', choice.value)"
          >
            <AppIcon
              v-if="filter === choice.value"
              name="tick"
            />{{ choice.label }} · {{ counts[choice.value] }}
          </button>
        </div>
      </div>
      <div class="filter-choices">
        <h3 id="sent-sheet-sort">
          Trier
        </h3>
        <div
          class="filter-choices-row"
          role="radiogroup"
          aria-labelledby="sent-sheet-sort"
          @keydown="radioKey"
        >
          <button
            v-for="choice in SORTS"
            :key="choice.value"
            type="button"
            class="filter-choice"
            role="radio"
            :aria-checked="sort === choice.value"
            :tabindex="sort === choice.value ? 0 : -1"
            :data-test="choice.test"
            @click="emit('update:sort', choice.value)"
          >
            <AppIcon
              v-if="sort === choice.value"
              name="tick"
            />{{ choice.label }}
          </button>
        </div>
      </div>
    </div>
    <template #actions>
      <button
        type="button"
        class="link filters-clear"
        data-test="sent-sheet-reset"
        @click="emit('reset')"
      >
        Tout effacer
      </button>
      <button
        type="button"
        class="primary filters-show"
        data-test="sent-sheet-show"
        @click="open = false"
      >
        {{ showLabel }}
      </button>
    </template>
  </BottomSheet>
</template>

<style scoped>
/* Visuel refait d'après la planche FiltresEnvoyees du 18.11 (Kevin, 18.11, 10 h 48) :
   - « Statut » et « Trier » en 15/700 couleur du texte, comme sur Filtres (règle commune de .filter-choices h3) ;
   - 22 px entre les groupes, 10 px entre un titre et ses pastilles ;
   - pastilles de 44 px, trait de 1,5 px (--card-line, la choisie en bleu), 14/600 ;
   - en bas, « Tout effacer » à gauche et « Afficher N candidatures » qui prend la place qui reste, 52 px, en pilule,
     sous un trait, comme sur Filtres. */
.filter-sheet { gap: var(--sent-filters-gap, 22px); }
.filter-sheet .filter-choices { gap: var(--sent-filters-label-gap, 10px); }
.filter-sheet .filter-choice { border-width: 1.5px; font-size: var(--font-small); font-weight: var(--weight-semibold); }
.filter-sheet .filter-choice:not([aria-checked="true"]) { border-color: var(--card-line); }
.filters-dialog :deep(.sheet-actions) { gap: var(--space-3); margin: 0; padding: var(--sent-actions-top, 14px) var(--space-5) 0; border-top: 1px solid var(--line); }
.filters-clear { min-height: var(--sent-52, 52px); padding: 0 var(--space-5); font-size: var(--font-body); font-weight: var(--weight-bold); }
.filters-show { flex: 1 1 0; min-width: 0; padding: 0 var(--space-2); white-space: nowrap; min-height: var(--sent-52, 52px); justify-content: center; border-radius: var(--radius-pill); font-size: var(--font-body); font-weight: var(--weight-bold); }
</style>
