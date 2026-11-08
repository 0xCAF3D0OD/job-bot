<script setup lang="ts">
import { computed } from "vue";

import type { components } from "../api/schema";
import { dateInSentence } from "../dates";

// Ta semaine (docs/86) : la part de l'objectif ORP pour cette semaine, un point par jour, et
// une phrase qui dit où tu en es, sans reproche.
type Week = components["schemas"]["RhythmWeek"];
// `nested` : dans la carte Mois ORP d'Aujourd'hui (docs/95 §4), sans cadre, un sous-titre.
// `monthBehind` : le mois ORP est en retard ; « Semaine faite » se tait alors (1.6.27).
// `band` (maquette du 8 novembre, Aujourd'hui sur ordinateur) : à droite du mois dans la carte à cheval sur la bande,
// « Cette semaine », le compte (« 4 sur 4, faite » en vert), puis les 7 ronds de 34 px. Décoratif : la carte porte la
// phrase lue.
const props = defineProps<{ week: Week; nested?: boolean; monthBehind?: boolean; band?: boolean }>();

const LETTERS = ["L", "M", "M", "J", "V", "S", "D"];
const NAMES = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"];
const todayIso = (() => {
  const now = new Date();
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
})();

const done = computed(() => props.week.target !== null && props.week.count >= props.week.target);
const left = computed(() => Math.max(0, (props.week.target ?? 0) - props.week.count));
const sentence = computed(() => {
  // En pause (0.68.1) : ni dose ni retard ; l'annoncer au conseiller.
  if (props.week.pause_until) {
    // « jusqu'au 1er novembre » : la date de phrase sans son « le », contracté dans « au ».
    const until = dateInSentence(`${props.week.pause_until}T12:00:00`).replace(/^le /, "");
    return `En pause jusqu'au ${until}. Pense à l'annoncer à ton conseiller.`;
  }
  if (props.week.target === null) return "";
  if (done.value) return props.monthBehind ? "" : "Semaine faite. Le reste du temps est à toi.";
  // Jour de repos : dans la carte d'Aujourd'hui, la phrase du haut le dit déjà (1.6.26).
  if (!props.week.research_today) return props.nested ? "" : "Jour de repos : rien à faire aujourd'hui.";
  // Dans la carte du mois (docs/129) : le compte au-dessus le dit déjà.
  if (props.nested) return "";
  return left.value === 1 ? "Encore 1 cette semaine." : `Encore ${left.value} cette semaine.`;
});

function dayLabel(day: Week["days"][number], index: number): string {
  const parts = [NAMES[index] ?? ""];
  if (day.paused) parts.push("en pause");
  else if (!day.research) parts.push("jour de repos");
  if (day.sent) parts.push(day.sent === 1 ? "1 candidature" : `${day.sent} candidatures`);
  return parts.join(", ");
}
</script>

<template>
  <div
    v-if="band"
    :class="['rhythm-band', { done }]"
    data-test="rhythm"
  >
    <div class="rhythm-band-text">
      <strong>Cette semaine</strong>
      <span
        v-if="week.pause_until"
        data-test="rhythm-count"
      >En pause</span>
      <span
        v-else-if="week.target !== null"
        data-test="rhythm-count"
      >{{ week.count }} sur {{ week.target }}{{ done ? ", faite" : "" }}</span>
    </div>
    <ol
      class="rhythm-band-days"
      aria-hidden="true"
    >
      <li
        v-for="(day, index) in week.days"
        :key="day.day"
        :class="{ rest: !day.research || day.paused, sent: day.sent > 0, today: day.day === todayIso }"
      >
        <span class="rhythm-band-dot">{{ day.sent > 0 ? day.sent : "" }}</span>
        <span>{{ LETTERS[index] }}</span>
      </li>
    </ol>
  </div>
  <section
    v-else
    :class="[nested ? 'rhythm-nested' : 'dash-card', 'rhythm-card', { done }]"
    data-test="rhythm"
  >
    <header class="rhythm-head">
      <h3
        v-if="nested"
        class="today-sub-title"
      >
        Cette semaine
      </h3>
      <h2 v-else>
        Semaine
      </h2>
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
      v-else-if="week.target === null"
      class="hint"
    >
      <RouterLink :to="{ path: '/reglages', query: { rubrique: 'recherche' } }">
        Indiquer l'objectif mensuel
      </RouterLink> pour le répartir sur tes semaines.
    </p>
  </section>
</template>
