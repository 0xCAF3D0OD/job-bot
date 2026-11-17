<script setup lang="ts">
import { defineAsyncComponent, onMounted, ref, watch } from "vue";

import { useAssistant, useAssistantPlace } from "../composables/useAssistant";
import AssistantMascot from "./AssistantMascot.vue";

// Le bouton flottant de l'Assistant, sur toutes les pages ; le panneau (AssistantPanel, environ 10 Ko gzip) ne se
// télécharge qu'à la première ouverture : bouton, question posée d'ailleurs ou page Assistant du téléphone
// (allègement du 17.11, choix de Kevin). Le bouton est le même que celui du panneau, qui prend le relais une fois chargé ;
// pendant le chargement, il reste affiché, pour que le focus y revienne à la fermeture.
const AssistantPanel = defineAsyncComponent(() => import("./AssistantPanel.vue"));

const { available, open, check } = useAssistant();
const { page, quiet, fabHidden } = useAssistantPlace();
// Demandé une fois, le panneau reste là : la discussion se garde quand on le ferme ou qu'on change de page.
const wanted = ref(false);
const ready = ref(false);
watch([open, page], ([isOpen, isPage]) => {
  if (isOpen || isPage) wanted.value = true;
}, { immediate: true });
onMounted(() => void check());
</script>

<template>
  <template v-if="available">
    <button
      v-if="!ready && !page && !quiet && !fabHidden"
      type="button"
      class="assistant-fab"
      aria-label="Ouvrir l’assistant"
      data-test="assistant-open"
      @click="open = true"
    >
      <AssistantMascot :size="28" />
      <span class="assistant-fab-label">Assistant</span>
    </button>
    <AssistantPanel
      v-if="wanted"
      @ready="ready = true"
    />
  </template>
</template>
