<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";

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

// Lot 14 (MODIFICATIONS du 8 novembre au soir) : la date abrégée dès que la pilule a moins de 280 px, jamais sur deux
// lignes. On mesure la place offerte (le champ moins la pilule de l'heure), pas la pilule elle-même, dont la largeur
// suit son texte : sinon la date passerait sans fin d'une forme à l'autre.
const SHORT_BELOW = 280;
const field = ref<HTMLElement | null>(null);
const timePart = ref<HTMLElement | null>(null);
const narrow = ref(false);
function measure(): void {
  const el = field.value;
  if (!el) return;
  const time = props.withTime ? (timePart.value?.getBoundingClientRect().width ?? 0) : 0;
  const gap = props.withTime ? parseFloat(getComputedStyle(el).columnGap) || 0 : 0;
  const room = el.getBoundingClientRect().width - time - gap;
  narrow.value = room > 0 && room < SHORT_BELOW;
}
let observer: ResizeObserver | null = null;
onMounted(() => {
  if (typeof ResizeObserver === "undefined" || !field.value) return;
  observer = new ResizeObserver(measure);
  observer.observe(field.value);
  measure();
});
onUnmounted(() => observer?.disconnect());
// Téléphone (corrections du 9 novembre) : date et heure côte à côte, la pilule vide dit « Choisir » ; le libellé au-dessus
// nomme déjà le champ, et « Choisir une heure » ne tiendrait pas à 360 px.
const empty = (long: string) => (props.compact ? "Choisir" : long);
const dateText = computed(() =>
  props.date ? (props.compact || narrow.value ? shortDate(props.date) : longDate(props.date)) : empty("Choisir une date"),
);
const timeText = computed(() => (props.time ? clockLabel(props.time) : empty("Choisir une heure")));
</script>

<template>
  <div
    ref="field"
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
      ref="timePart"
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
