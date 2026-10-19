<script setup lang="ts">
import { computed } from "vue";

import { LOGO_LOOPS, LOGO_STAR, LOGO_VIEWBOX } from "../brandPaths";

// Le logo jobA1 (docs/97) : deux boucles au stylo bleu autour de l'étoile pêche. Le trait
// s'épaissit quand le logo rapetisse, aux paliers de la planche. Décoratif : le nom à côté dit
// ce que c'est.
const props = withDefaults(defineProps<{ size?: number }>(), { size: 26 });
const stroke = computed(() => (props.size >= 100 ? 2.6 : props.size >= 48 ? 3.6 : props.size >= 24 ? 5 : 7));
</script>

<template>
  <svg
    class="brand-logo"
    :width="size"
    :height="size"
    :viewBox="LOGO_VIEWBOX"
    aria-hidden="true"
    data-test="brand-logo"
  >
    <path
      v-for="(loop, index) in LOGO_LOOPS"
      :key="index"
      :d="loop"
      class="brand-logo-loop"
      :stroke-width="stroke"
    />
    <path
      :d="LOGO_STAR"
      class="brand-logo-star"
    />
  </svg>
</template>
