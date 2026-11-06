<script setup lang="ts">
import type { Pose } from "../personnage";
import Illustration from "./Illustration.vue";

// Un état montré par le personnage (docs/141 §3) : la pose, le titre, une ligne, puis les actions. Même
// mise en page que FaceState, mais avec le personnage à la place du visage ; jamais les deux à la fois.
// `full` : un écran plein (240 à 280 px) ; sinon l'état tient dans une liste (200 px au plus).
withDefaults(
  defineProps<{ pose: Pose; title: string; height?: number; desktopHeight?: number; full?: boolean; heading?: "h1" | "h2" }>(),
  { height: 200, desktopHeight: undefined, full: false, heading: "h2" },
);
</script>

<template>
  <div class="face-state character-state">
    <Illustration
      :pose="pose"
      :height="height"
      :desktop-height="desktopHeight"
      :full="full"
    />
    <component
      :is="heading"
      class="face-state-title character-state-title"
    >
      {{ title }}
    </component>
    <div
      v-if="$slots.default"
      class="face-state-line"
    >
      <slot />
    </div>
  </div>
</template>

<style scoped>
/* Valeurs de la maquette AucuneOffre (390 px) : le titre à 22 px en gras, 8 px sous le personnage. */
.character-state-title { margin-top: var(--space-2); font-size: var(--font-section); font-weight: var(--weight-bold); }
</style>
