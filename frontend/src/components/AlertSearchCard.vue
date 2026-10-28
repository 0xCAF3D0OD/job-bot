<script setup lang="ts">
import { computed } from "vue";

import type { SearchGroup, SiteState } from "../alertsState";
import MoreMenu, { type MoreMenuItem } from "./MoreMenu.vue";
import SettingCard from "./SettingCard.vue";
import SettingRow from "./SettingRow.vue";
import StatusPill from "./StatusPill.vue";

// Une recherche (planche « 6. Alertes ») : une carte, la ligne d'en-tête (les mots, les lieux, l'état
// en pastille), puis une ligne par site avec son état ; « Créer » ouvre le pas à pas sur ce site.
// La pastille et le mot disent l'état (WCAG 1.4.1, StatusPill) ; l'orange est réservé à ce qui demande
// une action (§4) ; « rien depuis N jours » reste une mention grise.
// Le ton de la pastille (§4) : reçue = réussi ; rien reçu depuis la création ou à créer = à faire
// (une action, la bande le dit) ; en attente, en pause = neutre.
type Tone = "neutral" | "todo" | "ok";
const SEARCH_TONE: Record<SearchGroup["pill"]["kind"], Tone> = { received: "ok", waiting: "neutral", todo: "todo", paused: "neutral" };
const SITE_TONE: Record<SiteState["kind"], Tone> = { received: "ok", quiet: "neutral", waiting: "neutral", silent: "todo", todo: "todo" };

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
      inline
    >
      <StatusPill
        :tone="SEARCH_TONE[group.pill.kind]"
        data-test="search-state"
      >
        {{ group.pill.label }}
      </StatusPill>
      <MoreMenu
        :items="menu"
        :label="`Plus d'actions sur la recherche « ${group.terms} »`"
        :test-id="`search-more-${group.ids[0]}`"
      />
    </SettingRow>
    <SettingRow
      v-for="site in group.sites"
      :key="site.slug"
      :title="site.name"
      class="alert-site"
      inline
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
      <StatusPill
        v-else
        :tone="SITE_TONE[site.state.kind]"
      >
        {{ site.state.label }}
      </StatusPill>
    </SettingRow>
  </SettingCard>
</template>
