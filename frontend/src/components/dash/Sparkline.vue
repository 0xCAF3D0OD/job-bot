<script setup lang="ts">
import { computed } from "vue";

// Petite courbe des 7 derniers jours sur une tuile (docs/54 §2), comme la maquette : une
// ligne lissée, sans axe ni chiffre.
const props = defineProps<{ values: number[] }>();
const W = 96;
const H = 32;

const path = computed(() => {
  const values = props.values.length > 1 ? props.values : [0, 0];
  const max = Math.max(...values, 1);
  const points = values.map((v, i) => [(i / (values.length - 1)) * W, H - 3 - (v / max) * (H - 6)] as const);
  return points
    .map(([x, y], i) => {
      if (i === 0) return `M${x.toFixed(1)},${y.toFixed(1)}`;
      const [px, py] = points[i - 1]!;
      const mid = (px + x) / 2;
      return `C${mid.toFixed(1)},${py.toFixed(1)} ${mid.toFixed(1)},${y.toFixed(1)} ${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
});
</script>

<template>
  <svg
    class="sparkline"
    :viewBox="`0 0 ${W} ${H}`"
    :width="W"
    :height="H"
    aria-hidden="true"
  >
    <path
      :d="path"
      fill="none"
      stroke="currentColor"
      stroke-width="1.6"
      stroke-linecap="round"
    />
  </svg>
</template>
