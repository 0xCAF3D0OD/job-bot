<script setup lang="ts">
import { onBeforeUnmount, ref } from "vue";

// Description au survol (docs/53) : remplace les « ? ». Le libellé, souligné en pointillé,
// montre une courte bulle après 3 secondes de souris immobile dessus. Rien au toucher
// (l'assistant répond sur téléphone) ; les lecteurs d'écran la lisent avec le libellé
// (aria-description), sans qu'elle s'ajoute au texte d'un titre.
defineProps<{ text: string }>();

const DELAY_MS = 3000;
const shown = ref(false);
let timer: ReturnType<typeof setTimeout> | null = null;

function enter(event: PointerEvent): void {
  if (event.pointerType !== "mouse") return;
  leave();
  timer = setTimeout(() => (shown.value = true), DELAY_MS);
}

function leave(): void {
  if (timer) clearTimeout(timer);
  timer = null;
  shown.value = false;
}

onBeforeUnmount(leave);
</script>

<template>
  <!-- Sans description (texte vide), le libellé reste simple. -->
  <template v-if="!text">
    <slot />
  </template>
  <span
    v-else
    class="hover-note"
    :aria-description="text"
    data-test="hover-note"
    @pointerenter="enter"
    @pointerleave="leave"
  >
    <slot />
    <span
      v-if="shown"
      class="hover-note-bubble"
      aria-hidden="true"
      data-test="hover-note-text"
    >{{ text }}</span>
  </span>
</template>
