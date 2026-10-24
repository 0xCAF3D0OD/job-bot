<script setup lang="ts">
import type { Mood } from "../brandPaths";
import FaceMark from "./FaceMark.vue";

// La tuile du visage (docs/123 §1, 56 px) : à droite du titre d'une carte, la couleur de
// l'humeur en fond, le visage en noir. `act` : l'orange, seulement quand il faut agir ;
// `waiting` : le geste de l'attente (docs/128, les premières offres arrivent).
defineProps<{ mood: Mood; act?: boolean; wink?: boolean; small?: boolean; waiting?: boolean }>();
</script>

<template>
  <span
    :class="['face-tile', mood, { act, small }]"
    aria-hidden="true"
  >
    <FaceMark
      :mood="mood"
      :size="small ? 28 : 32"
      :wink="wink"
      :waiting="waiting"
    />
  </span>
</template>
