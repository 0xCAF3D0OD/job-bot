<script setup lang="ts">
import { computed } from "vue";

import { scoreWord } from "../format";

// La note dans un cercle : le contour se remplit selon la note, plein à 100 (docs/73). Sans
// note, un cercle vide en pointillés, qui dit pourquoi (docs/76 §3).
const props = defineProps<{ score: number | null; pending?: string; stale?: boolean; large?: boolean }>();

const value = computed(() =>
  props.score === null ? null : Math.max(0, Math.min(100, Math.round(props.score))),
);
const label = computed(() =>
  value.value === null
    ? (props.pending ?? "Pas encore notée")
    : `Note de l'IA : ${value.value} sur 100${props.stale ? ", faite avec un ancien profil" : ""}`,
);
</script>

<template>
  <span
    v-if="value === null"
    class="score-ring pending"
    role="img"
    :aria-label="label"
    :title="label"
    data-test="score"
  >–</span>
  <span
    v-else
    :class="['score-ring', scoreWord(value).tone, { stale, large }]"
    :style="{ '--p': value }"
    role="img"
    :aria-label="label"
    :title="label"
    data-test="score"
  >{{ value }}<small v-if="large">/100</small></span>
</template>
