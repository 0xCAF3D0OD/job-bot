<script setup lang="ts">
import { computed } from "vue";

import { PAGE_TRANSITIONS, pageTransition } from "../composables/usePageTransition";
import FaceState from "./FaceState.vue";

// La transition d'une page qui charge (docs/61 §2) : l'écran grisé, le visage du 1 au centre,
// l'œil et la bille qui pulsent (docs/123 §2, T), et le nom de la page dessous ; elle s'efface
// quand les données sont là.
const shown = computed(() => (pageTransition.shown && pageTransition.page ? PAGE_TRANSITIONS[pageTransition.page] : null));
</script>

<template>
  <Transition name="page-veil">
    <div
      v-if="shown"
      class="page-veil"
      role="status"
      aria-live="polite"
      data-test="page-transition"
    >
      <FaceState
        :title="shown.label"
        heading="p"
        waiting
      />
    </div>
  </Transition>
</template>
