<script setup lang="ts">
import { onMounted, onUnmounted, watch } from "vue";

// Bulle temporaire (docs/32 §4) : 5 s, 8 s pour une erreur ; le compte s'arrête tant que la
// souris ou le clavier est dessus, et reprend en sortant. × pour la fermer tout de suite.
const TOAST_MS = 5000;
const TOAST_ERROR_MS = 8000;

const props = defineProps<{ message: string; error?: boolean }>();
const emit = defineEmits<{ close: [] }>();

let timer: ReturnType<typeof setTimeout> | undefined;

function hold(): void {
  clearTimeout(timer);
}

function release(): void {
  clearTimeout(timer);
  timer = setTimeout(() => emit("close"), props.error ? TOAST_ERROR_MS : TOAST_MS);
}

watch(() => props.message, release);
onMounted(release);
onUnmounted(hold);
</script>

<template>
  <div
    class="toast"
    role="status"
    data-test="toast"
    @mouseenter="hold"
    @mouseleave="release"
    @focusin="hold"
    @focusout="release"
  >
    <span>{{ message }}</span>
    <button
      type="button"
      class="assistant-close toast-close"
      aria-label="Fermer"
      data-test="toast-close"
      @click="emit('close')"
    >
      ×
    </button>
  </div>
</template>
