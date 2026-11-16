<script setup lang="ts">
import { computed, ref } from "vue";

import AppIcon from "./AppIcon.vue";

// Le curseur du tri sur téléphone (§40 du 16.11, planches TrierOffresV2, TrierOffresCurseurGauche et
// TrierOffresCurseurDroite) : une piste de 64 px, « Écarter » à gauche, « Garder » à droite, un rond de 52 px au milieu.
// Glissé vers un bout, le remplissage suit le rond à 6 px de lui et dit « Lâche pour écarter » (ou garder) ; lâché
// après la moitié du chemin, l'action est faite ; avant, le rond revient au milieu. Toucher « Écarter » ou « Garder »
// fait l'action sans glisser : ce sont deux vrais boutons, le rond est caché aux lecteurs d'écran (WCAG 2.5.7).
const emit = defineEmits<{ decide: [choice: "dismiss" | "keep"] }>();

const KNOB = 52;
const GAP = 6;
const track = ref<HTMLElement | null>(null);
const shift = ref(0);
const dragging = ref(false);
let start = 0;
let travel = 0;
let pointer: number | null = null;

const side = computed(() => (shift.value < 0 ? "dismiss" : shift.value > 0 ? "keep" : null));

function down(event: PointerEvent): void {
  if (!track.value) return;
  pointer = event.pointerId;
  (event.currentTarget as HTMLElement).setPointerCapture?.(pointer);
  start = event.clientX;
  travel = (track.value.clientWidth - KNOB) / 2 - GAP;
  dragging.value = true;
}
function move(event: PointerEvent): void {
  if (event.pointerId !== pointer) return;
  shift.value = Math.max(-travel, Math.min(travel, event.clientX - start));
}
function up(event: PointerEvent): void {
  if (event.pointerId !== pointer) return;
  pointer = null;
  dragging.value = false;
  const choice = side.value;
  const far = Math.abs(shift.value) >= travel / 2;
  shift.value = 0;
  if (choice && far) emit("decide", choice);
}
</script>

<template>
  <div
    ref="track"
    role="group"
    aria-label="Trier cette offre"
    :class="['tri-slider', side, { dragging }]"
    :style="{ '--shift': `${shift}px` }"
    data-test="triage-slider"
  >
    <button
      type="button"
      class="tri-slider-dismiss"
      aria-label="Écarter l’offre"
      aria-keyshortcuts="ArrowLeft"
      data-test="triage-dismiss"
      @click="emit('decide', 'dismiss')"
    >
      <AppIcon name="close" />Écarter
    </button>
    <button
      type="button"
      class="tri-slider-keep"
      aria-label="Garder l’offre"
      aria-keyshortcuts="ArrowRight"
      data-test="triage-keep"
      @click="emit('decide', 'keep')"
    >
      Garder<AppIcon name="bookmark" />
    </button>
    <span
      v-if="side"
      class="tri-slider-fill"
      aria-hidden="true"
    >{{ side === "keep" ? "Lâche pour garder" : "Lâche pour écarter" }}</span>
    <span
      class="tri-slider-knob"
      aria-hidden="true"
      data-test="triage-knob"
      @pointerdown="down"
      @pointermove="move"
      @pointerup="up"
      @pointercancel="up"
    ><AppIcon :name="side === 'keep' ? 'bookmark' : side === 'dismiss' ? 'close' : 'arrows'" /></span>
  </div>
</template>

<style scoped>
/* Les valeurs des planches ; 22 px de retrait des boutons ramenés à 24 (grille de 4). */
.tri-slider {
  --s-h: 64px; --s-knob: 52px; --s-gap: 6px; --s-pad: 24px; --s-16: 1rem; --s-18: 1.125rem; --s-24: 24px; --s-46: 46px;
  position: relative; height: var(--s-h); border-radius: var(--radius-pill); background: var(--surface); box-shadow: inset 0 0 0 1.5px var(--tri-card-edge); overflow: hidden; touch-action: pan-y;
}
.tri-slider button { position: absolute; top: 0; bottom: 0; display: flex; align-items: center; gap: var(--space-2); width: 50%; padding: 0; border: 0; background: transparent; font-size: var(--s-16); font-weight: var(--weight-bold); }
.tri-slider button :deep(svg) { width: var(--s-18); height: var(--s-18); }
.tri-slider .tri-slider-dismiss { left: 0; padding-left: var(--s-pad); color: var(--tri-tag-text); }
.tri-slider .tri-slider-keep { right: 0; justify-content: flex-end; padding-right: var(--s-pad); color: var(--primary-text); }
.tri-slider.dismiss .tri-slider-dismiss, .tri-slider.keep .tri-slider-keep { visibility: hidden; }
.tri-slider.dismiss .tri-slider-keep, .tri-slider.keep .tri-slider-dismiss { color: var(--tri-slide-muted); }
.tri-slider-knob {
  position: absolute; left: calc(50% - var(--s-knob) / 2); top: var(--s-gap); display: flex; align-items: center; justify-content: center;
  width: var(--s-knob); height: var(--s-knob); border-radius: 50%; background: var(--primary-graphic); color: var(--tri-slide-keep-ink); box-shadow: var(--tri-knob-shadow);
  transform: translateX(var(--shift)); transition: transform var(--t-standard) var(--ease-standard); cursor: grab; touch-action: none;
}
.tri-slider-knob :deep(svg) { width: var(--s-24); height: var(--s-24); }
.dragging .tri-slider-knob { transition: none; cursor: grabbing; }
.dismiss .tri-slider-knob { background: var(--surface); color: var(--tri-slide-out); }
.keep .tri-slider-knob { background: var(--surface); color: var(--primary-graphic); }
.tri-slider-fill { position: absolute; top: 0; bottom: 0; display: flex; align-items: center; justify-content: center; border-radius: var(--radius-pill); font-size: var(--s-16); font-weight: var(--weight-heavy); }
.dismiss .tri-slider-fill { right: 0; left: calc(50% - var(--s-knob) / 2 - var(--s-gap) + var(--shift)); padding-left: var(--s-46); background: var(--tri-slide-out); color: var(--tri-slide-out-ink); }
.keep .tri-slider-fill { left: 0; right: calc(50% - var(--s-knob) / 2 - var(--s-gap) - var(--shift)); padding-right: var(--s-46); background: var(--primary-graphic); color: var(--tri-slide-keep-ink); }
@media (prefers-reduced-motion: reduce) { .tri-slider-knob { transition: none; } }
</style>
