<script setup lang="ts">
import { computed } from "vue";

import type { Application } from "../api/client";
import { applicationStatusLabel, localDate, plural } from "../format";

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
// Statut par la couleur seule (choix du 2026-10-14) : blanc en attente, orange relancée,
// violet entretien, rouge refus, vert clair engagement, gris sans réponse ; légende dessous et
// statuts lus par les lecteurs d'écran.
const LEGEND = ["en_attente", "relancee", "entretien", "refus", "engagement", "sans_reponse"] as const;
const WEEKDAYS = ["lun.", "mar.", "mer.", "jeu.", "ven.", "sam.", "dim."];

function iso(date: Date): string {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}

function addDays(day: string, n: number): string {
  const date = localDate(day);
  date.setDate(date.getDate() + n);
  return iso(date);
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

const WEEKDAY_NAME = new Intl.DateTimeFormat("fr-CH", { weekday: "long" });

function label(day: string): string {
  const sent = sentOn.value.get(day) ?? [];
  // Le jour de la semaine dans le nom (docs/117 §1) : les en-têtes « L M M… » sont visuels.
  const parts = [WEEKDAY_NAME.format(new Date(`${day}T12:00:00`)) + ` ${Number(day.slice(8))}`];
  if (sent.length) {
    const statuses = sent.map((a) => applicationStatusLabel[a.status ?? "en_attente"].toLowerCase());
    parts.push(`${plural(sent.length, "candidature", "candidatures")} : ${statuses.join(", ")}`);
  }
  // L'anneau orange se dit aussi au lecteur d'écran (0.90.2).
  if (sent.some((a) => props.incomplete.has(a.id))) parts.push("à compléter pour l'ORP");
  if (interviews.value.has(day)) parts.push("entretien");
  if (reminders.value.has(day)) parts.push("à relancer");
  if (nextSteps.value.has(day)) parts.push("suite attendue");
  return parts.join(", ");
}
</script>

<template>
  <div class="suivi-calendar-wrap">
    <!-- La légende, une ligne discrète au-dessus du calendrier (docs/133 §5). -->
    <ul
      class="suivi-legend"
      aria-label="Légende"
      data-test="suivi-legend"
    >
      <li
        v-for="status in LEGEND"
        :key="status"
      >
        <span
          :class="['dot', status]"
          aria-hidden="true"
        />{{ applicationStatusLabel[status] }}
      </li>
      <li>
        <span
          class="dot en_attente incomplete"
          aria-hidden="true"
        />à compléter
      </li>
    </ul>
    <div
      class="suivi-calendar"
      role="group"
      aria-label="Candidatures du mois"
      data-test="calendar"
    >
      <div
        v-for="name in WEEKDAYS"
        :key="name"
        class="weekday"
        aria-hidden="true"
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
            :class="['day', 'empty']"
          />
          <button
            v-else
            type="button"
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
                aria-hidden="true"
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
  </div>
</template>
