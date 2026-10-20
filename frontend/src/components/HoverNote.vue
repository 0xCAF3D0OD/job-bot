<script lang="ts">
import { ref as moduleRef } from "vue";

// La description ouverte au doigt, une à la fois sur toute la page.
const openNote = moduleRef<number | null>(null);
let seq = 0;
</script>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";

import { usePhone } from "../composables/usePhone";

// Description au survol (docs/53) : remplace les « ? ». Le libellé, souligné en pointillé,
// montre une courte bulle après 3 secondes de souris immobile dessus. Rien au toucher
// (l'assistant répond sur téléphone) ; les lecteurs d'écran la lisent avec le libellé
// (aria-description), sans qu'elle s'ajoute au texte d'un titre.
defineProps<{ text: string }>();

// Au doigt (docs/108 §2) : sur téléphone, un petit « i » à droite du titre ouvre la description
// en une ligne grise sous lui ; un second appui la referme. Une seule ouverte à la fois. Pas de
// « i » dans un bouton ou un lien : le bouton garde son aspect et son geste.
const { phone } = usePhone();
const root = ref<HTMLElement | null>(null);
const inControl = ref(false);
const id = ++seq;
const open = computed(() => openNote.value === id);
function toggle(): void {
  openNote.value = open.value ? null : id;
}
onMounted(() => {
  inControl.value = Boolean(root.value?.parentElement?.closest("button, a, [role=button]"));
});

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

onBeforeUnmount(() => {
  leave();
  if (open.value) openNote.value = null;
});
</script>

<template>
  <!-- Sans description (texte vide), le libellé reste simple. -->
  <template v-if="!text">
    <slot />
  </template>
  <span
    v-else
    ref="root"
    class="hover-note"
    :aria-description="text"
    data-test="hover-note"
    @pointerenter="enter"
    @pointerleave="leave"
  >
    <slot />
    <button
      v-if="phone && !inControl"
      type="button"
      class="hover-note-info"
      aria-label="Aide"
      :aria-expanded="open"
      data-test="hover-note-info"
      @click.prevent.stop="toggle"
    >
      <span aria-hidden="true">i</span>
    </button>
    <span
      v-if="phone && open"
      class="hover-note-line"
      data-test="hover-note-line"
    >{{ text }}</span>
    <span
      v-if="shown"
      class="hover-note-bubble"
      aria-hidden="true"
      data-test="hover-note-text"
    >{{ text }}</span>
  </span>
</template>
