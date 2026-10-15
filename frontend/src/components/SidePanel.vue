<script setup lang="ts">
import { nextTick, onBeforeUnmount, ref, watch } from "vue";

import HelpTip from "./HelpTip.vue";

// Panneau latéral (docs/32 §2.2) : le contenu long et secondaire glisse depuis la droite,
// la page dessous ne bouge pas. Fermeture par ×, Échap ou clic à côté. Le contenu reste
// monté une fois la page ouverte (comptes, formulaires en cours).
const props = defineProps<{ open: boolean; title: string; help?: string }>();
const emit = defineEmits<{ close: [] }>();

const closeButton = ref<HTMLButtonElement | null>(null);
let returnTo: HTMLElement | null = null;
let locked = false;

// La page derrière ne défile plus tant qu'un panneau est ouvert (retour du 2026-10-15) :
// sa barre de défilement n'a pas de sens à côté du panneau.
function lockPage(lock: boolean): void {
  if (lock === locked) return;
  locked = lock;
  openPanels += lock ? 1 : -1;
  document.documentElement.classList.toggle("side-open", openPanels > 0);
}

function onKey(event: KeyboardEvent): void {
  if (event.key === "Escape") emit("close");
}

watch(
  () => props.open,
  async (open) => {
    lockPage(open);
    if (open) {
      returnTo = document.activeElement as HTMLElement | null;
      document.addEventListener("keydown", onKey);
      await nextTick();
      closeButton.value?.focus();
    } else {
      document.removeEventListener("keydown", onKey);
      returnTo?.focus?.();
      returnTo = null;
    }
  },
  { immediate: true },
);
onBeforeUnmount(() => {
  document.removeEventListener("keydown", onKey);
  lockPage(false);
});
</script>

<script lang="ts">
let openPanels = 0;
</script>

<template>
  <Teleport to="body">
    <Transition
      name="side-fade"
      appear
    >
      <div
        v-show="open"
        class="side-backdrop"
        data-test="side-backdrop"
        @click="emit('close')"
      />
    </Transition>
    <Transition
      name="side-slide"
      appear
    >
      <aside
        v-show="open"
        class="side-panel"
        role="dialog"
        :aria-label="title"
        data-test="side-panel"
      >
        <header class="side-panel-head">
          <h2>{{ title }}</h2>
          <HelpTip
            v-if="help"
            :text="help"
          />
          <button
            ref="closeButton"
            type="button"
            class="assistant-close"
            aria-label="Fermer"
            data-test="side-close"
            @click="emit('close')"
          >
            ×
          </button>
        </header>
        <div class="side-panel-body">
          <slot />
        </div>
      </aside>
    </Transition>
  </Teleport>
</template>
