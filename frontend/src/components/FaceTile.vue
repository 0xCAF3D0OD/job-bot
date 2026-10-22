<script setup lang="ts">
import type { Mood } from "../brandPaths";
import FaceMark from "./FaceMark.vue";

// La tuile du visage (docs/123 §1, 56 px) : à droite du titre d'une carte, la couleur de
// l'humeur en fond, le visage en noir. `act` : l'orange, seulement quand il faut agir.
defineProps<{ mood: Mood; act?: boolean; wink?: boolean }>();
</script>

<template>
  <span
    :class="['face-tile', mood, { act }]"
    aria-hidden="true"
  >
    <FaceMark
      :mood="mood"
      :size="40"
      :wink="wink"
    />
  </span>
</template>
