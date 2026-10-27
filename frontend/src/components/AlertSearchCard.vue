<script setup lang="ts">
import { computed } from "vue";

import type { SearchGroup } from "../alertsState";
import MoreMenu, { type MoreMenuItem } from "./MoreMenu.vue";
import SettingCard from "./SettingCard.vue";
import SettingRow from "./SettingRow.vue";

// Une recherche (planche « 6. Alertes ») : une carte, la ligne d'en-tête (les mots, les lieux, l'état
// en pastille), puis une ligne par site avec son état ; « Créer » ouvre le pas à pas sur ce site.
// La pastille et le mot disent l'état (WCAG 1.4.1) ; l'orange est réservé à ce qui demande une action
// (§4) ; « rien depuis N jours » reste une mention grise.
const props = defineProps<{ group: SearchGroup }>();
const emit = defineEmits<{ create: [site: string]; manage: []; remove: [] }>();

const menu = computed<MoreMenuItem[]>(() => [
  { label: "Modifier", test: "search-manage", icon: "pencil", run: () => emit("manage") },
  { label: "Supprimer", test: "search-remove", icon: "trash", danger: true, run: () => emit("remove") },
]);
</script>

<template>
  <SettingCard
    class="alert-search"
    :data-test="`alert-search-${props.group.ids[0]}`"
  >
    <SettingRow
      :title="group.terms"
      :description="group.locations.join(', ') || 'Toute la Suisse'"
      class="alert-search-head"
    >
      <span
        :class="['alert-state', group.pill.kind]"
        data-test="search-state"
      >{{ group.pill.label }}</span>
      <MoreMenu
        :items="menu"
        :label="`Actions pour « ${group.terms} »`"
        :test-id="`search-more-${group.ids[0]}`"
      />
    </SettingRow>
    <SettingRow
      v-for="site in group.sites"
      :key="site.slug"
      :title="site.name"
      class="alert-site"
      :data-test="`site-${site.slug}`"
    >
      <button
        v-if="site.state.kind === 'todo'"
        type="button"
        class="secondary small"
        :aria-label="`Créer l'alerte « ${group.terms} » sur ${site.name}`"
        :data-test="`create-${site.slug}`"
        @click="emit('create', site.slug)"
      >
        Créer
      </button>
      <span
        v-else-if="site.state.kind === 'quiet'"
        class="alert-quiet"
      >{{ site.state.label }}</span>
      <span
        v-else
        :class="['alert-state', site.state.kind]"
      >{{ site.state.label }}</span>
    </SettingRow>
  </SettingCard>
</template>
