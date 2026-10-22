<script setup lang="ts">
import type { Mood } from "../brandPaths";
import FaceMark from "./FaceMark.vue";

// Un état de jobA1 (docs/123 §2, T) : le visage de 120 px au centre, le titre, une ligne. Pour
// une liste vide et pour une page qui charge (`waiting` : l'œil et la bille pulsent).
withDefaults(defineProps<{ title: string; mood?: Mood; waiting?: boolean; heading?: "h2" | "p" }>(), {
  mood: "content",
  heading: "h2",
});
</script>

<template>
  <div class="face-state">
    <FaceMark
      :mood="mood"
      :size="120"
      :waiting="waiting"
    />
    <component
      :is="heading"
      class="face-state-title"
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
