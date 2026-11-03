<script setup lang="ts">
import { computed } from "vue";

import { scoreWord } from "../format";

// L'anneau de la note (maquette Systeme, règle 1 ; D3, D5) : une piste complète en couleur pâle, des
// graduations tous les 25 % découpées dans la couleur du fond, un arc rempli selon la note, dans la couleur du
// mot (Très proche et Proche en --success, À creuser en --score-dig, Loin en --neutral-graphic), jamais en bleu.
// `worded` : pas de chiffre au centre, le mot dessous ; le chiffre reste pour les lecteurs d'écran et au survol.
// Sans note : pas d'anneau, « Pas encore notée » en texte (la raison au survol et pour les lecteurs d'écran).
const props = defineProps<{ score: number | null; pending?: string; stale?: boolean; large?: boolean; worded?: boolean }>();

const value = computed(() =>
  props.score === null ? null : Math.max(0, Math.min(100, Math.round(props.score))),
);
const word = computed(() => (value.value === null ? null : scoreWord(value.value)));
const label = computed(() =>
  value.value === null
    ? (props.pending ?? "Pas encore notée")
    : `${word.value?.word} : ${value.value} sur 100${props.stale ? ", calculée avec un ancien profil" : ""}`,
);
// Le cercle de rayon 42 (viewBox 100) : 2π × 42.
const CIRCUMFERENCE = 263.89;
const dash = computed(() => `${(((value.value ?? 0) * CIRCUMFERENCE) / 100).toFixed(2)} ${CIRCUMFERENCE}`);
</script>

<template>
  <span
    v-if="value === null || !word"
    class="score-pending"
    :title="label"
    data-test="score"
  >Pas encore notée<span
    v-if="label !== 'Pas encore notée'"
    class="visually-hidden"
  > : {{ label }}</span></span>
  <span
    v-else
    :class="['score-ring-wrap', word.tone, { 'score-ring-worded': worded, stale }]"
    role="img"
    :aria-label="label"
    :title="label"
    data-test="score"
  >
    <span
      :class="['score-ring', word.tone, { large }]"
      aria-hidden="true"
    >
      <svg
        viewBox="0 0 100 100"
        focusable="false"
      >
        <circle
          class="score-ring-track"
          cx="50"
          cy="50"
          r="42"
        />
        <circle
          class="score-ring-arc"
          cx="50"
          cy="50"
          r="42"
          :stroke-dasharray="dash"
          transform="rotate(-90 50 50)"
        />
        <path
          class="score-ring-ticks"
          d="M50 1V15M85 50H99M50 85V99M1 50H15"
        />
      </svg>
      <span
        v-if="!worded"
        class="score-ring-value"
      >{{ value }}<small v-if="large">/100</small></span>
    </span>
    <span
      v-if="worded"
      class="score-ring-word"
      aria-hidden="true"
    >{{ word.word }}</span>
  </span>
</template>
