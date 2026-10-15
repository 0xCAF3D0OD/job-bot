<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";

import Illustration from "./Illustration.vue";

// L'IA rédige (docs/58 §3.2) : 10 à 30 secondes ; l'illustration animée et une phrase qui
// change toutes les 4 secondes, au lieu d'un texte d'attente immobile.
const props = defineProps<{ kind: "letter" | "cv" | "coaching" }>();

const PHRASES: Record<typeof props.kind, string[]> = {
  letter: ["Je lis l'offre…", "Je choisis tes expériences…", "J'écris la lettre…", "Je relis…"],
  cv: ["Je lis l'offre…", "Je choisis ce qui compte pour ce poste…", "Je mets en forme ton CV…", "Je relis…"],
  coaching: ["Je relis tes retours d'entretien…", "Je cherche ce qui revient…", "Je prépare des pistes…"],
};
const index = ref(0);
let timer: ReturnType<typeof setInterval> | undefined;
onMounted(() => {
  timer = setInterval(() => {
    index.value = Math.min(index.value + 1, PHRASES[props.kind].length - 1);
  }, 4000);
});
onUnmounted(() => clearInterval(timer));
</script>

<template>
  <div
    class="ai-writing"
    role="status"
    data-test="ai-writing"
  >
    <Illustration name="ai-generated-document" />
    <p class="ai-writing-text">
      {{ PHRASES[kind][index] }}
    </p>
    <p class="hint">
      {{ kind === "coaching" ? "Quelques secondes." : "Compte une trentaine de secondes." }}
    </p>
  </div>
</template>
