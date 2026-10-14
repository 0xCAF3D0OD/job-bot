<script setup lang="ts">
import { computed, ref, watch } from "vue";

// Courbe des notes (docs/27 §3) : nombre d'offres par tranche de 5 points, lissée ; la partie
// choisie est la MÊME courbe, découpée entre les deux poignées, en vert.
const props = defineProps<{ bins: number[]; min: number | null; max: number | null; unscored: number }>();
const emit = defineEmits<{ change: [min: number | null, max: number | null] }>();

const WIDTH = 300;
const HEIGHT = 72;
const BASE = 64;

const low = ref(props.min ?? 0);
const high = ref(props.max ?? 100);
watch(
  () => [props.min, props.max],
  () => {
    low.value = props.min ?? 0;
    high.value = props.max ?? 100;
  },
);

const total = computed(() => props.bins.reduce((n, c) => n + c, 0));

// Lissage léger (moyenne pondérée sur les tranches voisines) : une forme douce plutôt que
// des pics, comme le modèle ; la hauteur reste proportionnelle au nombre d'offres.
const KERNEL = [1, 2, 3, 2, 1];
const smoothed = computed(() =>
  props.bins.map((_, index) => {
    let sum = 0;
    let weight = 0;
    KERNEL.forEach((k, offset) => {
      const value = props.bins[index + offset - 2];
      if (value !== undefined) {
        sum += value * k;
        weight += k;
      }
    });
    return weight ? sum / weight : 0;
  }),
);

// Courbe de Catmull-Rom convertie en Bézier : passe par chaque tranche, sans angles.
const path = computed(() => {
  const values = smoothed.value;
  const peak = Math.max(0.001, ...values);
  const points: [number, number][] = [[0, BASE]];
  values.forEach((count, index) => {
    points.push([((index + 0.5) / values.length) * WIDTH, BASE - (count / peak) * (BASE - 6)]);
  });
  points.push([WIDTH, BASE]);
  let d = `M${points[0]![0]},${points[0]![1]}`;
  for (let i = 0; i < points.length - 1; i += 1) {
    const p0 = points[i - 1] ?? points[i]!;
    const p1 = points[i]!;
    const p2 = points[i + 1]!;
    const p3 = points[i + 2] ?? p2;
    const c1 = [p1[0] + (p2[0] - p0[0]) / 6, Math.min(BASE, p1[1] + (p2[1] - p0[1]) / 6)];
    const c2 = [p2[0] - (p3[0] - p1[0]) / 6, Math.min(BASE, p2[1] - (p3[1] - p1[1]) / 6)];
    d += ` C${c1[0]!.toFixed(1)},${c1[1]!.toFixed(1)} ${c2[0]!.toFixed(1)},${c2[1]!.toFixed(1)} ${p2[0].toFixed(1)},${p2[1].toFixed(1)}`;
  }
  return `${d} Z`;
});

const left = computed(() => (low.value / 100) * WIDTH);
const right = computed(() => (high.value / 100) * WIDTH);
const clipId = `score-curve-${Math.random().toString(36).slice(2, 8)}`;

function clamp(value: number): number {
  return Math.max(0, Math.min(100, Math.round(value)));
}

function commit(): void {
  const a = clamp(Math.min(low.value, high.value));
  const b = clamp(Math.max(low.value, high.value));
  low.value = a;
  high.value = b;
  emit("change", a > 0 ? a : null, b < 100 ? b : null);
}

function onLow(event: Event): void {
  low.value = Math.min(Number((event.target as HTMLInputElement).value), high.value);
}
function onHigh(event: Event): void {
  high.value = Math.max(Number((event.target as HTMLInputElement).value), low.value);
}
function onField(which: "low" | "high", event: Event): void {
  const value = clamp(Number((event.target as HTMLInputElement).value) || 0);
  if (which === "low") low.value = value;
  else high.value = value;
  commit();
}
</script>

<template>
  <div
    class="score-curve"
    data-test="score-curve"
  >
    <template v-if="total">
      <svg
        :viewBox="`0 0 ${WIDTH} ${HEIGHT}`"
        preserveAspectRatio="none"
        role="img"
        aria-label="Répartition des notes des offres affichées"
      >
        <defs>
          <clipPath :id="clipId">
            <rect
              :x="left"
              y="0"
              :width="Math.max(0, right - left)"
              :height="HEIGHT"
            />
          </clipPath>
        </defs>
        <path
          :d="path"
          class="curve-all"
        />
        <path
          :d="path"
          class="curve-chosen"
          :clip-path="`url(#${clipId})`"
          data-test="curve-chosen"
        />
        <line
          x1="0"
          :y1="BASE"
          :x2="WIDTH"
          :y2="BASE"
          class="curve-axis"
        />
        <line
          :x1="left"
          :y1="BASE"
          :x2="right"
          :y2="BASE"
          class="curve-axis chosen"
        />
      </svg>
      <div class="dual-range">
        <input
          type="range"
          min="0"
          max="100"
          step="5"
          :value="low"
          aria-label="Note minimale"
          data-test="score-low"
          @input="onLow"
          @change="commit"
        >
        <input
          type="range"
          min="0"
          max="100"
          step="5"
          :value="high"
          aria-label="Note maximale"
          data-test="score-high"
          @input="onHigh"
          @change="commit"
        >
      </div>
    </template>
    <p
      v-else
      class="hint"
    >
      Aucune offre notée pour l'instant.
    </p>
    <div class="score-fields">
      <input
        type="number"
        min="0"
        max="100"
        :value="low"
        aria-label="Note minimale"
        data-test="score-min-field"
        @change="onField('low', $event)"
      >
      <span aria-hidden="true">–</span>
      <input
        type="number"
        min="0"
        max="100"
        :value="high"
        aria-label="Note maximale"
        data-test="score-max-field"
        @change="onField('high', $event)"
      >
    </div>
    <p
      v-if="unscored"
      class="hint"
    >
      {{ unscored }} offre{{ unscored > 1 ? "s" : "" }} pas encore notée{{ unscored > 1 ? "s" : "" }} :
      {{ low > 0 || high < 100 ? "masquées" : "visibles" }}
    </p>
  </div>
</template>
