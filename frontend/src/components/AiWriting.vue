<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";

import AppIcon from "./AppIcon.vue";

// L'IA rédige (docs/59 §4) : la seule vraie attente de la plateforme (10 à 30 s). Une barre
// d'étapes, l'étape en cours en violet, les faites cochées ; elle avance avec le temps
// habituel de chaque étape et s'arrête sur la dernière jusqu'à l'arrivée du texte.
const props = defineProps<{ kind: "letter" | "cv" | "coaching" | "feedback" }>();

const STEPS: Record<typeof props.kind, { labels: string[]; everyMs: number; hint: string }> = {
  letter: {
    labels: ["Lire l'offre", "Choisir tes expériences", "Rédiger", "Relire"],
    everyMs: 7000,
    hint: "Une trentaine de secondes.",
  },
  cv: {
    labels: ["Lire l'offre", "Choisir ce qui compte", "Mettre en forme", "Relire"],
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
  <div
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
        <span
          v-if="index < current"
          class="with-icon"
        ><AppIcon name="done" />{{ label }}</span>
        <template v-else>
          {{ label }}
        </template>
      </li>
    </ol>
    <p class="hint">
      {{ STEPS[kind].hint }}
    </p>
  </div>
</template>
