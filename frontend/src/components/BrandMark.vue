<script setup lang="ts">
import { computed } from "vue";

import { LOGO_DIAMOND, LOGO_DIAMOND_SMALL_SIZE, LOGO_LOOP, LOGO_VIEWBOX } from "../brandPaths";

// Le logo jobA1 (docs/100) : un trait bleu qui entoure une fois et dépasse, le diamant pêche
// au même trait. Le trait s'épaissit quand le logo rapetisse, aux paliers de la planche ; à
// 32 px et moins, trait épais et diamant un peu plus grand. Décoratif : le nom à côté le dit.
const props = withDefaults(defineProps<{ size?: number }>(), { size: 28 });
const tier = computed(() => {
  if (props.size >= 100) return { loop: 3.6, diamond: 3.6, path: LOGO_DIAMOND };
  if (props.size >= 60) return { loop: 5, diamond: 5, path: LOGO_DIAMOND };
  if (props.size > 32) return { loop: 5.5, diamond: 5.5, path: LOGO_DIAMOND };
  return { loop: 8.5, diamond: 8, path: LOGO_DIAMOND_SMALL_SIZE };
});
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
      :d="LOGO_LOOP"
      class="brand-logo-loop"
      :stroke-width="tier.loop"
    />
    <path
      :d="tier.path"
      class="brand-logo-diamond"
      :stroke-width="tier.diamond"
    />
  </svg>
</template>
