<script setup lang="ts">
import type { Mood } from "../brandPaths";
import FaceMark from "./FaceMark.vue";
import Illustration, { type IllustrationName } from "./Illustration.vue";

// Un état de jobA1 (docs/123 §2, T) : le visage de 120 px au centre, le titre, une ligne. Pour
// une liste vide et pour une page qui charge (`waiting` : l'œil et la bille pulsent).
// `illustration` (1.6.73, règle §4) : une illustration décorative à la place du visage, pour un
// écran vide, des premiers pas, une réussite ou une erreur ; jamais les deux à la fois.
withDefaults(
  defineProps<{ title: string; mood?: Mood; waiting?: boolean; heading?: "h2" | "p"; illustration?: IllustrationName }>(),
  {
    mood: "content",
    heading: "h2",
    illustration: undefined,
  },
);
</script>

<template>
  <div class="face-state">
    <Illustration
      v-if="illustration"
      :name="illustration"
      class="spot"
      sizes="(max-width: 820px) 260px, 424px"
    />
    <FaceMark
      v-else
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
