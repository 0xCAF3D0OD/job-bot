<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";

import { fitChips } from "../chipFit";
import { plural } from "../format";

// La rangée d'étiquettes d'une carte d'offre (lot du 11 novembre au soir, PR 46 ; maquettes Candidatures et
// CandidaturesOrdinateurB) : une seule ligne, sans retour, sans fondu ni défilement. Si elle déborde, les dernières
// étiquettes sont retirées et une pastille « +k » dit combien, avec le nom « k autres étiquettes ». « Gardée »,
// toujours la première, porte le petit marque-page orange et n'est jamais retirée.
export interface Chip {
  text: string;
  tone?: "peach" | "blue" | "warn" | "kept";
  title?: string;
}
const props = defineProps<{ chips: Chip[] }>();

const row = ref<HTMLElement | null>(null);
const gauge = ref<HTMLElement | null>(null);
const shown = ref(props.chips.length);
const hidden = computed(() => props.chips.length - shown.value);

// Toutes les étiquettes restent dans la page pour être mesurées ; celles qui ne tiennent pas sortent du flux,
// invisibles et hors de l'arbre d'accessibilité.
function measure(): void {
  const el = row.value;
  if (!el) return;
  const chips = [...el.querySelectorAll<HTMLElement>("[data-chip]")];
  const gap = parseFloat(getComputedStyle(el).columnGap) || 0;
  const plus = gauge.value?.offsetWidth ?? 0;
  shown.value = fitChips(chips.map((c) => c.offsetWidth), el.clientWidth, gap, () => plus);
}
let observer: ResizeObserver | undefined;
onMounted(() => {
  measure();
  if (typeof ResizeObserver === "undefined" || !row.value) return;
  observer = new ResizeObserver(measure);
  observer.observe(row.value);
  // Les polices chargées changent les largeurs.
  void document.fonts?.ready.then(measure);
});
onBeforeUnmount(() => observer?.disconnect());
watch(
  () => props.chips.map((c) => c.text).join("|"),
  () => void nextTick(measure),
);
</script>

<template>
  <span
    ref="row"
    class="list-card-chips chip-line"
    data-test="chip-line"
  >
    <span
      v-for="(chip, i) in chips"
      :key="chip.text"
      :class="[chip.tone, { 'chip-off': i >= shown }]"
      :title="chip.title"
      :aria-hidden="i >= shown ? 'true' : undefined"
      data-chip
      data-test="offer-chip"
    ><svg
      v-if="chip.tone === 'kept'"
      class="chip-kept-mark"
      viewBox="0 0 12 15"
      aria-hidden="true"
    ><path d="M1 1.5A1.5 1.5 0 0 1 2.5 0h7A1.5 1.5 0 0 1 11 1.5V15L6 11.5 1 15z" /></svg>{{ chip.text }}</span>
    <span
      v-if="hidden > 0"
      class="chip-more"
      role="img"
      :aria-label="plural(hidden, 'autre étiquette', 'autres étiquettes')"
      data-test="chip-more"
    >+{{ hidden }}</span>
    <!-- La jauge : la largeur de la pastille au plus large (« +n »), jamais affichée. -->
    <span
      ref="gauge"
      class="chip-more chip-off"
      aria-hidden="true"
    >+{{ chips.length }}</span>
  </span>
</template>

<style>
/* Maquette : « Gardée » en #FFF1E6 et #8A4A12 (sombre : #3A2A1C et #F2B98E), 12 px en 700, le marque-page de
   9 × 12 px à 4 px du mot ; la même hauteur et le même rayon que les autres étiquettes. */
.chip-line { --kept-bg: #FFF1E6; --kept-text: #8A4A12; --kept-mark: #F2853A; --kept-w: 9px; --kept-h: 12px; position: relative; flex-wrap: nowrap; white-space: nowrap; }
:root[data-theme="dark"] .chip-line { --kept-bg: #3A2A1C; --kept-text: #F2B98E; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) .chip-line { --kept-bg: #3A2A1C; --kept-text: #F2B98E; } }
.list-card-chips.chip-line > .kept { display: inline-flex; align-items: center; gap: var(--space-1); background: var(--kept-bg); color: var(--kept-text); font-weight: var(--weight-bold); }
.chip-kept-mark { flex: none; width: var(--kept-w); height: var(--kept-h); fill: var(--kept-mark); }
.list-card-chips.chip-line > .chip-more { font-weight: var(--weight-bold); }
.list-card-chips.chip-line > .chip-off { position: absolute; left: 0; top: 0; visibility: hidden; pointer-events: none; }
</style>
