<script setup lang="ts">
import { computed, useId } from "vue";

// Le cercle liquide de l'ORP (D6, 2026-11-02 ; maquettes AccueilSmile et Orp) : l'eau monte selon la part
// faite, « x/y » toujours écrit au centre. L'eau monte une fois et la vague passe deux fois (D9) ; rien ne
// bouge si l'appareil demande moins d'animations.
const props = defineProps<{ count: number; target: number; size?: number }>();

const clip = `liquid-${useId()}`;
const share = computed(() => (props.target > 0 ? Math.min(1, props.count / props.target) : 0));
// Le niveau de l'eau dans le cercle (rayon 44, centré en 50) : de 94 (vide) à 6 (plein).
const level = computed(() => 94 - share.value * 88);
const label = computed(() => `${props.count} recherches sur ${props.target}`);
// Une vague régulière, deux fois plus large que le cercle, qui glisse d'une période.
const WAVE = `M -100 0 ${"q 12.5 -3 25 0 q 12.5 3 25 0 ".repeat(6)}L 200 120 L -100 120 Z`;
</script>

<template>
  <svg
    class="liquid-circle"
    :width="size ?? 104"
    :height="size ?? 104"
    viewBox="0 0 100 100"
    role="img"
    :aria-label="label"
    data-test="liquid-circle"
  >
    <defs>
      <clipPath :id="clip">
        <circle
          cx="50"
          cy="50"
          r="44"
        />
      </clipPath>
    </defs>
    <circle
      class="liquid-circle-bg"
      cx="50"
      cy="50"
      r="44"
    />
    <g :clip-path="`url(#${clip})`">
      <g class="liquid-circle-rise">
        <g :transform="`translate(0 ${level})`">
          <path
            class="liquid-circle-wave"
            :d="WAVE"
          />
        </g>
      </g>
    </g>
    <circle
      class="liquid-circle-ring"
      cx="50"
      cy="50"
      r="44"
    />
    <text
      x="50"
      y="59"
      text-anchor="middle"
      aria-hidden="true"
    >{{ count }}/{{ target }}</text>
  </svg>
</template>

<style>
/* Sorti de style.css (allègement du 16.11, issue #797) : ces règles ne servent qu'ici, chargées avec ce composant. */
.liquid-circle { flex: none; }
.liquid-circle-ring { fill: none; stroke: var(--primary-graphic); stroke-width: 3.5; }
.liquid-circle-wave { fill: var(--water); stroke: var(--primary-graphic); stroke-width: 2.5; animation: liquid-wave 1.4s linear 2; }
.liquid-circle-rise { animation: liquid-rise 1.2s var(--ease-standard) both; }
.liquid-circle text { font-size: var(--font-figure); font-weight: var(--weight-bold); fill: var(--text); stroke: var(--surface); stroke-width: 4.5; paint-order: stroke; }
@media (prefers-reduced-motion: reduce) {
.liquid-circle-wave, .liquid-circle-rise { animation: none; }
}
</style>
