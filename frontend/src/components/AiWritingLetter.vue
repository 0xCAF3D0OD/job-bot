<script setup lang="ts">
import { defineAsyncComponent } from "vue";

// Chargé à la demande, comme avant dans AiWriting.
const LoadingSteps = defineAsyncComponent(() => import("./LoadingSteps.vue"));

// L'écriture de la lettre (§53, planche ChargementLettre ; Kevin, 17.11) : l'attente ne bloque pas l'écran, elle prend
// seulement le style de la planche dans sa zone. « CV adapté » et « puis j'adapte ton CV » seulement quand un CV se
// prépare en même temps (`withCv`). À part d'AiWriting pour que Suivi et les entretiens, qui n'écrivent pas de lettre,
// ne téléchargent pas ce code (poids de suivi-assistant, 17.11).
defineProps<{ withCv?: boolean; done?: boolean }>();
</script>

<template>
  <LoadingSteps
    class="ai-writing-letter"
    :lines="['J’écris ta lettre,', withCv ? 'puis j’adapte ton CV' : 'environ 30 secondes']"
    :steps="withCv ? ['Annonce lue', 'Lettre', 'CV adapté', 'Relecture'] : ['Annonce lue', 'Lettre', 'Relecture']"
    :every-ms="7000"
    :done="done"
    label="Écriture de la lettre"
    data-test="ai-writing"
  />
</template>

<style>
.ai-writing-letter { padding: var(--space-6) var(--space-5); }
</style>
