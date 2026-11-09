<script setup lang="ts">
import { nextTick, onBeforeUnmount, ref, useId, watch } from "vue";

import AppIcon from "./AppIcon.vue";

// La feuille du bas (règles §4, Material 3 « bottom sheets ») : filtres d'Offres, menu « ⋯ », choix
// d'une date. Titre à gauche, ✕ rond à droite, action principale en bas (slot `actions`). Une
// <dialog> modale : le focus reste dedans, Échap et un toucher sur le voile la ferment, la page
// derrière est inerte. Sur ordinateur, elle s'ouvre au centre. `full` : en plein écran sur téléphone
// (la cloche).
// Version du 9 novembre (MODIFICATIONS §10.1 et §10.7, maquette OffreCompatibilite) : sur téléphone, poignée, titre de
// 22 px, croix de 48 px, 24 px de marge, montée depuis le bas en 320 ms ; elle se ferme aussi par un glissement vers
// le bas (sur la poignée ou le titre) et par le bouton retour du téléphone (une entrée d'historique tant qu'elle est
// ouverte). Le focus revient au déclencheur. On n'ouvre jamais une feuille depuis une autre.
const props = withDefaults(defineProps<{ open: boolean; title: string; subtitle?: string; full?: boolean }>(), { subtitle: "", full: false });
const emit = defineEmits<{ close: [] }>();
const dialog = ref<HTMLDialogElement | null>(null);
const titleId = useId();
let returnTo: HTMLElement | null = null;

// Le bouton retour : une entrée d'historique (même adresse, même état du routeur) tant que la feuille est ouverte.
let historyEntry = false;
function onPopState(): void {
  if (!historyEntry) return;
  historyEntry = false;
  emit("close");
}
function pushEntry(): void {
  if (typeof window === "undefined" || !window.history?.pushState) return;
  window.history.pushState({ ...(window.history.state ?? {}), sheet: titleId }, "", window.location.href);
  historyEntry = true;
  window.addEventListener("popstate", onPopState);
}
function dropEntry(): void {
  window.removeEventListener("popstate", onPopState);
  if (!historyEntry) return;
  historyEntry = false;
  if (window.history.state?.sheet === titleId) window.history.back();
}

// Le glissement vers le bas : la feuille suit le doigt ; au-delà de 80 px, elle se ferme.
const DRAG_CLOSE = 80;
const dragY = ref(0);
let dragStart: number | null = null;
function onDragStart(event: PointerEvent): void {
  if ((event.target as HTMLElement).closest("button")) return;
  dragStart = event.clientY;
  (event.currentTarget as HTMLElement).setPointerCapture?.(event.pointerId);
}
function onDragMove(event: PointerEvent): void {
  if (dragStart === null) return;
  dragY.value = Math.max(0, event.clientY - dragStart);
}
function onDragEnd(): void {
  if (dragStart === null) return;
  const far = dragY.value > DRAG_CLOSE;
  dragStart = null;
  dragY.value = 0;
  if (far) emit("close");
}

watch(
  () => props.open,
  async (open) => {
    await nextTick();
    const el = dialog.value;
    if (!el) return;
    if (open && !el.open) {
      returnTo = document.activeElement as HTMLElement | null;
      if (typeof el.showModal === "function") el.showModal();
      else el.setAttribute("open", "");
      pushEntry();
    } else if (!open && el.open) {
      if (typeof el.close === "function") el.close();
      else el.removeAttribute("open");
      dropEntry();
      returnTo?.focus?.();
    }
  },
  { immediate: true },
);
// Retirée encore ouverte (v-if) : la fermer d'abord, sinon la page reste inerte et le focus ne revient pas.
onBeforeUnmount(() => {
  const el = dialog.value;
  if (el?.open && typeof el.close === "function") el.close();
  dropEntry();
  returnTo?.focus?.();
});

// Un toucher sur le voile (hors du contenu) ferme la feuille.
function onClick(event: MouseEvent): void {
  if (event.target === dialog.value) emit("close");
}
</script>

<template>
  <dialog
    ref="dialog"
    :class="['sheet', { 'sheet-full': full }]"
    :aria-labelledby="titleId"
    :style="dragY ? { transform: `translateY(${dragY}px)` } : undefined"
    data-test="sheet"
    @cancel.prevent="emit('close')"
    @click="onClick"
  >
    <div class="sheet-inner">
      <header
        class="sheet-head"
        @pointerdown="onDragStart"
        @pointermove="onDragMove"
        @pointerup="onDragEnd"
        @pointercancel="onDragEnd"
      >
        <div class="sheet-heading">
          <h2
            :id="titleId"
            class="sheet-title"
          >
            {{ title }}
          </h2>
          <p
            v-if="subtitle"
            class="sheet-subtitle"
          >
            {{ subtitle }}
          </p>
        </div>
        <button
          type="button"
          class="sheet-close"
          aria-label="Fermer"
          data-test="sheet-close"
          @click="emit('close')"
        >
          <AppIcon name="close" />
        </button>
      </header>
      <div class="sheet-body">
        <slot />
      </div>
      <footer
        v-if="$slots.actions"
        class="sheet-actions"
      >
        <slot name="actions" />
      </footer>
    </div>
  </dialog>
</template>
