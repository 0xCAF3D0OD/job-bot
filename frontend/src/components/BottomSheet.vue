<script lang="ts">
// La feuille ouverte en ce moment (une seule à la fois, §45 du 17.11).
let active: { id: string; handOver: () => HTMLElement | null } | null = null;
// Un nom propre à chaque feuille (useId se répète d’une application de test à l’autre).
let serial = 0;
</script>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, useId, watch } from "vue";

import { enterEntry, leaveEntry, useEntryTracker } from "../filterHistory";
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
// `labelledBy` : la feuille dessine son propre en-tête (ActionsOffre, §17 du 15 novembre) ; pas de titre ni de croix,
// le nom vient de l’élément désigné.
// Îlot du 17 novembre (LISEZMOI §45 et §46, Kevin 17.11) : sur téléphone, la feuille flotte à 8 px des bords et du bas,
// rayon 28 px, fond blanc (#221E1A en sombre, avec un trait). `size` : « fit » (par défaut) épouse son contenu, sans
// poignée ; « medium » prend la moitié de la hauteur visible, poignée, glisser vers le haut l’agrandit ; « large »
// monte jusqu’à 64 px du haut, poignée. La poignée est un bouton (« Agrandir » / « Réduire »), au clic et au clavier.
// Une seule feuille ouverte à la fois : en ouvrir une ferme la précédente. `modeless` (« Pourquoi » du CV) : sans voile,
// aria-modal="false", la page reste utilisable ; le focus entre dans la feuille et Échap la ferme.
const props = withDefaults(
  defineProps<{
    open: boolean;
    title: string;
    subtitle?: string;
    eyebrow?: string;
    full?: boolean;
    icon?: IconName | "";
    labelledBy?: string;
    size?: "fit" | "medium" | "large";
    modeless?: boolean;
  }>(),
  {
    subtitle: "",
    eyebrow: "",
    labelledBy: "",
    full: false,
    icon: "",
    size: "fit",
    modeless: false,
  },
);
const emit = defineEmits<{ close: [] }>();
const dialog = ref<HTMLDialogElement | null>(null);
const titleId = useId();
const key = `sheet-${(serial += 1)}`;
let returnTo: HTMLElement | null = null;
// Sous l'en-tête : le haut du panneau suit le bas de l'en-tête (et du bandeau de la démo, s'il est là).
const top = ref(0);
function measureTop(): void {
  const header = document.querySelector<HTMLElement>("[data-test=app-header]");
  top.value = Math.max(0, header?.getBoundingClientRect().bottom ?? 0);
}

// La hauteur du moment : « medium » ou « large » (la poignée passe de l’une à l’autre). « fit » n’en a pas.
const height = ref<"medium" | "large">(props.size === "large" ? "large" : "medium");
const handle = computed(() => props.size !== "fit" && !props.full && !props.icon);
function setHeight(next: "medium" | "large"): void {
  height.value = next;
}
function onHandleKey(event: KeyboardEvent): void {
  if (event.key === "ArrowUp") setHeight("large");
  else if (event.key === "ArrowDown") setHeight("medium");
  else return;
  event.preventDefault();
}

// Le bouton retour : une entrée d'historique (même adresse, même état du routeur) tant que la feuille est ouverte.
let historyEntry = false;
// Retour pendant l’ouverture applique aussi les choix faits dans la feuille (Kevin, 17.11, filterHistory.ts).
const tracker = useEntryTracker();
function onPopState(): void {
  if (!historyEntry) return;
  historyEntry = false;
  tracker.reapply();
  emit("close");
}
function pushEntry(inherited: boolean): void {
  if (!enterEntry(key, inherited)) return;
  tracker.start();
  historyEntry = true;
  window.addEventListener("popstate", onPopState);
}
// Fermer applique : les filtres choisis restent (filterHistory.ts, Kevin 17.11).
function dropEntry(): void {
  window.removeEventListener("popstate", onPopState);
  tracker.stop();
  if (!historyEntry) return;
  historyEntry = false;
  leaveEntry(key);
}

// Une seule feuille à la fois : la nouvelle reprend l’entrée d’historique et le bouton d’origine de la précédente.
let handedOver = false;
function handOver(): HTMLElement | null {
  window.removeEventListener("popstate", onPopState);
  tracker.stop();
  historyEntry = false;
  handedOver = true;
  emit("close");
  return returnTo;
}
function release(): void {
  if (active?.id === key) active = null;
}

// Le glissement : la feuille suit le doigt ; au-delà de 80 px vers le bas, elle se ferme ; vers le haut, une feuille
// « medium » passe en « large ».
const DRAG_CLOSE = 80;
const DRAG_GROW = 40;
const dragY = ref(0);
let dragStart: number | null = null;
let dragUp = 0;
function onDragStart(event: PointerEvent): void {
  const target = event.target as HTMLElement;
  if (target.closest("button") && !target.closest(".sheet-handle")) return;
  dragStart = event.clientY;
  dragUp = 0;
  (event.currentTarget as HTMLElement).setPointerCapture?.(event.pointerId);
}
function onDragMove(event: PointerEvent): void {
  if (dragStart === null) return;
  const delta = event.clientY - dragStart;
  dragY.value = Math.max(0, delta);
  dragUp = Math.max(0, -delta);
}
function onDragEnd(): void {
  if (dragStart === null) return;
  const far = dragY.value > DRAG_CLOSE;
  const grow = handle.value && dragUp > DRAG_GROW;
  dragStart = null;
  dragY.value = 0;
  dragUp = 0;
  if (far) emit("close");
  else if (grow) setHeight("large");
}

