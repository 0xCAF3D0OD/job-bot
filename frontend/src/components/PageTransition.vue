<script setup lang="ts">
import { computed } from "vue";

import { PAGE_TRANSITIONS, pageTransition } from "../composables/usePageTransition";
import Illustration from "./Illustration.vue";

// La transition d'une page qui charge (docs/61 §2) : l'écran grisé, l'illustration de la page au
// centre et son nom dessous ; elle s'efface quand les données sont là.
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
      <Illustration
        :key="shown.illustration"
        :name="shown.illustration"
      />
      <p>{{ shown.label }}</p>
    </div>
  </Transition>
</template>
