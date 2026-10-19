<script setup lang="ts">
import { computed } from "vue";

import type { components } from "../api/schema";

// Ta semaine (docs/86) : la part de l'objectif ORP pour cette semaine, un point par jour, et
// une phrase qui dit où tu en es, sans reproche.
type Week = components["schemas"]["RhythmWeek"];
const props = defineProps<{ week: Week }>();

const LETTERS = ["L", "M", "M", "J", "V", "S", "D"];
const NAMES = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"];
const todayIso = (() => {
  const now = new Date();
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
})();

const longDate = new Intl.DateTimeFormat("fr-CH", { day: "numeric", month: "long" });
const done = computed(() => props.week.target !== null && props.week.count >= props.week.target);
const left = computed(() => Math.max(0, (props.week.target ?? 0) - props.week.count));
const sentence = computed(() => {
  // En pause (0.68.1) : ni dose ni retard ; l'annoncer au conseiller.
  if (props.week.pause_until) {
    return `En pause jusqu'au ${longDate.format(new Date(`${props.week.pause_until}T12:00:00`))}. Pense à l'annoncer à ton conseiller.`;
  }
  if (props.week.target === null) return "";
  if (done.value) return "Semaine faite. Le reste du temps est à toi.";
  if (!props.week.research_today) return "Jour sans recherche : rien à faire aujourd'hui.";
  return left.value === 1 ? "Encore 1 cette semaine." : `Encore ${left.value} cette semaine.`;
});

function dayLabel(day: Week["days"][number], index: number): string {
  const parts = [NAMES[index] ?? ""];
  if (day.paused) parts.push("en pause");
  else if (!day.research) parts.push("sans recherche");
  if (day.sent) parts.push(day.sent === 1 ? "1 candidature" : `${day.sent} candidatures`);
  return parts.join(", ");
}
</script>

<template>
  <section
    :class="['dash-card', 'rhythm-card', { done }]"
    data-test="rhythm"
  >
    <header class="rhythm-head">
      <h2>Ta semaine</h2>
      <p
        v-if="week.target !== null && !week.pause_until"
        class="rhythm-count"
        data-test="rhythm-count"
      >
        <strong>{{ week.count }}</strong> / {{ week.target }} {{ week.target === 1 ? "candidature" : "candidatures" }}
      </p>
    </header>
    <ol
      class="rhythm-days"
      aria-label="Les jours de la semaine"
    >
      <li
        v-for="(day, index) in week.days"
        :key="day.day"
        :class="{ rest: !day.research, paused: day.paused, sent: day.sent > 0, today: day.day === todayIso }"
        :aria-label="dayLabel(day, index)"
        :aria-current="day.day === todayIso ? 'date' : undefined"
      >
        <span
          class="rhythm-dot"
          aria-hidden="true"
        >{{ day.sent > 1 ? day.sent : "" }}</span>
        <span aria-hidden="true">{{ LETTERS[index] }}</span>
      </li>
    </ol>
    <p
      v-if="sentence"
      :class="['rhythm-sentence', { pause: week.pause_until }]"
      data-test="rhythm-sentence"
    >
      {{ sentence }}
    </p>
    <p
      v-else
      class="hint"
    >
      <RouterLink :to="{ path: '/reglages', query: { rubrique: 'recherche' } }">
        Indique ton objectif mensuel
      </RouterLink> pour le répartir sur tes semaines.
    </p>
  </section>
</template>
