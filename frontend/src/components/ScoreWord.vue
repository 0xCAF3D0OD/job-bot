<script setup lang="ts">
import { computed } from "vue";

import { scoreWord } from "../format";
import FaceMark from "./FaceMark.vue";

// La note en mots, dans les listes (docs/121 §C.5, règles §4) : le visage du 1 et un mot (Très
// proche, Proche, À creuser, Loin) ; dessous, une jauge discrète remplie comme la note, pour la
// nuance à l'intérieur d'un niveau (retirée en 1.6.4, rétablie en 1.6.6) ; le chiffre au survol
// et pour les lecteurs d'écran. Sans note :
// « Pas encore notée », sans visage, avec la raison au survol. Le cercle chiffré reste dans
// la fiche de l'offre.
// `plain` : le mot seul, sans le visage (« Pour cette offre », Kevin 2026-11-05).
const props = defineProps<{ score: number | null; pending?: string; stale?: boolean; plain?: boolean }>();

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
        v-if="!plain"
        :mood="word.mood"
      />
      <span aria-hidden="true">{{ word.word }}</span>
    </span>
    <span
      class="score-gauge"
      :style="{ '--p': Math.max(0, Math.min(100, score!)) }"
      aria-hidden="true"
    />
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

<!-- Styles gardés ici : le composant n’est monté nulle part dans l’application (allègement du CSS commun, 14.11). -->
<style>
/* La note en mots (docs/121 §C.5, docs/123) : le visage du 1 et un mot, à la couleur de la
   note ; le chiffre au survol. Le filet en bas de la ligne d'offre, à la longueur de la note,
   sur le filet gris de la liste. Pas encore notée : en gris, filet en pointillés. */
.score-word { display: inline-grid; justify-items: end; gap: var(--space-2); flex: none; font-size: var(--font-small); font-weight: var(--weight-semibold); white-space: nowrap; }
.score-word-label { display: inline-flex; align-items: center; gap: var(--space-2); }
/* La jauge discrète, pour la nuance à l'intérieur d'un niveau (rétablie en 1.6.6) ; la piste sur --border. */
.score-gauge { display: block; width: 4.5rem; height: 4px; border-radius: var(--radius-pill); background: linear-gradient(to right, currentColor calc(var(--p, 0) * 1%), var(--border) 0); }
.score-word.very-close { color: var(--ok-text); }
.score-word.close { color: var(--accent); }
.score-word.dig { color: var(--score-dig); }
.score-word.far, .score-word.pending { color: var(--muted); }
/* « Loin » : le mot en --text-secondary, la jauge en --neutral-graphic, distincte du gris chaud d'« À creuser ». */
.score-word.far .score-gauge { color: var(--neutral-graphic); }
.score-word.pending { font-weight: var(--weight-regular); font-size: var(--font-small); }
.score-word.stale { opacity: 0.7; }
</style>
