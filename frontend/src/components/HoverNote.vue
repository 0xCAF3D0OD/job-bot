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
// montre une courte bulle après 3 secondes de souris immobile dessus, et tout de suite au focus
// clavier (sur le libellé lui-même, ou sur le bouton ou le lien qui le contient). WCAG 1.4.13 :
// Échap la ferme sans bouger la souris ni le focus ; la souris peut passer sur la bulle sans
// qu'elle disparaisse ; elle reste tant que la souris ou le focus sont là. Les lecteurs d'écran
// la lisent avec le libellé (aria-description), sans qu'elle s'ajoute au texte d'un titre.
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
// Le bouton ou le lien qui contient le libellé : son focus clavier montre la bulle.
let control: HTMLElement | null = null;
onMounted(() => {
  control = root.value?.parentElement?.closest<HTMLElement>("button, a, [role=button]") ?? null;
  inControl.value = Boolean(control);
  control?.addEventListener("focusin", focusIn);
  control?.addEventListener("focusout", focusOut);
  document.addEventListener("keydown", onKeydown);
});

const DELAY_MS = 3000;
// Le temps de passer du libellé à la bulle sans qu'elle se ferme.
const GRACE_MS = 300;
const shown = ref(false);
let timer: ReturnType<typeof setTimeout> | null = null;
let hideTimer: ReturnType<typeof setTimeout> | null = null;
let hovered = false;
let focused = false;

function clearTimers(): void {
  if (timer) clearTimeout(timer);
  if (hideTimer) clearTimeout(hideTimer);
  timer = hideTimer = null;
}

function enter(event: PointerEvent): void {
  if (event.pointerType !== "mouse") return;
  hovered = true;
  if (hideTimer) clearTimeout(hideTimer);
  hideTimer = null;
  if (shown.value || timer) return;
  timer = setTimeout(() => {
    timer = null;
    shown.value = true;
  }, DELAY_MS);
}

function leave(): void {
  hovered = false;
  if (timer) clearTimeout(timer);
  timer = null;
  if (focused) return;
  hideTimer = setTimeout(() => (shown.value = false), GRACE_MS);
}

function keyboardFocus(target: HTMLElement | null): boolean {
  try {
    return Boolean(target?.matches(":focus-visible"));
  } catch {
    return true;
  }
}

function focusIn(event: FocusEvent): void {
  // Seulement le focus clavier : un clic sur le bouton n'ouvre pas la bulle.
  if (!keyboardFocus(event.target as HTMLElement | null)) return;
  focused = true;
  clearTimers();
  shown.value = true;
}

function focusOut(): void {
  focused = false;
  if (!hovered) shown.value = false;
}

// Échap ferme la bulle, sans bouger la souris ni le focus (WCAG 1.4.13).
function onKeydown(event: KeyboardEvent): void {
  if (event.key === "Escape" && shown.value) {
    clearTimers();
    shown.value = false;
  }
}

onBeforeUnmount(() => {
  clearTimers();
  control?.removeEventListener("focusin", focusIn);
  control?.removeEventListener("focusout", focusOut);
  document.removeEventListener("keydown", onKeydown);
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
    :tabindex="!phone && !inControl ? 0 : undefined"
    data-test="hover-note"
    @pointerenter="enter"
    @pointerleave="leave"
    @focusin="!inControl && focusIn($event)"
    @focusout="!inControl && focusOut()"
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
