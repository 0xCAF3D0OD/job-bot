<script setup lang="ts">
import { LOGO_EYE, LOGO_ONE, LOGO_SMILE, LOGO_SPARK, LOGO_TILT, LOGO_VIEWBOX } from "../brandPaths";

// Le logo jobA1 (docs/102) : un visage complice fait avec le 1 du nom. Le 1 trace le sourcil
// et le nez, un œil bleu, un œil pêche (la bille), un sourire discret ; le tout penché de −6°.
// Couleurs du thème : `--logo-line` pour le visage, `--logo-spark` pour la bille. Décoratif :
// le nom à côté le dit.
withDefaults(defineProps<{ size?: number }>(), { size: 28 });
</script>

<template>
  <svg
    class="brand-logo"
    :width="size"
    :height="size"
    :viewBox="LOGO_VIEWBOX"
    aria-hidden="true"
    focusable="false"
    data-test="brand-logo"
  >
    <g :transform="LOGO_TILT">
      <path
        class="brand-logo-line"
        :d="LOGO_ONE"
      />
      <circle
        class="brand-logo-eye"
        :cx="LOGO_EYE.x"
        :cy="LOGO_EYE.y"
        :r="LOGO_EYE.r"
      />
      <circle
        class="brand-logo-spark"
        :cx="LOGO_SPARK.x"
        :cy="LOGO_SPARK.y"
        :r="LOGO_SPARK.r"
      />
      <path
        class="brand-logo-line"
        :d="LOGO_SMILE"
      />
    </g>
  </svg>
</template>
