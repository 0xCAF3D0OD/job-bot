<script setup lang="ts">
import type { Today } from "../../api/client";
import { formatMonth } from "../../format";
import OrpMonth from "../OrpMonth.vue";

// « Objectif ORP » (docs/54 §2) : le mois en cours comme dans Aujourd'hui (docs/123 §2, Q :
// la tuile du visage, les segments, la phrase), puis trois cases pour les mois précédents.
const props = defineProps<{ count: number; target: number | null; month: string; history: Today["orp_history"] }>();

function result(count: number): { text: string; tone: string } {
  if (!props.target) return { text: count ? "envoyées" : "aucune", tone: "" };
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
    <OrpMonth
      title="Objectif ORP"
      :sub="formatMonth(month)"
      :count="count"
      :target="target"
      :month="month"
    />
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
