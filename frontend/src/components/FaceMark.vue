<script setup lang="ts">
import { FACE_MOUTH, ICON_EYE, ICON_ONE, ICON_SPARK, LOGO_VIEWBOX, type Mood } from "../brandPaths";

// Le visage du 1 (docs/123) : le « 1 » trace le sourcil et le nez, un œil, la bille pêche, et
// une bouche selon l'humeur. Il prend la couleur du texte autour (`currentColor`) ; la bille
// reste pêche. Décoratif : le mot à côté dit tout.
withDefaults(defineProps<{ mood: Mood; size?: number }>(), { size: 20 });
</script>

<template>
  <svg
    class="face-mark"
    :width="size"
    :height="size"
    :viewBox="LOGO_VIEWBOX"
    aria-hidden="true"
    focusable="false"
    :data-mood="mood"
  >
    <path
      class="face-line"
      :d="ICON_ONE"
    />
    <circle
      class="face-eye"
      :cx="ICON_EYE.x"
      :cy="ICON_EYE.y"
      r="10"
    />
    <circle
      class="face-spark"
      :cx="ICON_SPARK.x"
      :cy="ICON_SPARK.y"
      r="10"
    />
    <path
      class="face-line"
      :d="FACE_MOUTH[mood]"
    />
  </svg>
</template>
