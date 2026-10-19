<script setup lang="ts">
import { computed } from "vue";

import { LOGO_DIAMOND, LOGO_DIAMOND_SMALL_SIZE, LOGO_LOOPS, LOGO_VIEWBOX } from "../brandPaths";

// Le logo jobA1 (docs/97, docs/98) : deux boucles au stylo bleu autour d'un diamant pêche
// tracé au stylo. Le trait s'épaissit quand le logo rapetisse, aux paliers de la planche ; sous
// 24 px, une seule boucle et un diamant plus grand. Décoratif : le nom à côté dit ce que c'est.
const props = withDefaults(defineProps<{ size?: number }>(), { size: 28 });
const tier = computed(() => {
  if (props.size >= 100) return { loop: 2.6, loops: 2, diamond: LOGO_DIAMOND };
  if (props.size >= 50) return { loop: 3.8, loops: 2, diamond: LOGO_DIAMOND };
  if (props.size >= 40) return { loop: 4, loops: 2, diamond: LOGO_DIAMOND };
  if (props.size >= 24) return { loop: 5, loops: 2, diamond: LOGO_DIAMOND };
  return { loop: 10, loops: 1, diamond: LOGO_DIAMOND_SMALL_SIZE };
});
const loops = computed(() => LOGO_LOOPS.slice(0, tier.value.loops));
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
      v-for="(loop, index) in loops"
      :key="index"
      :d="loop"
      class="brand-logo-loop"
      :stroke-width="tier.loop"
    />
    <path
      :d="tier.diamond"
      class="brand-logo-diamond"
      :stroke-width="Math.round(tier.loop * 1.1 * 100) / 100"
    />
  </svg>
</template>
