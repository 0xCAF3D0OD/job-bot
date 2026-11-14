<script setup lang="ts">
import { computed, ref } from "vue";

import AppIcon from "./AppIcon.vue";
import BottomSheet from "./BottomSheet.vue";
import CountBadge from "./CountBadge.vue";
import OfferSearch from "./OfferSearch.vue";
import { plural } from "../format";
import { SENT_FILTERS, type SentFilter, type SentSort } from "../sentFilters";

// Les filtres des Envoyées sur téléphone (maquette du 14 novembre, Envoyees, §3 et §6 de docs/design/regles.md) :
// - le champ « Poste, entreprise, lieu » sous l'en-tête Candidatures, au-dessus des onglets (#jobs-tools), à la même
//   place que sur Offres ; lu « Rechercher une candidature » (décision de Kevin du 14.11) ;
// - l'icône Filtres dans l'en-tête, à côté d'« Alertes », qui ouvre la feuille Filtres ;
// - dans la feuille : les statuts (avant en puces sous la recherche) et le tri, « À relancer d'abord » par défaut ou
//   « Plus récentes d'abord » (décision de Kevin du 14.11) ; « Tout effacer » et « Afficher N candidatures » en bas.
// La logique (mots, statut et tri gardés dans l'adresse) reste dans ApplicationsView.
const props = defineProps<{ words: string; filter: SentFilter; sort: SentSort; counts: Record<SentFilter, number>; total: number }>();
const emit = defineEmits<{ "update:words": [value: string]; "update:filter": [value: SentFilter]; "update:sort": [value: SentSort]; reset: [] }>();

const open = ref(false);
// Un statut à 0 est masqué, sauf celui qui est choisi (pour pouvoir le quitter), comme sur ordinateur.
const shown = computed(() => SENT_FILTERS.filter((f) => f.value === "toutes" || props.counts[f.value] > 0 || f.value === props.filter));
const SORTS: { value: SentSort; label: string }[] = [
  { value: "relancer", label: "À relancer d’abord" },
  { value: "recentes", label: "Plus récentes d’abord" },
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
    title="Filtres"
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
          role="group"
          aria-labelledby="sent-sheet-status"
        >
          <button
            v-for="choice in shown"
            :key="choice.value"
            type="button"
            class="filter-choice"
            :aria-pressed="filter === choice.value"
            :data-test="`sent-status-${choice.value}`"
            @click="emit('update:filter', choice.value)"
          >
            {{ choice.label }} · {{ counts[choice.value] }}
          </button>
        </div>
      </div>
      <div class="filter-choices">
        <h3 id="sent-sheet-sort">
          Trier
        </h3>
        <div
          class="filter-choices-row"
          role="group"
          aria-labelledby="sent-sheet-sort"
        >
          <button
            v-for="choice in SORTS"
            :key="choice.value"
            type="button"
            class="filter-choice"
            :aria-pressed="sort === choice.value"
            :data-test="`sent-sort-${choice.value}`"
            @click="emit('update:sort', choice.value)"
          >
            {{ choice.label }}
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
/* §4 du 14 novembre (feuilles) : libellés de section en capitales 13/700 gris, espacement .05em ; en bas, « Tout effacer »
   et le bouton alignés à droite, 24 px entre eux, le bouton en pilule de 52 px à la largeur de son texte. */
/* Le champ de la planche Envoyees : 48 px, coins de 14, bord --line, fond blanc, loupe à 14 px, texte 16. */
.sent-phone-search { --sent-14: 14px; --sent-icon: 20px; --sent-gap: 10px; display: block; }
.sent-phone-search :deep(.filters-search) { box-sizing: border-box; height: var(--field-h); padding: 0 var(--sent-14) 0 calc(var(--sent-14) + var(--sent-icon) + var(--sent-gap)); border: 1px solid var(--line); border-radius: var(--sent-14); background-color: var(--surface); font-size: var(--font-body); }
.sent-phone-search :deep(.icon) { left: var(--sent-14); width: var(--sent-icon); height: var(--sent-icon); color: var(--text-secondary); }
.filters-dialog { max-height: calc(100dvh - 9.625rem); }
.filter-sheet .filter-choices h3 { font-size: var(--panel-caps-size, 13px); font-weight: var(--weight-bold); letter-spacing: .05em; text-transform: uppercase; color: var(--text-secondary); }
.filters-dialog :deep(.sheet-actions) { justify-content: flex-end; gap: var(--space-6); margin: 0 calc(var(--sheet-pad) * -1); padding: var(--space-3) var(--space-5) 0 var(--sheet-pad); border-top: 1px solid var(--line); }
.filters-dialog :deep(.sheet-actions > .primary) { flex: none; }
.filters-clear { min-height: var(--target-min); padding: 0; font-size: var(--font-body); font-weight: var(--weight-bold); }
.filters-show { --sent-52: 52px; min-height: var(--sent-52); padding: 0 var(--space-6); border-radius: var(--radius-pill); font-size: var(--font-body); font-weight: var(--weight-bold); }
</style>
