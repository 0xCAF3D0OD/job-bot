<script setup lang="ts">
import { defineAsyncComponent, onMounted, onUnmounted, ref } from "vue";

import AppIcon from "./AppIcon.vue";

// La lettre (§53, planche ChargementLettre ; Kevin, 17.11) : l'attente ne bloque pas l'écran, elle prend seulement le
// style de la planche dans sa zone. « CV adapté » et « puis j'adapte ton CV » seulement quand un CV se prépare en même
// temps (`withCv`, lu au début de l'attente : les étapes restent celles du travail lancé). Chargé à la demande : les autres attentes gardent leurs étapes.
const LoadingSteps = defineAsyncComponent(() => import("./LoadingSteps.vue"));

// L'IA rédige (docs/59 §4) : la seule vraie attente de la plateforme (10 à 30 s). Une barre
// d'étapes, l'étape en cours en violet, les faites cochées ; elle avance avec le temps
// habituel de chaque étape et s'arrête sur la dernière jusqu'à l'arrivée du texte.
const props = defineProps<{ kind: "letter" | "cv" | "coaching" | "feedback"; withCv?: boolean; done?: boolean }>();


const STEPS: Record<typeof props.kind, { labels: string[]; everyMs: number; hint: string }> = {
  letter: {
    labels: ["Lire l’offre", "Choisir tes expériences", "Rédiger", "Relire"],
    everyMs: 7000,
    hint: "Une trentaine de secondes.",
  },
  cv: {
    labels: ["Lire l’offre", "Choisir ce qui compte", "Mettre en forme", "Relire"],
    everyMs: 6000,
    hint: "Une vingtaine de secondes.",
  },
  coaching: {
    labels: ["Relire tes retours", "Chercher ce qui revient", "Préparer des pistes"],
    everyMs: 3000,
    hint: "Quelques secondes.",
  },
  feedback: {
    labels: ["Relire tes réponses", "Les comparer à ton profil", "Écrire le retour"],
    everyMs: 5000,
    hint: "Une quinzaine de secondes.",
  },
};
const current = ref(0);
let timer: ReturnType<typeof setInterval> | undefined;
onMounted(() => {
  timer = setInterval(() => {
    current.value = Math.min(current.value + 1, STEPS[props.kind].labels.length - 1);
  }, STEPS[props.kind].everyMs);
});
onUnmounted(() => clearInterval(timer));
</script>

<template>
  <LoadingSteps
    v-if="kind === 'letter'"
    class="ai-writing-letter"
    :lines="['J’écris ta lettre,', withCv ? 'puis j’adapte ton CV' : 'environ 30 secondes']"
    :steps="withCv ? ['Annonce lue', 'Lettre', 'CV adapté', 'Relecture'] : ['Annonce lue', 'Lettre', 'Relecture']"
    :every-ms="7000"
    :done="done"
    label="Écriture de la lettre"
    data-test="ai-writing"
  />
  <div
    v-else
    class="ai-writing"
    role="status"
    data-test="ai-writing"
  >
    <ol
      class="ai-steps"
      :style="{ '--ai-steps': STEPS[kind].labels.length }"
    >
      <li
        v-for="(label, index) in STEPS[kind].labels"
        :key="label"
        :class="{ done: index < current, current: index === current }"
        :aria-current="index === current ? 'step' : undefined"
      >
        <!-- Le libellé sur deux lignes au plus, dans sa colonne (Kevin, 2026-11-05 : rien ne déborde à 320 px). -->
        <span class="ai-step-label"><AppIcon
          v-if="index < current"
          name="done"
        />{{ label }}</span>
      </li>
    </ol>
    <p class="hint">
      {{ STEPS[kind].hint }}
    </p>
  </div>
</template>

<style>
/* Sorti de style.css (allègement du 16.11, issue #797) : ces règles ne servent qu'ici, chargées avec ce composant. */
.ai-writing-letter { padding: var(--space-6) var(--space-5); }
.ai-steps li::before { content: ""; height: 4px; border-radius: var(--radius-pill); background: var(--border); transition: background-color var(--t-state); }
@media (max-width: 599px) {
.ai-steps { gap: var(--space-1); }
}
</style>
