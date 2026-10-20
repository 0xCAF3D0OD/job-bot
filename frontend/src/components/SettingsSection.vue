<script lang="ts">
import type { IconName } from "../icons";

// Une petite icône au trait devant le titre, de la famille de la navigation (docs/62 §1) ;
// plus d'illustration dans un formulaire. Le sommaire des Réglages reprend les mêmes (docs/101).
export const SETTINGS_ICONS: Record<string, IconName> = {
  recherche: "search",
  rythme: "clock",
  actualites: "news",
  notifications: "bell",
  ia: "spark",
  compte: "shield",
  outils: "plug",
  plateforme: "user",
};
</script>

<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";

import { usePhone } from "../composables/usePhone";
import DisclosureRow from "./DisclosureRow.vue";
import AppIcon from "./AppIcon.vue";

// Section des Réglages (docs/34 §3) : sur ordinateur, le titre et son contenu comme avant ;
// sur téléphone, une ligne dépliable avec un résumé, une seule ouverte à la fois. Un lien
// « /reglages#actualites » ouvre directement la bonne ligne.
// Sur ordinateur, une rubrique à la fois (docs/48 §2) : seule la rubrique active s'affiche.
const props = withDefaults(defineProps<{ id: string; title: string; value?: string; active?: boolean }>(), {
  value: "",
  active: true,
});
const { phone } = usePhone();
const route = useRoute();
// « /reglages?rubrique=actualites » (docs/48) ou l'ancien « #actualites » : la ligne s'ouvre.
const targeted = computed(() => route.query.rubrique === props.id || route.hash === `#${props.id}`);
</script>

<template>
  <DisclosureRow
    v-if="phone"
    :id="id"
    :key="route.fullPath"
    :title="title"
    :value="value"
    group="settings"
    :start-open="targeted"
    class="settings-row"
  >
    <slot />
  </DisclosureRow>
  <template v-else-if="active">
    <h2
      :id="id"
      class="section-title"
    >
      <AppIcon
        v-if="SETTINGS_ICONS[id]"
        :name="SETTINGS_ICONS[id]!"
      />
      {{ title }}
    </h2>
    <!-- Une rubrique, une carte (docs/106 §1) : les cartes du contenu y perdent leur cadre. -->
    <div
      class="settings-card"
      data-test="settings-card"
    >
      <slot />
    </div>
  </template>
</template>
