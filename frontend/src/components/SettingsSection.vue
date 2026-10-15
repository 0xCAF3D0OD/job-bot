<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";

import { usePhone } from "../composables/usePhone";
import DisclosureRow from "./DisclosureRow.vue";

// Section des Réglages (docs/34 §3) : sur ordinateur, le titre et son contenu comme avant ;
// sur téléphone, une ligne dépliable avec un résumé, une seule ouverte à la fois. Un lien
// « /reglages#actualites » ouvre directement la bonne ligne.
const props = withDefaults(defineProps<{ id: string; title: string; value?: string }>(), { value: "" });
const { phone } = usePhone();
const route = useRoute();
const targeted = computed(() => route.hash === `#${props.id}`);
</script>

<template>
  <DisclosureRow
    v-if="phone"
    :id="id"
    :key="route.hash"
    :title="title"
    :value="value"
    group="settings"
    :start-open="targeted"
    class="settings-row"
  >
    <slot />
  </DisclosureRow>
  <template v-else>
    <h2
      :id="id"
      class="section-title"
    >
      {{ title }}
    </h2>
    <slot />
  </template>
</template>
