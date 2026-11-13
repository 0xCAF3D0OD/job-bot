<script setup lang="ts">
import { nextTick, onBeforeUnmount, ref, useId, watch } from "vue";

import type { IconName } from "../icons";
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
// `icon` (paquet du 11 novembre, PR 37) : le panneau à formulaire, au format du menu du compte. Sur ordinateur, sous
// l'en-tête, 420 px, coin haut gauche arrondi, ombre à gauche, sans voile ; en-tête à pastille ronde de 48 px, titre
// de 18 px, sous-titre de 14 px, croix de 44 px ; corps qui défile, pied fixe (slot `actions`). Sur téléphone, la même
// feuille monte du bas. Elle reste une <dialog> modale : focus bloqué dedans, rendu au bouton d'origine (WCAG 2.1.2,
// 2.4.3) ; croix, Échap et clic à l'extérieur la ferment, sans bouton « Annuler ».
const props = withDefaults(defineProps<{ open: boolean; title: string; subtitle?: string; full?: boolean; icon?: IconName | "" }>(), {
  subtitle: "",
  full: false,
  icon: "",
});
const emit = defineEmits<{ close: [] }>();
const dialog = ref<HTMLDialogElement | null>(null);
const titleId = useId();
let returnTo: HTMLElement | null = null;
// Sous l'en-tête : le haut du panneau suit le bas de l'en-tête (et du bandeau de la démo, s'il est là).
const top = ref(0);
function measureTop(): void {
  const header = document.querySelector<HTMLElement>("[data-test=app-header]");
  top.value = Math.max(0, header?.getBoundingClientRect().bottom ?? 0);
}

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
      if (props.icon) measureTop();
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

// La tabulation tourne dans la feuille : après le dernier contrôle, le premier (et l’inverse avec Maj), au lieu de
// partir vers la barre du navigateur (WCAG 2.4.3).
const FOCUSABLE = "a[href], button, input, select, textarea, [tabindex]:not([tabindex='-1'])";
function onTab(event: KeyboardEvent): void {
  const el = dialog.value;
  if (!el) return;
  const stops = [...el.querySelectorAll<HTMLElement>(FOCUSABLE)].filter(
    (stop) => !stop.hasAttribute("disabled") && !stop.closest("[hidden], [inert]") && (stop.checkVisibility?.() ?? true),
  );
  const first = stops[0];
  const last = stops[stops.length - 1];
  if (!first || !last) return;
  const at = document.activeElement;
  if (event.shiftKey ? at === first || at === el : at === last) {
    event.preventDefault();
    (event.shiftKey ? last : first).focus();
  }
}

// Un toucher sur le voile (hors du contenu) ferme la feuille.
function onClick(event: MouseEvent): void {
  if (event.target === dialog.value) emit("close");
}
</script>

<template>
  <dialog
    ref="dialog"
    :class="['sheet', { 'sheet-full': full, 'sheet-panel': icon }]"
    :aria-labelledby="titleId"
    :style="{ ...(dragY ? { transform: `translateY(${dragY}px)` } : {}), ...(icon ? { '--sheet-top': `${top}px` } : {}) }"
    data-test="sheet"
    @cancel.prevent="emit('close')"
    @click="onClick"
    @keydown.tab="onTab"
  >
    <div class="sheet-inner">
      <header
        class="sheet-head"
        @pointerdown="onDragStart"
        @pointermove="onDragMove"
        @pointerup="onDragEnd"
        @pointercancel="onDragEnd"
      >
        <span
          v-if="icon"
          class="sheet-badge"
          aria-hidden="true"
        ><AppIcon :name="icon" /></span>
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
