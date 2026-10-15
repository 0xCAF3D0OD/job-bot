<script setup lang="ts">
import { nextTick, onBeforeUnmount, ref } from "vue";

// Aide « ? » (docs/29 §2) : remplace une infobulle au survol, invisible au toucher et au
// clavier. S'ouvre au clic, au toucher ou à Entrée ; Échap, un clic ailleurs ou la sortie du
// champ la ferment. Le texte est annoncé par les lecteurs d'écran (zone polie).
defineProps<{ text: string; label?: string }>();

const open = ref(false);
const root = ref<HTMLElement | null>(null);
const bubble = ref<HTMLElement | null>(null);
// Décalage horizontal pour que la bulle reste dans l'écran (docs/32 §1 : le « ? » est partout).
const shift = ref(0);
const MARGIN = 8;

async function place(): Promise<void> {
  shift.value = 0;
  await nextTick();
  const rect = bubble.value?.getBoundingClientRect();
  if (!rect) return;
  const width = globalThis.innerWidth ?? 0;
  if (rect.left < MARGIN) shift.value = MARGIN - rect.left;
  else if (width && rect.right > width - MARGIN) shift.value = width - MARGIN - rect.right;
}
const id = `help-${Math.random().toString(36).slice(2, 8)}`;

function onDocument(event: Event): void {
  if (root.value && !root.value.contains(event.target as Node)) open.value = false;
}

function toggle(): void {
  open.value = !open.value;
  if (open.value) {
    document.addEventListener("pointerdown", onDocument);
    void place();
  }
  else document.removeEventListener("pointerdown", onDocument);
}

function close(): void {
  open.value = false;
  document.removeEventListener("pointerdown", onDocument);
}

onBeforeUnmount(close);
</script>

<template>
  <span
    ref="root"
    class="help-tip"
    @keydown.esc="close"
  >
    <button
      type="button"
      class="help-tip-button"
      :aria-label="label ?? 'Aide'"
      :aria-expanded="open"
      :aria-controls="id"
      data-test="help-tip"
      @click="toggle"
    >?</button>
    <span
      :id="id"
      class="help-tip-text"
      role="status"
      aria-live="polite"
    >
      <span
        v-if="open"
        ref="bubble"
        :style="shift ? { marginLeft: `${shift}px` } : undefined"
        data-test="help-tip-text"
      >{{ text }}</span>
    </span>
  </span>
</template>
