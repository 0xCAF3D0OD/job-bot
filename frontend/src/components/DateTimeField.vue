<script setup lang="ts">
import { computed } from "vue";

import AppIcon from "./AppIcon.vue";
import { clockLabel, longDate, shortDate } from "../dates";

// Les déclencheurs date et heure en pilule (maquette du 8 novembre, docs/143, D26) : 52 px, bordure 1,5 px
// --field-border, icône bleue, valeur en toutes lettres, chevron. Un clic ouvre le sélecteur (DateTimePanel), qui
// prend la place du formulaire. `compact` : la date abrégée des pilules étroites du téléphone (maquette RendezVous).
const props = withDefaults(
  defineProps<{
    date: string;
    time: string;
    open?: "" | "date" | "time";
    compact?: boolean;
    dateLabel?: string;
    timeLabel?: string;
    withTime?: boolean;
  }>(),
  { open: "", compact: false, dateLabel: "Date", timeLabel: "Heure", withTime: true },
);
const emit = defineEmits<{ open: [which: "date" | "time"] }>();

const dateText = computed(() => (props.date ? (props.compact ? shortDate(props.date) : longDate(props.date)) : "Choisir une date"));
const timeText = computed(() => (props.time ? clockLabel(props.time) : "Choisir une heure"));
</script>

<template>
  <div
    class="dt-field"
    data-test="date-time-field"
  >
    <div class="dt-field-part dt-field-date">
      <span
        class="dt-field-label"
        aria-hidden="true"
      >{{ dateLabel }}</span>
      <button
        type="button"
        :class="['dt-pill', { 'dt-pill-open': open === 'date', 'dt-pill-empty': !date }]"
        :aria-label="`${dateLabel} : ${dateText}`"
        aria-haspopup="dialog"
        :aria-expanded="open === 'date'"
        data-test="dt-date"
        @click="emit('open', 'date')"
      >
        <AppIcon name="calendar" />
        <span class="dt-pill-value">{{ dateText }}</span>
        <AppIcon
          v-if="!compact"
          name="chevron-down"
        />
      </button>
    </div>
    <div
      v-if="withTime"
      class="dt-field-part dt-field-time"
    >
      <span
        class="dt-field-label"
        aria-hidden="true"
      >{{ timeLabel }}</span>
      <button
        type="button"
        :class="['dt-pill', { 'dt-pill-open': open === 'time', 'dt-pill-empty': !time }]"
        :aria-label="`${timeLabel} : ${timeText}`"
        aria-haspopup="dialog"
        :aria-expanded="open === 'time'"
        data-test="dt-time"
        @click="emit('open', 'time')"
      >
        <AppIcon name="clock" />
        <span class="dt-pill-value">{{ timeText }}</span>
        <AppIcon
          v-if="!compact"
          name="chevron-down"
        />
      </button>
    </div>
  </div>
</template>
