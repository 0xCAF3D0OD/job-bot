<script setup lang="ts">
import { computed } from "vue";

import { PAGE_TRANSITIONS, pageTransition } from "../composables/usePageTransition";
import { usePhone } from "../composables/usePhone";
import FaceState from "./FaceState.vue";
import FaceTransform from "./FaceTransform.vue";

// La transition d'une page qui charge (docs/61 §2) : l'écran grisé, le visage du 1 au centre,
// qui prend l'objet de la page (docs/123, complément 0.96.0) ou, sinon, dont l'œil et la bille
// pulsent (docs/123 §2, T), et le nom de la page dessous ; elle s'efface quand les données
// sont là.
// Téléphone (D9) : le feston d'attente seul, sans visage transformé.
const { phone } = usePhone();
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
      <div
        v-if="shown.face && !phone"
        class="face-state"
      >
        <FaceTransform :kind="shown.face" />
        <p class="face-state-title">
          {{ shown.label }}
        </p>
      </div>
      <FaceState
        v-else
        :title="shown.label"
        heading="p"
        waiting
        :animation="phone ? 'attente' : undefined"
      />
    </div>
  </Transition>
</template>
