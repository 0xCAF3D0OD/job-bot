<script setup lang="ts">
import { nextTick, onBeforeUnmount, ref, watch } from "vue";

import AppIcon from "./AppIcon.vue";

// Panneau latéral (docs/32 §2.2) : le contenu long et secondaire glisse depuis la droite,
// la page dessous ne bouge pas. Fermeture par la croix, Échap ou clic à côté. Le contenu reste
// monté une fois la page ouverte (comptes, formulaires en cours).
const props = defineProps<{ open: boolean; title: string }>();
const emit = defineEmits<{ close: [] }>();

const closeButton = ref<HTMLButtonElement | null>(null);
const aside = ref<HTMLElement | null>(null);
const self = Symbol("side-panel");
let returnTo: HTMLElement | null = null;
let locked = false;

// La page derrière ne défile plus tant qu'un panneau est ouvert (retour du 2026-10-15) :
// sa barre de défilement n'a pas de sens à côté du panneau.
function lockPage(lock: boolean): void {
  if (lock === locked) return;
  locked = lock;
  const index = openStack.indexOf(self);
  if (lock && index < 0) openStack.push(self);
  if (!lock && index >= 0) openStack.splice(index, 1);
  document.documentElement.classList.toggle("side-open", openStack.length > 0);
}

const FOCUSABLE =
  'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

// Tab et Maj+Tab restent dans le panneau ouvert (fenêtre modale).
function trapFocus(event: KeyboardEvent): void {
  const items = [...(aside.value?.querySelectorAll<HTMLElement>(FOCUSABLE) ?? [])];
  const first = items[0];
  const last = items[items.length - 1];
  if (!first || !last) return;
  const active = document.activeElement;
  if (event.shiftKey && (active === first || !aside.value?.contains(active))) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && (active === last || !aside.value?.contains(active))) {
    event.preventDefault();
    first.focus();
  }
}

// Seul le panneau du dessus réagit au clavier : Échap ferme celui-là, pas ceux d'en dessous
// ni l'offre ouverte dans la page.
function onKey(event: KeyboardEvent): void {
  if (openStack[openStack.length - 1] !== self) return;
  if (event.key === "Escape") {
    if (event.defaultPrevented) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    emit("close");
  } else if (event.key === "Tab") trapFocus(event);
}

function restoreFocus(): void {
  returnTo?.focus?.();
  returnTo = null;
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
      restoreFocus();
    }
  },
  { immediate: true },
);
// Panneau monté avec `v-if … open` puis démonté : le focus revient aussi à son point de départ.
onBeforeUnmount(() => {
  document.removeEventListener("keydown", onKey);
  lockPage(false);
  restoreFocus();
});
</script>

<script lang="ts">
// Panneaux ouverts, du plus ancien au plus récent : le dernier est celui du dessus.
const openStack: symbol[] = [];
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
        ref="aside"
        class="side-panel"
        role="dialog"
        aria-modal="true"
        :aria-label="title"
        data-test="side-panel"
      >
        <header class="side-panel-head">
          <h2>{{ title }}</h2>
          <!-- Le bouton de IconButton (docs/101), écrit ici pour garder la référence du focus. -->
          <button
            ref="closeButton"
            type="button"
            class="icon-button icon-only side-panel-close"
            aria-label="Fermer"
            data-label="Fermer"
            data-test="side-close"
            @click="emit('close')"
          >
            <AppIcon name="close" />
          </button>
        </header>
        <div class="side-panel-body">
          <slot />
        </div>
      </aside>
    </Transition>
  </Teleport>
</template>
