<script setup lang="ts">
import { computed } from "vue";

import AppIcon from "./AppIcon.vue";
import OfferSearch from "./OfferSearch.vue";
import { SENT_FILTERS, SENT_SORTS, type SentFilter, type SentSort } from "../sentFilters";

// Le filtre des Envoyées (paquet du 11 novembre, PR 39) : la même recherche que l'onglet Offres (« Filtrer par titre
// ou entreprise »), le tri, puis les statuts avec leur nombre. Un statut à 0 est masqué (sauf celui qui est choisi,
// pour pouvoir le quitter). Ordinateur : pastilles de 36 px sur une ligne ; téléphone : 44 px, la ligne défile.
// Ordinateur (maquette du 14 novembre, §3 et §6, avec `panel`) : la rangée d’Offres, le champ et « Plus de filtres »,
// qui ouvre le volet Filtres (statuts et tri). Plus de « Trier » ni de pastilles ici.
const props = defineProps<{ words: string; filter: SentFilter; sort: SentSort; counts: Record<SentFilter, number>; panel?: boolean; open?: boolean }>();
const emit = defineEmits<{ "update:words": [value: string]; "update:filter": [value: SentFilter]; "update:sort": [value: SentSort]; open: [] }>();
// Statut et tri différents de ceux par défaut : le nombre en pastille et dans le nom du bouton.
const active = computed(() => Number(props.filter !== "toutes") + Number(props.sort !== "relancer"));

const shown = computed(() => SENT_FILTERS.filter((f) => f.value === "toutes" || props.counts[f.value] > 0 || f.value === props.filter));
</script>

<template>
  <div
    class="sent-filters"
    data-test="sent-filters"
  >
    <div class="sent-filters-row">
      <OfferSearch
        :value="words"
        icon="filter"
        placeholder="Filtrer par titre ou entreprise"
        @search="emit('update:words', $event)"
      />
      <button
        v-if="panel"
        type="button"
        class="secondary offers-toolbar-button sent-more"
        :aria-label="active ? `Plus de filtres, ${active} ${active > 1 ? 'filtres actifs' : 'filtre actif'}` : undefined"
        :aria-expanded="open"
        aria-controls="sent-filters-panel"
        data-test="sent-filters-open"
        @click="emit('open')"
      >
        <span class="with-icon"><AppIcon name="settings" />Plus de filtres</span><span
          v-if="active"
          class="count-badge"
          aria-hidden="true"
        >{{ active }}</span>
      </button>
      <select
        v-else
        class="field-compact sent-sort"
        aria-label="Trier"
        :value="sort"
        data-test="sent-sort"
        @change="emit('update:sort', ($event.target as HTMLSelectElement).value as SentSort)"
      >
        <option
          v-for="choice in SENT_SORTS"
          :key="choice.value"
          :value="choice.value"
        >
          {{ choice.label }}
        </option>
      </select>
    </div>
    <div
      v-if="!panel"
      class="sent-pills"
      role="group"
      aria-label="Statut"
    >
      <button
        v-for="choice in shown"
        :key="choice.value"
        type="button"
        class="sent-pill"
        :aria-pressed="filter === choice.value"
        :data-test="`sent-status-${choice.value}`"
        @click="emit('update:filter', choice.value)"
      >
        {{ choice.label }}<span class="sent-pill-count">{{ counts[choice.value] }}</span>
      </button>
    </div>
  </div>
</template>

<style>
/* Sorti de style.css (allègement du 16.11, issue #797) : ces règles ne servent qu'ici, chargées avec ce composant. */
@media (min-width: 1024px) {
.linked-list > .sent-tools > .sent-filters { margin-bottom: var(--space-1); }
}
</style>

<style scoped>
.sent-filters { --pill-36: 36px; --pill-13: 13px; display: grid; gap: var(--space-3); margin-bottom: var(--space-4); }
.sent-filters-row { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: var(--space-2); }
.sent-filters-row :deep(.filters-search) { height: var(--target-min); padding-block: 0; padding-left: calc(var(--space-8) + var(--space-3)); border-color: var(--line); border-radius: var(--radius-pill); background-color: var(--surface); }
.sent-filters-row :deep(.filters-search-wrap .icon) { left: var(--space-4); }
.sent-more { min-height: var(--target-min); padding: 0 var(--space-4); border: 1.5px solid var(--button-outline); border-radius: var(--radius-pill); background: var(--surface); color: var(--text); font-size: var(--font-label); font-weight: var(--weight-bold); }
.sent-sort { height: var(--target-min); min-height: var(--target-min); border-color: var(--line); font-weight: var(--weight-semibold); }
.sent-pills { display: flex; gap: var(--space-2); overflow-x: auto; scrollbar-width: none; }
.sent-pill { display: inline-flex; flex: none; align-items: center; gap: var(--space-2); min-height: var(--pill-36); padding: 0 var(--space-3); border: 1px solid var(--line); border-radius: var(--radius-pill); background: var(--surface); color: var(--text); font-size: var(--pill-13); font-weight: var(--weight-semibold); white-space: nowrap; }
.sent-pill[aria-pressed="true"] { border-color: var(--accent); background: var(--primary-soft); color: var(--accent-strong); }
.sent-pill-count { color: var(--muted); font-weight: var(--weight-regular); }
.sent-pill[aria-pressed="true"] .sent-pill-count { color: inherit; }
@media (max-width: 820px) {
  .sent-filters-row { grid-template-columns: minmax(0, 1fr); }
  .sent-pills { margin-inline: calc(-1 * var(--space-4)); padding-inline: var(--space-4); }
  .sent-pill { min-height: var(--target-min); padding-inline: var(--space-4); }
}
</style>
