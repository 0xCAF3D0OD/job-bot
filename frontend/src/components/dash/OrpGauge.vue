<script setup lang="ts">
import { computed } from "vue";

import type { Today } from "../../api/client";
import { formatMonth } from "../../format";

// « Objectif ORP » (docs/54 §2) : jauge en demi-cercle, du rouge au vert comme la maquette
// (adoucie), le compte du mois au centre ; trois cases pour les mois précédents.
const props = defineProps<{ count: number; target: number | null; month: string; history: Today["orp_history"] }>();

const SEGMENTS = 5;
const R = 80;
const CX = 100;
const CY = 96;
const GAP = 0.09;
// Arcs de 180° à 0°, de gauche à droite.
const arcs = computed(() =>
  Array.from({ length: SEGMENTS }, (_, i) => {
    const from = Math.PI - (i / SEGMENTS) * Math.PI - GAP / 2;
    const to = Math.PI - ((i + 1) / SEGMENTS) * Math.PI + GAP / 2;
    const p = (a: number) => `${(CX + R * Math.cos(a)).toFixed(1)},${(CY - R * Math.sin(a)).toFixed(1)}`;
    return { d: `M${p(i === 0 ? Math.PI : from)} A${R},${R} 0 0 1 ${p(i === SEGMENTS - 1 ? 0 : to)}`, tone: `g${i}` };
  }),
);
const share = computed(() => (props.target ? Math.min(1, props.count / props.target) : 0));
const marker = computed(() => {
  const a = Math.PI - share.value * Math.PI;
  return { x: CX + R * Math.cos(a), y: CY - R * Math.sin(a) };
});
// Où en est-on par rapport au rythme attendu à cette date du mois ?
const pace = computed(() => {
  if (!props.target) return "objectif à saisir";
  if (props.count >= props.target) return "atteint";
  const now = new Date();
  const days = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate();
  return props.count >= (props.target * now.getDate()) / days ? "dans les temps" : "à rattraper";
});
function result(count: number): { text: string; tone: string } {
  if (!props.target) return { text: count ? "envoyées" : "—", tone: "" };
  return count >= props.target ? { text: "atteint", tone: "ok" } : { text: "manqué", tone: "short" };
}
const short = (month: string): string => formatMonth(month).split(" ")[0] ?? month;
</script>

<template>
  <RouterLink
    :to="{ path: '/candidatures/suivi', query: { mois: month } }"
    class="dash-card dash-link orp-gauge"
    data-test="orp-gauge"
  >
    <header class="dash-card-head">
      <h2>Objectif ORP</h2>
      <span class="muted">{{ formatMonth(month) }}</span>
    </header>
    <div class="gauge">
      <svg
        viewBox="0 0 200 112"
        aria-hidden="true"
      >
        <path
          v-for="arc in arcs"
          :key="arc.d"
          :d="arc.d"
          :class="['gauge-arc', arc.tone]"
        />
        <circle
          v-if="target"
          :cx="marker.x"
          :cy="marker.y"
          r="7"
          class="gauge-marker"
        />
      </svg>
      <p class="gauge-value">
        <strong data-test="gauge-count">{{ count }}</strong>
        <span>{{ target ? `sur ${target} · ${pace}` : pace }}</span>
      </p>
    </div>
    <ul class="gauge-history">
      <li
        v-for="item in history"
        :key="item.month"
        :class="result(item.count).tone"
      >
        <span class="muted">{{ short(item.month) }}</span>
        <strong>{{ item.count }}</strong>
        <span>{{ result(item.count).text }}</span>
      </li>
    </ul>
  </RouterLink>
</template>
