<script setup lang="ts">
import { computed } from "vue";

import { scoreLevel } from "../format";

// La note dans un cercle : le contour se remplit selon la note, plein à 100 (docs/73).
const props = defineProps<{ score: number; stale?: boolean; large?: boolean }>();

const value = computed(() => Math.max(0, Math.min(100, Math.round(props.score))));
const label = computed(
  () =>
    `Note de l'IA : ${value.value} sur 100${props.stale ? ", faite avec un ancien profil" : ""}`,
);
</script>

<template>
  <span
    :class="['score-ring', scoreLevel(value), { stale, large }]"
    :style="{ '--p': value }"
    role="img"
    :aria-label="label"
    :title="label"
    data-test="score"
  >{{ value }}<small v-if="large">/100</small></span>
</template>
