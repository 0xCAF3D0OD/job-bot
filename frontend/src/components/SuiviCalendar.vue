<script setup lang="ts">
import { computed } from "vue";

import type { Application } from "../api/client";
import { applicationStatusLabel } from "../format";

// Calendrier du mois (docs/22 §3) : une pastille par candidature envoyée, repères entretien
// et relance, point rouge si la ligne ORP est à compléter.
const props = defineProps<{
  month: string;
  applications: Application[];
  incomplete: Set<number>;
  selected: string | null;
}>();
const emit = defineEmits<{ select: [day: string] }>();

const REMIND_AFTER_DAYS = 10;
const MAX_DOTS = 3;
const WEEKDAYS = ["lun.", "mar.", "mer.", "jeu.", "ven.", "sam.", "dim."];

function iso(date: Date): string {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}

function addDays(day: string, n: number): string {
  const [y, m, d] = day.split("-").map(Number);
  return iso(new Date(y!, m! - 1, d! + n));
}

const today = iso(new Date());

// Semaines du mois, du lundi au dimanche ; null pour les cases hors du mois.
const weeks = computed(() => {
  const [year, month] = props.month.split("-").map(Number);
  const first = new Date(year!, month! - 1, 1);
  const days = new Date(year!, month!, 0).getDate();
  const offset = (first.getDay() + 6) % 7;
  const cells: (string | null)[] = Array(offset).fill(null);
  for (let d = 1; d <= days; d++) cells.push(iso(new Date(year!, month! - 1, d)));
  while (cells.length % 7) cells.push(null);
  return Array.from({ length: cells.length / 7 }, (_, i) => cells.slice(i * 7, i * 7 + 7));
});

const sentOn = computed(() => {
  const map = new Map<string, Application[]>();
  for (const a of props.applications) map.set(a.sent_at, [...(map.get(a.sent_at) ?? []), a]);
  return map;
});
const interviews = computed(() => {
  const set = new Set<string>();
  for (const a of props.applications) if (a.interview_at) set.add(iso(new Date(a.interview_at)));
  return set;
});
// Prochaine étape annoncée en entretien (docs/23 §3) : « réponse attendue », etc.
const nextSteps = computed(() => {
  const set = new Set<string>();
  for (const a of props.applications) for (const i of a.interviews ?? []) if (i.next_step_at) set.add(i.next_step_at);
  return set;
});
const reminders = computed(() => {
  const set = new Set<string>();
  for (const a of props.applications) if (a.status === "en_attente") set.add(addDays(a.sent_at, REMIND_AFTER_DAYS));
  return set;
});

function label(day: string): string {
  const sent = sentOn.value.get(day) ?? [];
  const parts = [`${Number(day.slice(8))}`];
  if (sent.length) parts.push(`${sent.length} candidature(s)`);
  if (interviews.value.has(day)) parts.push("entretien");
  if (reminders.value.has(day)) parts.push("à relancer");
  if (nextSteps.value.has(day)) parts.push("suite attendue");
  return parts.join(", ");
}
</script>

<template>
  <div
    class="suivi-calendar"
    role="grid"
    aria-label="Candidatures du mois"
    data-test="calendar"
  >
    <div
      v-for="name in WEEKDAYS"
      :key="name"
      class="weekday"
      role="columnheader"
    >
      {{ name }}
    </div>
    <template
      v-for="(week, w) in weeks"
      :key="w"
    >
      <template
        v-for="(day, d) in week"
        :key="`${w}-${d}`"
      >
        <span
          v-if="!day"
          class="day empty"
        />
        <button
          v-else
          type="button"
          role="gridcell"
          :class="['day', { today: day === today, selected: day === selected, busy: sentOn.get(day)?.length }]"
          :aria-label="label(day)"
          :aria-pressed="day === selected"
          :data-test="`day-${day}`"
          @click="emit('select', day)"
        >
          <span class="day-number">{{ Number(day.slice(8)) }}</span>
          <span class="day-dots">
            <span
              v-for="application in (sentOn.get(day) ?? []).slice(0, MAX_DOTS)"
              :key="application.id"
              :class="['dot', application.status, { incomplete: incomplete.has(application.id) }]"
              :title="`${application.company} · ${applicationStatusLabel[application.status ?? 'en_attente']}`"
            />
            <span
              v-if="(sentOn.get(day)?.length ?? 0) > MAX_DOTS"
              class="more"
            >+{{ sentOn.get(day)!.length - MAX_DOTS }}</span>
          </span>
          <span class="day-marks">
            <span
              v-if="interviews.has(day)"
              class="mark interview"
              data-test="mark-interview"
            >entretien</span>
            <span
              v-if="reminders.has(day)"
              class="mark remind"
              data-test="mark-remind"
            >relancer</span>
            <span
              v-if="nextSteps.has(day)"
              class="mark next"
              data-test="mark-next"
            >suite attendue</span>
          </span>
        </button>
      </template>
    </template>
  </div>
</template>
