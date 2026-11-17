<script setup lang="ts">
import { computed, ref, watch } from "vue";

import type { AlertsPage } from "../api/client";
import {
  combinations,
  limitMessage,
  loadSearchCriteria,
  MAX_ROLES,
  MAX_SEARCHES,
  RATES,
  rateLabel,
  saveSearchCriteria,
  searchPlace,
  type SavedSearches,
} from "../searchCriteria";
import AppIcon from "./AppIcon.vue";
import IconButton from "./IconButton.vue";
import LoadingBlocks from "./LoadingBlocks.vue";
import SidePanel from "./SidePanel.vue";

// Le volet « Ta recherche » (« Modifier » de la carte des Alertes, Kevin 17.11) : les critères du Profil, avec les
// éléments des premiers pas en attendant sa planche. Postes en pastilles à choix multiple (3 au plus) et « + Autre
// poste », lieux (champ « Ville ou région » et pastilles, « Toute la Suisse » sans lieu), taux en choix unique. Au-delà
// de 8 recherches, « Enregistrer » est désactivé et la pastille orange le dit (aria-describedby, Kevin 17.11, 14 h 27).
const props = defineProps<{ open: boolean; page: AlertsPage }>();
const emit = defineEmits<{ close: []; saved: [result: SavedSearches] }>();

const roles = ref<string[]>([]);
const picked = ref<string[]>([]);
const places = ref<string[]>([]);
const rate = ref<number | null>(null);
const loaded = ref(false);
const failed = ref(false);
const busy = ref(false);
const newRole = ref("");
const adding = ref(false);
const newPlace = ref("");

watch(
  () => props.open,
  async (open) => {
    if (!open) return;
    loaded.value = false;
    failed.value = false;
    const criteria = await loadSearchCriteria(props.page);
    if (criteria) {
      roles.value = [...criteria.roles];
      picked.value = criteria.roles.slice(0, MAX_ROLES);
      places.value = [...criteria.places];
      rate.value = criteria.rate;
    }
    failed.value = !criteria;
    loaded.value = true;
  },
  { immediate: true },
);

const count = computed(() => combinations({ roles: picked.value, places: places.value }).length);
const tooMany = computed(() => count.value > MAX_SEARCHES);

function toggle(role: string): void {
  if (picked.value.includes(role)) picked.value = picked.value.filter((r) => r !== role);
  else if (picked.value.length < MAX_ROLES) picked.value = [...picked.value, role];
}
function addRole(): void {
  const role = newRole.value.trim().slice(0, 80);
  newRole.value = "";
  if (!role) return;
  const same = roles.value.find((r) => r.toLowerCase() === role.toLowerCase());
  if (!same) roles.value = [...roles.value, role];
  const name = same ?? role;
  if (!picked.value.includes(name) && picked.value.length < MAX_ROLES) picked.value = [...picked.value, name];
}
function addPlace(): void {
  for (const part of newPlace.value.split(",")) {
    const place = part.trim();
    if (place && !places.value.some((p) => searchPlace(p).toLowerCase() === searchPlace(place).toLowerCase()))
      places.value = [...places.value, place];
  }
  newPlace.value = "";
}

