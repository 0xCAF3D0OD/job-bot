<script setup lang="ts">
import { FACE_MOUTH, FACE_VIEWBOX_SNUG, ICON_EYE, ICON_ONE, ICON_SPARK, LOGO_VIEWBOX, type Mood } from "../brandPaths";

// Le visage du 1 (docs/123) : le « 1 » trace le sourcil et le nez, un œil, la bille pêche, et
// une bouche selon l'humeur. Il prend la couleur du texte autour (`currentColor`) ; la bille
// reste pêche. Décoratif : le mot à côté dit tout.
// Trois gestes, chacun lié à un événement (docs/123 §3) : `wink`, un clin d'œil une fois
// (l'objectif atteint) ; `waiting`, l'œil et la bille qui pulsent pendant une vraie attente ;
// changer d'humeur, la bouche en fondu (150 ms). Rien avec « réduire les animations ».
// `snug` : cadré au plus près, pour qu'à côté d'un mot le dessin remplisse sa taille (1.6.5).
withDefaults(defineProps<{ mood: Mood; size?: number; wink?: boolean; waiting?: boolean; snug?: boolean }>(), { size: 20 });
</script>

<template>
  <svg
    :class="['face-mark', { wink, waiting }]"
    :width="size"
    :height="size"
    :viewBox="snug ? FACE_VIEWBOX_SNUG : LOGO_VIEWBOX"
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
    <Transition
      name="face-mouth"
      mode="out-in"
    >
      <path
        :key="mood"
        class="face-line"
        :d="FACE_MOUTH[mood]"
      />
    </Transition>
  </svg>
</template>
