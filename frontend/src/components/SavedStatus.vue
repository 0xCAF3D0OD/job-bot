<script setup lang="ts">
import { onUnmounted, ref, watch } from "vue";

import AppIcon from "./AppIcon.vue";

// « Enregistré » après une case qui s'enregistre tout de suite (planche « Champs », comme les Réglages) :
// visible 3 s et annoncé aux lecteurs d'écran (message d'état, WCAG 4.1.3). La zone role="status"
// est toujours là, pour que l'annonce parte. `at` : l'heure du dernier enregistrement réussi.
const props = defineProps<{ at: number }>();
const SHOWN_MS = 3000;
const shown = ref(false);
let timer: ReturnType<typeof setTimeout> | undefined;
watch(
  () => props.at,
  (at) => {
    if (!at) return;
    shown.value = true;
    clearTimeout(timer);
    timer = setTimeout(() => (shown.value = false), SHOWN_MS);
  },
);
onUnmounted(() => clearTimeout(timer));
</script>

<template>
  <span
    class="saved-status"
    role="status"
    data-test="saved-status"
  ><template v-if="shown"><AppIcon name="done" />Enregistré</template></span>
</template>
