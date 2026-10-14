<script setup lang="ts">
import { onBeforeUnmount, ref } from "vue";

// Aide « ? » (docs/29 §2) : remplace une infobulle au survol, invisible au toucher et au
// clavier. S'ouvre au clic, au toucher ou à Entrée ; Échap, un clic ailleurs ou la sortie du
// champ la ferment. Le texte est annoncé par les lecteurs d'écran (zone polie).
defineProps<{ text: string; label?: string }>();

const open = ref(false);
const root = ref<HTMLElement | null>(null);
const id = `help-${Math.random().toString(36).slice(2, 8)}`;

function onDocument(event: Event): void {
  if (root.value && !root.value.contains(event.target as Node)) open.value = false;
}

function toggle(): void {
  open.value = !open.value;
  if (open.value) document.addEventListener("pointerdown", onDocument);
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
        data-test="help-tip-text"
      >{{ text }}</span>
    </span>
  </span>
</template>