const FOCUSABLE = "a[href], button, input, select, textarea, [tabindex]:not([tabindex='-1'])";
function stopsIn(el: HTMLElement): HTMLElement[] {
  return [...el.querySelectorAll<HTMLElement>(FOCUSABLE)].filter(
    (stop) => !stop.hasAttribute("disabled") && !stop.closest("[hidden], [inert]") && (stop.checkVisibility?.() ?? true),
  );
}

watch(
  () => props.open,
  async (open) => {
    await nextTick();
    const el = dialog.value;
    if (!el) return;
    if (open && !el.open) {
      returnTo = document.activeElement as HTMLElement | null;
      handedOver = false;
      height.value = props.size === "large" ? "large" : "medium";
      const previous = active;
      active = { id: key, handOver };
      const inherited = previous && previous.id !== key ? previous.handOver() : null;
      if (inherited) returnTo = inherited;
      if (props.icon) measureTop();
      if (props.modeless) {
        if (typeof el.show === "function") el.show();
        else el.setAttribute("open", "");
        // Sans fenêtre modale, le navigateur ne déplace pas le focus : on l’amène dans la feuille.
        (stopsIn(el)[0] ?? el).focus?.();
      } else if (typeof el.showModal === "function") el.showModal();
      else el.setAttribute("open", "");
      pushEntry(Boolean(previous && previous.id !== key));
    } else if (!open && el.open) {
      if (typeof el.close === "function") el.close();
      else el.removeAttribute("open");
      release();
      dropEntry();
      if (!handedOver) returnTo?.focus?.();
    }
  },
  { immediate: true },
);
// Retirée encore ouverte (v-if) : la fermer d'abord, sinon la page reste inerte et le focus ne revient pas.
onBeforeUnmount(() => {
  const el = dialog.value;
  const wasOpen = Boolean(el?.open);
  if (el?.open && typeof el.close === "function") el.close();
  release();
  dropEntry();
  if (wasOpen && !handedOver) returnTo?.focus?.();
});

// La tabulation tourne dans la feuille : après le dernier contrôle, le premier (et l’inverse avec Maj), au lieu de
// partir vers la barre du navigateur (WCAG 2.4.3). Sans voile (`modeless`), la tabulation peut sortir.
function onTab(event: KeyboardEvent): void {
  const el = dialog.value;
  if (!el || props.modeless) return;
  const stops = stopsIn(el);
  const first = stops[0];
  const last = stops[stops.length - 1];
  if (!first || !last) return;
  const at = document.activeElement;
  if (event.shiftKey ? at === first || at === el : at === last) {
    event.preventDefault();
    (event.shiftKey ? last : first).focus();
  }
}

// Une feuille sans voile n’a pas d’événement « cancel » : Échap la ferme ici.
function onEscape(event: KeyboardEvent): void {
  if (!props.modeless) return;
  event.preventDefault();
  emit("close");
}

// Un toucher sur le voile (hors du contenu) ferme la feuille.
function onClick(event: MouseEvent): void {
  if (event.target === dialog.value && !props.modeless) emit("close");
}
</script>

<template>
  <dialog
    ref="dialog"
    :class="['sheet', `sheet-${size}`, handle ? `sheet-h-${height}` : '', { 'sheet-full': full, 'sheet-panel': icon, 'sheet-modeless': modeless }]"
    :aria-labelledby="labelledBy || titleId"
    :aria-modal="modeless ? 'false' : 'true'"
    :style="{ ...(dragY ? { transform: `translateY(${dragY}px)` } : {}), ...(icon ? { '--sheet-top': `${top}px` } : {}) }"
    data-test="sheet"
    @cancel.prevent="emit('close')"
    @click="onClick"
    @keydown.tab="onTab"
    @keydown.esc="onEscape"
  >
    <div class="sheet-inner">
      <button
        v-if="handle"
        type="button"
        class="sheet-handle"
        :aria-label="height === 'large' ? 'Réduire' : 'Agrandir'"
        :aria-expanded="height === 'large' ? 'true' : 'false'"
        data-test="sheet-handle"
        @click="setHeight(height === 'large' ? 'medium' : 'large')"
        @keydown="onHandleKey"
        @pointerdown="onDragStart"
        @pointermove="onDragMove"
        @pointerup="onDragEnd"
        @pointercancel="onDragEnd"
      />
      <header
        v-if="!labelledBy"
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
        <slot name="lead" />
        <div class="sheet-heading">
          <!-- Au-dessus du titre, en petit (« Changement 2 sur 4 », §37 du 16.11). -->
          <span
            v-if="eyebrow"
            class="sheet-eyebrow"
            data-test="sheet-eyebrow"
          >{{ eyebrow }}</span>
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

<style>
/* Sorti de style.css (allègement du 16.11, issue #797) : ces règles ne servent qu'ici, chargées avec ce composant. */
.sheet-panel { --panel-radius: 24px; --panel-pad-x: 22px; --panel-pad-y: 20px; --panel-badge: 48px; --panel-title: var(--panel-title-size); --panel-head-gap: 14px; --panel-head-pad: 18px; --panel-icon: 22px; }
@media (min-width: 821px) {
.sheet.sheet-panel .sheet-head { min-height: 0; }
}
</style>
