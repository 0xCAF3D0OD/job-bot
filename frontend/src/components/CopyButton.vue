<script setup lang="ts">
import { onUnmounted, ref } from "vue";

import CopyLabel from "./CopyLabel.vue";

// Copier, un seul bouton partout (règles §4, planche « tête de carte, Copier et ⋯ ») : l'icône seule,
// juste à côté de la valeur ; « Copier » en légende au survol, puis la coche et « Copié » pendant 2 s,
// annoncés aux lecteurs d'écran (WCAG 4.1.3). Inspiré du bouton de copie de GitHub (Primer).
// `text` (maquette Preparer, étape 7c) : le mot « Copier » dans une pastille, qui devient « Copié » en vert ;
// le nom du champ reste lu par un lecteur d'écran.
// `announce: false` : la page annonce elle-même la copie (panneau des alertes, « Adresse copiée »).
// `word` : le mot de la pastille à la place de « Copier » (« Objet » dans la Relance) ; `ariaLabel` : le nom lu par
// un lecteur d'écran, à la place du mot et de `text`.
const props = withDefaults(defineProps<{ value: string; label?: string; testId?: string; text?: string; announce?: boolean; word?: string; ariaLabel?: string }>(), {
  label: "Copier",
  word: "Copier",
  ariaLabel: undefined,
  testId: "copy",
  text: "",
  announce: true,
});
const emit = defineEmits<{ copied: [] }>();

const COPIED_MS = 2000;

const done = ref(false);
let timer: ReturnType<typeof setTimeout> | undefined;

async function copy(): Promise<void> {
  try {
    await navigator.clipboard.writeText(props.value);
  } catch {
    done.value = false;
    return;
  }
  done.value = true;
  emit("copied");
  clearTimeout(timer);
  timer = setTimeout(() => (done.value = false), COPIED_MS);
}
onUnmounted(() => clearTimeout(timer));
</script>

<template>
  <button
    type="button"
    :class="text ? ['copy-text', { 'copy-done': done }] : 'copy-button'"
    :data-test="testId"
    :aria-label="ariaLabel"
    @click="copy"
  >
    <template v-if="text">
      {{ done ? "Copié" : word }}<span
        v-if="!ariaLabel"
        class="visually-hidden"
      > : {{ text }}</span>
    </template>
    <CopyLabel
      v-else
      :done="done"
      :label="label"
    />
  </button>
  <span
    v-if="announce"
    class="visually-hidden"
    role="status"
  >{{ done ? "Copié" : "" }}</span>
</template>
