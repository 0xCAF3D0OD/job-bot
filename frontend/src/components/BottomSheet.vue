<script setup lang="ts">
import { nextTick, onBeforeUnmount, ref, useId, watch } from "vue";

import AppIcon from "./AppIcon.vue";

// La feuille du bas (règles §4, Material 3 « bottom sheets ») : filtres d'Offres, menu « ⋯ », choix
// d'une date. Titre à gauche, ✕ rond à droite, action principale en bas (slot `actions`). Une
// <dialog> modale : le focus reste dedans, Échap et un toucher sur le voile la ferment, la page
// derrière est inerte. Sur ordinateur, elle s'ouvre au centre. `full` : en plein écran sur téléphone
// (la cloche).
const props = withDefaults(defineProps<{ open: boolean; title: string; full?: boolean }>(), { full: false });
const emit = defineEmits<{ close: [] }>();
const dialog = ref<HTMLDialogElement | null>(null);
const titleId = useId();
let returnTo: HTMLElement | null = null;

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
    } else if (!open && el.open) {
      if (typeof el.close === "function") el.close();
      else el.removeAttribute("open");
      returnTo?.focus?.();
    }
  },
  { immediate: true },
);
onBeforeUnmount(() => returnTo?.focus?.());

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
    data-test="sheet"
    @cancel.prevent="emit('close')"
    @click="onClick"
  >
    <div class="sheet-inner">
      <header class="sheet-head">
        <h2
          :id="titleId"
          class="sheet-title"
        >
          {{ title }}
        </h2>
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
