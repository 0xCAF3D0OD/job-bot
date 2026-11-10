<script setup lang="ts">
import { computed } from "vue";

import { PAGE_TRANSITIONS, pageTransition } from "../composables/usePageTransition";
import { usePhone } from "../composables/usePhone";
import FaceTransform from "./FaceTransform.vue";
import TroupeLoader from "./TroupeLoader.vue";

// La transition d'une page qui charge (docs/61 §2) : l'écran grisé, le visage du 1 au centre,
// qui prend l'objet de la page (docs/123, complément 0.96.0) et le nom de la page dessous ; elle
// s'efface quand les données sont là.
// Sur téléphone, et pour une page sans objet : les 4 morceaux du logo qui sautent l'un après l'autre
// (TroupeLoader, §15 du 9 novembre), de 1 à 10 s.
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
      <TroupeLoader
        v-else
        :label="shown.label"
        :delay="0"
      />
    </div>
  </Transition>
</template>
