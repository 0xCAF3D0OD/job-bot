<script setup lang="ts">
import { computed } from "vue";

import { MASCOT_EYE, MASCOT_FACE, MASCOT_SMILE, MASCOT_STAR, MASCOT_STAR_SMALL_SIZE } from "../brandPaths";

// La mascotte de l'assistant (docs/97) : le visage plein, l'œil fermé, l'étoile, le sourire.
// Les traits et l'étoile s'épaississent aux petites tailles, aux paliers de la planche.
// Décorative : « Assistant » à côté dit ce que c'est.
const props = withDefaults(defineProps<{ size?: number }>(), { size: 28 });
const widths = computed(() => {
  if (props.size >= 100) return { eye: 4.42, smile: 3.74 };
  if (props.size >= 40) return { eye: 5.85, smile: 4.95 };
  if (props.size >= 24) return { eye: 7.2, smile: 6.6 };
  return { eye: 10.8, smile: 9.9 };
});
const star = computed(() => (props.size >= 40 ? MASCOT_STAR : MASCOT_STAR_SMALL_SIZE));
</script>

<template>
  <svg
    class="assistant-mascot"
    :width="size"
    :height="size"
    viewBox="0 0 100 100"
    aria-hidden="true"
    data-test="assistant-mascot"
  >
    <path
      :d="MASCOT_FACE"
      class="mascot-face"
    />
    <path
      :d="MASCOT_EYE"
      class="mascot-line"
      :stroke-width="widths.eye"
    />
    <path
      :d="star"
      class="mascot-star"
    />
    <path
      :d="MASCOT_SMILE"
      class="mascot-line"
      :stroke-width="widths.smile"
    />
  </svg>
</template>
