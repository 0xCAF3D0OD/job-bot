<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";

import { usePhone } from "../composables/usePhone";
import DisclosureRow from "./DisclosureRow.vue";
import IllustratedSide from "./IllustratedSide.vue";
import type { IllustrationName } from "./Illustration.vue";

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
// Sur ordinateur, le formulaire garde une largeur de lecture, son image à droite (docs/61 §3).
const ILLUSTRATIONS: Record<string, IllustrationName> = {
  recherche: "stepping-up",
  actualites: "newsfeed",
  notifications: "lock-screen-notifications",
  ia: "artificial-intelligence",
  compte: "security-on",
  outils: "online-connection",
};
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
      {{ title }}
    </h2>
    <IllustratedSide
      v-if="ILLUSTRATIONS[id]"
      :name="ILLUSTRATIONS[id]!"
      side="right"
    >
      <div class="settings-side-body">
        <slot />
      </div>
    </IllustratedSide>
    <slot v-else />
  </template>
</template>
