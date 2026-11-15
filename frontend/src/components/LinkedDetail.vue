<script lang="ts">
import type { FunctionalComponent } from "vue";

// Sans liste reliée (téléphone, tablette) : le détail tel quel, sans zone.
export const Plain: FunctionalComponent<{ list?: HTMLElement | null }> = (_props, { slots }) => slots.default?.();
Plain.props = ["list"];
</script>

<script setup lang="ts">
import { ref, toRef, useId } from "vue";

import { useLinkedNotch } from "../composables/useLinkedNotch";

// La zone de détail reliée à la liste (Candidatures sur ordinateur, maquette du 15 novembre, §11) : pas de fond ni de
// cadre, un trait de 1,5 px à gauche et en haut (coin de 24), qui s'efface en dégradé sur 160 px à droite ; un fondu de
// 72 px en bas ; l'encoche creusée dans le trait gauche en face de la flèche de la carte choisie (tracés de la planche,
// data-notch). Le trait, l'encoche et les fondus restent fixes : seul le contenu défile.
const props = defineProps<{ list: HTMLElement | null }>();
const zone = ref<HTMLElement | null>(null);
const { top, visible } = useLinkedNotch(toRef(props, "list"), zone);
const id = useId();
</script>

<template>
  <div
    ref="zone"
    class="linked-detail"
  >
    <svg
      v-show="visible"
      data-notch
      aria-hidden="true"
      class="linked-notch"
      width="24"
      height="43"
      viewBox="0 0 24 43"
      :style="{ top: `${top}px` }"
    >
      <defs>
        <filter
          :id="`${id}-halo`"
          x="-200%"
          y="-100%"
          width="500%"
          height="300%"
        ><feGaussianBlur stdDeviation="5" /></filter>
        <clipPath :id="`${id}-clip`"><rect
          x="0.75"
          y="-30"
          width="60"
          height="103"
        /></clipPath>
      </defs>
      <g :clip-path="`url(#${id}-clip)`"><path
        class="linked-notch-halo"
        d="M0.75 -4 L17.5 18.8 Q19.9 21.3 17.5 23.8 L0.75 46.6"
        fill="none"
        stroke-width="10"
        :filter="`url(#${id}-halo)`"
      /></g>
      <path
        class="linked-notch-fill"
        d="M-1 -2 L0.75 0 L17.5 18.8 Q19.9 21.3 17.5 23.8 L0.75 42.6 L-1 44.6 Z"
      />
      <path
        class="linked-notch-line"
        d="M0.75 0 L17.5 18.8 Q19.9 21.3 17.5 23.8 L0.75 42.6"
        fill="none"
        stroke-width="1.5"
        stroke-linejoin="round"
        stroke-linecap="round"
      />
    </svg>
    <div
      class="linked-fade-top"
      aria-hidden="true"
    />
    <div
      class="linked-fade-bottom"
      aria-hidden="true"
    />
    <div class="linked-scroll">
      <slot />
    </div>
  </div>
</template>

<style>
/* Valeurs de la planche CandidaturesOrdinateurB (onglets Offres et Envoyées) : la zone commence 18 px avant la fin de
   la colonne liste (532 px) ; contenu à 24 px du trait, 16 px entre les cartes, 48 px sous la dernière. Halo de
   l'encoche : --primary-graphic à 26 % (22 % en sombre), côté zone seulement. */
.linked-detail {
  --linked-r: 24px; --linked-w: 1.5px; --linked-fade-x: 160px; --linked-fade-y: 72px; --linked-into: -18px; --linked-halo: 0.26;
  position: relative; z-index: 0; display: flex; flex: 1; flex-direction: column; min-width: 0; min-height: 0; margin-left: var(--linked-into);
  border-top: var(--linked-w) solid var(--linked-line); border-left: var(--linked-w) solid var(--linked-line); border-top-left-radius: var(--linked-r);
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) .linked-detail { --linked-halo: 0.22; } }
:root[data-theme="dark"] .linked-detail { --linked-halo: 0.22; }
.linked-notch { position: absolute; left: calc(-1 * var(--linked-w)); z-index: 1; overflow: visible; }
.linked-notch-halo { stroke: var(--primary-graphic); stroke-opacity: var(--linked-halo); }
.linked-notch-fill { fill: var(--bg); }
.linked-notch-line { stroke: var(--linked-line); }
.linked-fade-top { position: absolute; top: calc(-1 * var(--linked-w)); right: 0; z-index: 2; width: var(--linked-fade-x); height: 2px; background: linear-gradient(90deg, transparent, var(--bg)); }
.linked-fade-bottom { position: absolute; left: -2px; right: 0; bottom: 0; z-index: 2; height: var(--linked-fade-y); background: linear-gradient(180deg, transparent, var(--bg) 85%); pointer-events: none; }
.linked-scroll { flex: 1; min-height: 0; overflow-y: auto; display: flex; flex-direction: column; gap: var(--space-4); padding: 0 0 var(--space-12) var(--space-6); }
/* La liste reliée (OffersView, ApplicationsView) : colonne de 532 px, cartes de 480 px à 52 px de la zone ; la barre
   de recherche et de filtres collée en haut (son fond couvre la carte choisie, 28 px de plus, sans toucher le trait de
   la zone, 18 px avant la fin de la colonne), seules les cartes défilent dessous, avec une ombre légère dès que la liste
   a défilé. La carte choisie s'allonge de 28 px vers la droite (fond --linked-selected-bg, contour de 2 px, sans
   ombre) et porte la flèche ; masquée quand son centre sort de la partie visible (data-arrow-off). */
:is(.offers-grid, .jobs-body) > .linked-list {
  --linked-col: 532px; --linked-gap: 52px; --linked-grow: 28px; --linked-room: 3px;
  position: relative; z-index: 2; flex: none; box-sizing: border-box; width: calc(var(--linked-col) + var(--linked-room)); min-height: 0;
  overflow-y: auto; margin: calc(-1 * var(--linked-room)) 0 0 calc(-1 * var(--linked-room)); padding: var(--linked-room) var(--linked-gap) var(--space-3) var(--linked-room);
}
.linked-list > [data-linked-tools] {
  --linked-cover: 32px;
  position: sticky; top: calc(-1 * var(--linked-room)); z-index: 3; margin: calc(-1 * var(--linked-room)) calc(-1 * var(--linked-cover)) 0 calc(-1 * var(--linked-room));
  padding: var(--linked-room) var(--linked-cover) var(--space-1) var(--linked-room); background: var(--bg);
}
.linked-list[data-scrolled] > [data-linked-tools] { box-shadow: 0 10px 12px -12px rgb(27 31 42 / 35%); }
.linked-list .list-card[aria-current="true"] { position: relative; margin-right: calc(-1 * var(--linked-grow)); background: var(--linked-selected-bg); box-shadow: none; }
.linked-list .list-card-arrow { --linked-arrow: 22px; display: block; position: absolute; top: 50%; right: calc(-1 * var(--linked-arrow)); margin-top: calc(-1 * var(--linked-arrow)); overflow: visible; }
.linked-list[data-arrow-off] .list-card-arrow { visibility: hidden; }
.list-card-arrow-fill { fill: var(--linked-selected-bg); }
.list-card-arrow-line { stroke: var(--primary-graphic); }
</style>
