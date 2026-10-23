<script setup lang="ts">
import { computed } from "vue";

import { scoreWord } from "../format";
import FaceMark from "./FaceMark.vue";

// La note en mots, dans les listes (docs/121 §C.5, règles §4) : le visage du 1 et un mot (Très
// proche, Proche, À creuser, Loin), sans jauge depuis la 1.6.4 ; le chiffre au survol et pour
// les lecteurs d'écran. Sans note :
// « Pas encore notée », sans visage, avec la raison au survol. Le cercle chiffré reste dans
// la fiche de l'offre.
const props = defineProps<{ score: number | null; pending?: string; stale?: boolean }>();

const word = computed(() => (props.score === null ? null : scoreWord(props.score)));
const label = computed(() =>
  props.score === null
    ? (props.pending ?? "Pas encore notée")
    : `${word.value!.word} : ${Math.round(props.score)} sur 100${props.stale ? ", note faite avec un ancien profil" : ""}`,
);
</script>

<template>
  <span
    v-if="word"
    :class="['score-word', word.tone, { stale }]"
    :title="label"
    :aria-label="label"
    role="img"
    data-test="score"
  >
    <span class="score-word-label">
      <FaceMark
        :mood="word.mood"
        snug
      />
      <span aria-hidden="true">{{ word.word }}</span>
    </span>
  </span>
  <span
    v-else
    class="score-word pending"
    :title="label"
    data-test="score"
  >Pas encore notée<span
    v-if="label !== 'Pas encore notée'"
    class="visually-hidden"
  > ({{ label }})</span></span>
</template>
