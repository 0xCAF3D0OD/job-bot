<script setup lang="ts">
import { onMounted, ref, watch } from "vue";

import { api } from "../api/client";
import type { components } from "../api/schema";
import { formatMonth } from "../format";

// Les semaines du mois (docs/86, 0.68.1), dans le Bilan : faites, manquées, en pause.
type Weeks = components["schemas"]["MonthWeeksOut"];
const props = defineProps<{ month: string }>();
const data = ref<Weeks | null>(null);

const day = new Intl.DateTimeFormat("fr-CH", { day: "numeric", month: "short" });
const STATES: Record<Weeks["weeks"][number]["state"], string> = {
  done: "faite",
  missed: "en dessous",
  current: "en cours",
  upcoming: "à venir",
  pause: "en pause",
};

function range(start: string, end: string): string {
  const from = new Date(`${start}T12:00:00`);
  const to = new Date(`${end}T12:00:00`);
  return start === end ? day.format(from) : `${day.format(from)} – ${day.format(to)}`;
}

async function load(): Promise<void> {
  const { data: found } = await api.GET("/api/rhythm/semaines", { params: { query: { month: props.month } } });
  data.value = found ?? null;
}

watch(() => props.month, () => void load());
onMounted(() => void load());
</script>

<template>
  <section
    v-if="data"
    class="dash-card rhythm-weeks"
    data-test="rhythm-weeks"
  >
    <header class="dash-card-head">
      <h2>Semaines</h2>
      <span class="muted">{{ formatMonth(data.month) }}</span>
    </header>
    <ol>
      <li
        v-for="week in data.weeks"
        :key="week.start"
        :class="week.state"
        :data-test="`rhythm-week-${week.state}`"
      >
        <span class="rhythm-weeks-range">{{ range(week.start, week.end) }}</span>
        <span class="rhythm-weeks-count">
          <template v-if="week.state === 'pause'">—</template>
          <template v-else-if="week.target !== null">{{ week.count }} / {{ week.target }}</template>
          <template v-else>{{ week.count }}</template>
        </span>
        <span class="rhythm-weeks-state">{{ STATES[week.state] }}</span>
      </li>
    </ol>
  </section>
</template>
