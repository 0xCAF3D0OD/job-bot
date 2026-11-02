<script setup lang="ts">
import { computed } from "vue";

import { scoreWord } from "../format";

// La note dans un cercle : le contour se remplit selon la note, plein à 100 (docs/73). Sans
// note, un cercle vide en pointillés, qui dit pourquoi (docs/76 §3).
// `worded` (D3, 2026-11-02) : l'anneau sert de jauge, sans chiffre au centre, le mot dessous ; le chiffre
// reste pour les lecteurs d'écran et au survol.
const props = defineProps<{ score: number | null; pending?: string; stale?: boolean; large?: boolean; worded?: boolean }>();

const value = computed(() =>
  props.score === null ? null : Math.max(0, Math.min(100, Math.round(props.score))),
);
const label = computed(() =>
  value.value === null
    ? (props.pending ?? "Pas encore notée")
    : `Proximité avec ton profil : ${value.value} sur 100${props.stale ? ", calculée avec un ancien profil" : ""}`,
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
    v-else-if="worded"
    :class="['score-ring-worded', scoreWord(value).tone]"
    role="img"
    :aria-label="`${scoreWord(value).word} : ${value} sur 100`"
    :title="`${scoreWord(value).word} : ${value} sur 100`"
    data-test="score"
  >
    <span
      :class="['score-ring', scoreWord(value).tone, { stale }]"
      :style="{ '--p': value }"
      aria-hidden="true"
    />
    <span aria-hidden="true">{{ scoreWord(value).word }}</span>
  </span>
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