async function save(): Promise<void> {
  if (newRole.value.trim()) addRole();
  if (newPlace.value.trim()) addPlace();
  if (tooMany.value || busy.value) return;
  busy.value = true;
  failed.value = false;
  try {
    const result = await saveSearchCriteria({ roles: picked.value, places: places.value, rate: rate.value }, props.page);
    if (result) emit("saved", result);
    else failed.value = true;
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <SidePanel
    :open="open"
    title="Ta recherche"
    panel-class="alerts-search-panel"
    @close="emit('close')"
  >
    <LoadingBlocks
      v-if="!loaded"
      :heights="['6rem', '5rem', '4rem']"
    />
    <form
      v-else
      class="alerts-search-form"
      data-test="search-panel-form"
      @submit.prevent="save"
    >
      <fieldset>
        <legend class="sheet-group-title">
          Postes
        </legend>
        <p class="alerts-search-note">
          Trois postes au plus.
        </p>
        <div
          class="filter-choices-row"
          data-test="search-panel-roles"
        >
          <button
            v-for="role in roles"
            :key="role"
            type="button"
            class="filter-choice"
            :aria-pressed="picked.includes(role)"
            :aria-disabled="!picked.includes(role) && picked.length >= MAX_ROLES ? 'true' : undefined"
            :aria-describedby="tooMany ? 'search-panel-limit' : undefined"
            @click="toggle(role)"
          >
            <AppIcon
              v-if="picked.includes(role)"
              name="tick"
            />{{ role }}
          </button>
          <button
            v-if="!adding"
            type="button"
            class="filter-choice"
            data-test="search-panel-other"
            @click="adding = true"
          >
            + Autre poste
          </button>
        </div>
        <div
          v-if="adding"
          class="tag-add"
        >
          <input
            v-model="newRole"
            type="text"
            maxlength="80"
            aria-label="Autre poste"
            placeholder="Autre poste"
            data-test="search-panel-role-input"
            @keydown.enter.prevent="addRole"
          >
          <IconButton
            icon="plus"
            label="Ajouter le poste"
            @click="addRole"
          />
        </div>
      </fieldset>

      <fieldset>
        <legend class="sheet-group-title">
          Lieux
        </legend>
        <div class="tag-add">
          <input
            v-model="newPlace"
            type="text"
            maxlength="80"
            aria-label="Ville ou région"
            placeholder="Ville ou région"
            data-test="search-panel-place-input"
            @keydown.enter.prevent="addPlace"
          >
          <IconButton
            icon="plus"
            label="Ajouter le lieu"
            @click="addPlace"
          />
        </div>
        <ul
          class="tags"
          data-test="search-panel-places"
        >
          <li
            v-for="place in places"
            :key="place"
            class="tag"
          >
            {{ searchPlace(place) }}
            <IconButton
              icon="close"
              class="chip-remove"
              :label="`Retirer ${searchPlace(place)}`"
              @click="places = places.filter((p) => p !== place)"
            />
          </li>
        </ul>
        <!-- « Toute la Suisse » remplace tous les autres lieux (Kevin, 17.11, 14 h 27). -->
        <div class="filter-choices-row">
          <button
            type="button"
            class="filter-choice"
            :aria-pressed="!places.length"
            data-test="search-panel-everywhere"
            @click="places = []"
          >
            <AppIcon
              v-if="!places.length"
              name="tick"
            />Toute la Suisse
          </button>
        </div>
      </fieldset>

      <fieldset>
        <legend class="sheet-group-title">
          Taux d’activité
        </legend>
        <div
          class="filter-choices-row"
          role="radiogroup"
          aria-label="Taux d’activité"
        >
          <button
            v-for="value in RATES"
            :key="String(value)"
            type="button"
            class="filter-choice"
            role="radio"
            :aria-checked="rate === value"
            :data-test="`search-panel-rate-${value ?? 'tous'}`"
            @click="rate = value"
          >
            <AppIcon
              v-if="rate === value"
              name="tick"
            />{{ rateLabel(value) }}
          </button>
        </div>
      </fieldset>

      <p
        v-if="tooMany"
        id="search-panel-limit"
        class="alerts-search-limit"
        role="status"
        data-test="search-panel-limit"
      >
        {{ limitMessage(count) }}
      </p>
      <p
        v-if="failed"
        class="notice error"
        role="alert"
      >
        Enregistrement refusé : réessaie.
      </p>
      <!-- L'encadré d'information (style de la section 62 du 17.11). -->
      <p class="alerts-search-info">
        <AppIcon name="info" />Ces critères servent aussi à trier tes offres.
      </p>
    </form>
    <template #footer>
      <button
        type="button"
        class="alert-site-later"
        data-test="search-panel-cancel"
        @click="emit('close')"
      >
        Annuler
      </button>
      <button
        type="button"
        class="action-1 alert-site-done"
        :disabled="!loaded || tooMany || busy"
        :aria-describedby="tooMany ? 'search-panel-limit' : undefined"
        data-test="search-panel-save"
        @click="save"
      >
        Enregistrer
      </button>
    </template>
  </SidePanel>
</template>

<style>
/* Le volet « Ta recherche » : le pied comme celui du volet d'un site ; l'encadré d'information de la section 62
   (fond des cartes, le volet ayant celui de la page ; rayon 14, icône i). */
.alerts-search-form { display: flex; flex-direction: column; gap: var(--space-6); }
.alerts-search-form fieldset { display: flex; flex-direction: column; gap: var(--space-3); min-width: 0; margin: 0; padding: 0; border: 0; }
.alerts-search-note { margin: 0; font-size: var(--font-small); color: var(--text-secondary); }
.alerts-search-panel .side-panel-foot { justify-content: flex-end; gap: var(--space-6); }
.alerts-search-limit { align-self: flex-start; margin: 0; padding: var(--space-1) var(--space-3); border-radius: var(--radius-pill); background: var(--limit-soft); color: var(--peach-text); font-size: var(--font-small); font-weight: var(--weight-semibold); line-height: var(--space-5); }
.alerts-search-info { display: flex; gap: var(--space-3); margin: 0; padding: var(--space-3) var(--space-4); border-radius: calc(var(--space-3) + var(--space-1) / 2); background: var(--surface); font-size: var(--font-small); line-height: var(--space-5); }
.alerts-search-info .icon { flex: none; width: 20px; height: 20px; color: var(--primary-graphic); }
</style>
