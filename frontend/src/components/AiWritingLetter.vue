<script setup lang="ts">
import { computed, defineAsyncComponent } from "vue";
import BrandMark from "./BrandMark.vue";

// Chargé à la demande, comme avant dans AiWriting.
const LoadingSteps = defineAsyncComponent(() => import("./LoadingSteps.vue"));

// L'écriture de la lettre sur téléphone (§53, planche ChargementLettre ; Kevin, 17.11 et 19.11) : posée sur le fond de
// la page, sans carte, le logo de 64 px, le titre manuscrit, la barre, puis les étapes. « CV adapté » et « puis j'adapte
// ton CV » seulement quand le CV s'adapte dans le même passage : `cv` vaut « busy » quand l'écriture commence. Le choix
// est fixé à ce moment, pour que la liste ne change pas de longueur si le CV finit avant la lettre.
// Les étapes suivent ce qui se passe vraiment (`phase` d'écriture puis de relecture, CV prêt ou non), jamais le temps :
// « CV adapté » n'est coché que si le CV est prêt. À part d'AiWriting pour que Suivi et les entretiens, qui n'écrivent
// pas de lettre, ne téléchargent pas ce code (poids de suivi-assistant, 17.11).
const props = defineProps<{ cv?: "" | "busy" | "failed"; cvReady?: boolean; phase?: "write" | "review"; done?: boolean }>();
const withCv = props.cv === "busy";
const writingNow = computed(() => !props.done && props.phase !== "review");
const states = computed(() => {
  const letter = writingNow.value ? "current" : "done";
  const review = props.done ? "done" : writingNow.value ? "todo" : "current";
  if (!withCv) return ["done", letter, review] as const;
  const cv = props.cvReady ? "done" : writingNow.value || String(props.cv) === "failed" ? "todo" : "current";
  return ["done", letter, cv, review] as const;
});
</script>

<template>
  <LoadingSteps
    class="ai-writing-letter"
    :lines="['J’écris ta lettre,', withCv ? 'puis j’adapte ton CV' : 'environ 30 secondes']"
    :steps="withCv ? ['Annonce lue', 'Lettre', 'CV adapté', 'Relecture'] : ['Annonce lue', 'Lettre', 'Relecture']"
    :states="[...states]"
    :details="['', 'D’après ton CV et l’annonce']"
    :every-ms="7000"
    :done="done"
    label="Écriture de la lettre"
    data-test="ai-writing"
  >
    <BrandMark :size="64" />
  </LoadingSteps>
</template>

<style>
/* 36 px du bord comme la planche : la marge de la page (20 px) et 16 px. */
.ai-writing-letter { padding: var(--space-8) var(--space-4); }
.ai-writing-letter .loading-steps-title { margin-top: calc(var(--space-6) + var(--space-1)); }
</style>
