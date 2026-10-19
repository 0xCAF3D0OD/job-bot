<script setup lang="ts">
import { computed } from "vue";

import {
  MASCOT_CLOSED_EYE,
  MASCOT_EYE_LEFT,
  MASCOT_EYE_RIGHT,
  MASCOT_FACE,
  MASCOT_O,
  MASCOT_OPEN_SMILE,
  MASCOT_SMILE,
  mascotSparkle,
} from "../brandPaths";

// La mascotte de l'assistant (docs/99) : un visage rond, trois expressions.
// « listening » : à l'écoute ; « thinking » : réfléchit ; « found » : a trouvé.
// Les traits, les points et les étincelles grossissent aux petites tailles (paliers de docs/97).
// Décorative : « Assistant » à côté dit ce que c'est.
export type MascotMood = "listening" | "thinking" | "found";
const props = withDefaults(defineProps<{ size?: number; mood?: MascotMood }>(), { size: 28, mood: "listening" });
const widths = computed(() => {
  if (props.size >= 100) return { eye: 6.5, smile: 6, dot: 5.2, sparkle: 10 };
  if (props.size >= 40) return { eye: 7, smile: 6.5, dot: 5.6, sparkle: 10.5 };
  if (props.size >= 24) return { eye: 8, smile: 7.5, dot: 6.2, sparkle: 11.5 };
  return { eye: 10.8, smile: 9.9, dot: 7.5, sparkle: 12.5 };
});
const sparkle = (eye: { x: number; y: number }) => mascotSparkle(eye.x, eye.y, widths.value.sparkle);
</script>

<template>
  <svg
    class="assistant-mascot"
    :width="size"
    :height="size"
    viewBox="0 0 100 100"
    aria-hidden="true"
    data-test="assistant-mascot"
    :data-mood="mood"
  >
    <path
      :d="MASCOT_FACE"
      class="mascot-face"
    />
    <g
      v-if="mood === 'thinking'"
      key="thinking"
      class="mascot-expression"
    >
      <circle
        :cx="MASCOT_EYE_LEFT.x"
        :cy="MASCOT_EYE_LEFT.y"
        :r="widths.dot"
        class="mascot-dot"
      />
      <circle
        :cx="MASCOT_EYE_RIGHT.x"
        :cy="MASCOT_EYE_RIGHT.y"
        :r="widths.dot"
        class="mascot-dot"
      />
      <circle
        :cx="MASCOT_O.x"
        :cy="MASCOT_O.y"
        :r="MASCOT_O.r"
        class="mascot-line"
        :stroke-width="widths.smile * 0.6"
      />
    </g>
    <g
      v-else-if="mood === 'found'"
      key="found"
      class="mascot-expression"
    >
      <path
        :d="sparkle(MASCOT_EYE_LEFT)"
        class="mascot-star"
      />
      <path
        :d="sparkle(MASCOT_EYE_RIGHT)"
        class="mascot-star"
      />
      <path
        :d="MASCOT_OPEN_SMILE"
        class="mascot-mouth"
      />
    </g>
    <g
      v-else
      key="listening"
      class="mascot-expression"
    >
      <path
        :d="MASCOT_CLOSED_EYE"
        class="mascot-line"
        :stroke-width="widths.eye"
      />
      <path
        :d="sparkle(MASCOT_EYE_RIGHT)"
        class="mascot-star"
      />
      <path
        :d="MASCOT_SMILE"
        class="mascot-line"
        :stroke-width="widths.smile"
      />
    </g>
  </svg>
</template>
