<script setup lang="ts">
import { computed, ref, watch } from "vue";

import BottomSheet from "./BottomSheet.vue";

// La pause du Rythme (planche ReglagesRythmePause du 18.11, §70 ; Q7 de Kevin du 17.11) : une feuille en îlot avec un
// seul calendrier de plage. Premier toucher = Du, second = Jusqu’au ; un toucher avant le début le déplace. Les mois
// défilent sous les jours de la semaine, fixes en haut. Jours passés grisés, aujourd’hui entouré, le prochain
// rendez-vous ORP marqué d’un point orange, et signalé s’il tombe pendant la pause. Rien n’est enregistré avant
// « Enregistrer » ; « Effacer » vide la plage (enregistrée vide, elle retire la pause).
// `wide` : sur ordinateur (planche ReglagesOrdinateurPause du 18.11, §71), la même plage dans une fenêtre centrée de
// 760 px, deux mois côte à côte (chacun avec ses jours de la semaine) ; les mois suivants viennent deux par deux en
// faisant défiler, comme sur téléphone. « Clic » au lieu de « toucher ».
const props = defineProps<{ open: boolean; from: string | null; until: string | null; meeting?: string | null; wide?: boolean }>();
const emit = defineEmits<{ close: []; save: [from: string | null, until: string | null] }>();

const start = ref<string | null>(null);
const end = ref<string | null>(null);
watch(
  () => props.open,
  (open) => {
    if (!open) return;
    start.value = props.from;
    end.value = props.until && props.from && props.until >= props.from ? props.until : null;
  },
  { immediate: true },
);

const iso = (d: Date): string =>
  `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
const parse = (value: string): Date => {
  const [y, m, d] = value.split("-").map(Number);
  return new Date(y!, m! - 1, d!);
};
const today = iso(new Date());
const meetingDay = computed(() => (props.meeting ? iso(new Date(props.meeting)) : null));

const WEEK = [
  ["L", "Lundi"],
  ["M", "Mardi"],
  ["M", "Mercredi"],
  ["J", "Jeudi"],
  ["V", "Vendredi"],
  ["S", "Samedi"],
  ["D", "Dimanche"],
] as const;
const monthName = new Intl.DateTimeFormat("fr-CH", { month: "long", year: "numeric" });
const dayName = new Intl.DateTimeFormat("fr-CH", { weekday: "long", day: "numeric", month: "long", year: "numeric" });
const short = new Intl.DateTimeFormat("fr-CH", { day: "numeric", month: "short" });

// Le mois en cours et les onze suivants ; la case vide avant le 1er aligne le lundi à gauche.
const months = computed(() => {
  const now = new Date();
  return Array.from({ length: 12 }, (_, i) => {
    const first = new Date(now.getFullYear(), now.getMonth() + i, 1);
    const length = new Date(first.getFullYear(), first.getMonth() + 1, 0).getDate();
    const title = monthName.format(first);
    return {
      key: iso(first),
      title: title.charAt(0).toUpperCase() + title.slice(1),
      offset: (first.getDay() + 6) % 7,
      days: Array.from({ length }, (_, d) => new Date(first.getFullYear(), first.getMonth(), d + 1)),
    };
  });
});

function pick(day: string): void {
  if (day < today) return;
  if (!start.value || end.value || day < start.value) {
    start.value = day;
    end.value = null;
  } else {
    end.value = day;
  }
}

const DAY_MS = 86_400_000;
const length = computed(() =>
  start.value && end.value ? Math.round((parse(end.value).getTime() - parse(start.value).getTime()) / DAY_MS) + 1 : 0,
);
const summary = computed(() => {
  const verb = props.wide ? "clique sur" : "touche";
  if (!start.value) return `${verb.charAt(0).toUpperCase()}${verb.slice(1)} le premier jour`;
  if (!end.value) return `${short.format(parse(start.value))} → ${verb} le dernier jour`;
  return `${short.format(parse(start.value))} → ${short.format(parse(end.value))}`;
});
const meetingInPause = computed(
  () => !!meetingDay.value && !!start.value && meetingDay.value >= start.value && meetingDay.value <= (end.value ?? start.value),
);

// La bande de la plage : arrondie au bout de chaque ligne et de chaque mois ; le début et la fin en rond plein.
function cellClass(date: Date): Record<string, boolean> {
  const day = iso(date);
  const last = start.value && (end.value ?? start.value);
  const inside = !!start.value && !!last && day >= start.value && day <= last;
  const isStart = day === start.value;
  const isEnd = day === last && !!end.value;
  const weekday = (date.getDay() + 6) % 7;
  const monthEnd = new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate() === date.getDate();
  const leftEdge = weekday === 0 || date.getDate() === 1;
  const rightEdge = weekday === 6 || monthEnd;
  const spans = !!end.value && end.value !== start.value;
  return {
    "pc-past": day < today,
    "pc-today": day === today,
    "pc-end": isStart || isEnd,
    "pc-band": spans && inside && !isStart && !isEnd,
    "pc-from": spans && isStart && !rightEdge,
    "pc-to": spans && isEnd && !leftEdge,
    "pc-l": spans && inside && !isStart && !isEnd && leftEdge,
    "pc-r": spans && inside && !isStart && !isEnd && rightEdge,
    "pc-rdv": day === meetingDay.value,
  };
}
</script>

<template>
  <BottomSheet
    :open="open"
    title="Pause"
    size="large"
    :class="['pause-sheet', { 'pause-wide': wide }]"
    data-test="pause-sheet"
    @close="emit('close')"
  >
    <div class="pause-top">
      <p
        class="pause-sum"
        role="status"
        data-test="pause-summary"
      >
        <svg
          viewBox="0 0 24 24"
          aria-hidden="true"
          class="icon"
        ><rect
          x="3"
          y="5"
          width="18"
          height="16"
          rx="2"
        /><path d="M3 10h18M8 3v4M16 3v4" /></svg>
        <span>{{ summary }}</span>
        <small v-if="length || wide">{{ [length ? `${length} ${length > 1 ? "jours" : "jour"}` : "", wide ? "1er clic : Du, 2e clic : Jusqu’au" : ""].filter(Boolean).join(" · ") }}</small>
      </p>
      <div
        v-if="!wide"
        class="pause-week"
        aria-hidden="true"
      >
        <span
          v-for="([letter], i) in WEEK"
          :key="i"
        >{{ letter }}</span>
      </div>
    </div>
    <div class="pause-months">
      <section
        v-for="month in months"
        :key="month.key"
        class="pause-month"
        :aria-label="month.title"
      >
        <h3>{{ month.title }}</h3>
        <div
          v-if="wide"
          class="pause-week"
          aria-hidden="true"
        >
          <span
            v-for="([letter], i) in WEEK"
            :key="i"
          >{{ letter }}</span>
        </div>
        <div class="pause-grid">
          <span
            v-if="month.offset"
            :style="{ gridColumn: `span ${month.offset}` }"
          />
          <span
            v-for="date in month.days"
            :key="date.getDate()"
            :class="['pc', cellClass(date)]"
          >
            <button
              type="button"
              :aria-label="dayName.format(date) + (iso(date) === meetingDay ? ', rendez-vous ORP' : '')"
              :aria-pressed="!!start && iso(date) >= start && iso(date) <= (end ?? start) ? 'true' : 'false'"
              :aria-disabled="iso(date) < today ? 'true' : undefined"
              :aria-current="iso(date) === today ? 'date' : undefined"
              :data-test="`pause-day-${iso(date)}`"
              @click="pick(iso(date))"
            >{{ date.getDate() }}</button>
          </span>
        </div>
      </section>
    </div>
    <template #actions>
      <p
        v-if="meetingInPause && meetingDay"
        class="pause-warn"
        data-test="pause-meeting"
      >
        <span aria-hidden="true" />Ton rendez-vous ORP du {{ short.format(parse(meetingDay)) }} tombe pendant la pause. Il reste dans
        ton agenda.
      </p>
      <div class="pause-foot">
        <button
          type="button"
          class="link pause-clear"
          data-test="pause-clear"
          @click="start = null; end = null"
        >
          Effacer
        </button>
        <button
          type="button"
          class="primary"
          data-test="pause-save"
          @click="emit('save', start, end)"
        >
          Enregistrer
        </button>
      </div>
    </template>
  </BottomSheet>
</template>

<style>
.pause-sheet .sheet-body { gap: 0; padding-inline: var(--space-2); }
.pause-sheet .sheet-actions { display: grid; gap: var(--space-3); border-top: 1px solid var(--line-soft); }
.pause-top { position: sticky; top: 0; z-index: 1; background: var(--surface); }
.pause-sum { display: flex; align-items: center; gap: var(--space-3); height: 52px; margin: var(--space-1) var(--space-2) 0; padding: 0 var(--space-5); border: 2px solid var(--text); border-radius: var(--radius-pill); font-weight: var(--weight-bold); }
.pause-sum .icon { width: 20px; height: 20px; fill: none; stroke: currentColor; stroke-width: 2; stroke-linecap: round; }
.pause-sum small { margin-left: auto; font-size: var(--font-small); font-weight: var(--weight-semibold); color: var(--text-secondary); }
.pause-week, .pause-grid { display: grid; grid-template-columns: repeat(7, 1fr); }
.pause-week { padding: var(--space-4) 0 var(--space-3); border-bottom: 1px solid var(--line-soft); font-size: var(--font-small); font-weight: var(--weight-bold); color: var(--text-secondary); text-align: center; }
.pause-month h3 { margin: var(--space-4) 0 var(--space-2); font-size: var(--font-body); text-align: center; }
.pause-grid { row-gap: var(--space-1); }
.pc { position: relative; display: grid; place-items: center; height: 44px; }
.pc button { display: grid; place-items: center; width: 44px; height: 44px; padding: 0; border: 0; border-radius: var(--radius-pill); background: transparent; color: var(--text); font: inherit; font-weight: var(--weight-semibold); cursor: pointer; }
.pc-past button { color: var(--text-disabled); font-weight: var(--weight-regular); cursor: default; }
.pc-today button { box-shadow: inset 0 0 0 1.5px var(--text); }
.pc-band, .pc-l, .pc-r { background: var(--primary-soft); }
.pc-l { border-radius: var(--radius-pill) 0 0 var(--radius-pill); }
.pc-r { border-radius: 0 var(--radius-pill) var(--radius-pill) 0; }
.pc-l.pc-r { border-radius: var(--radius-pill); }
.pc-from { background: linear-gradient(90deg, transparent 50%, var(--primary-soft) 50%); }
.pc-to { background: linear-gradient(90deg, var(--primary-soft) 50%, transparent 50%); }
.pc-end button { background: var(--action); color: var(--on-action); font-weight: var(--weight-heavy); }
.pc-rdv::after { content: ""; position: absolute; bottom: 0; width: 6px; height: 6px; border-radius: var(--radius-pill); background: var(--icon-peach); pointer-events: none; }
.pause-warn { display: flex; gap: var(--space-3); margin: 0; padding: var(--space-3) var(--space-4); border-radius: var(--radius-card); background: var(--peach-soft); font-size: var(--font-small); color: var(--text-secondary); }
.pause-warn > span { flex: none; width: 8px; height: 8px; margin-top: var(--space-2); border-radius: var(--radius-pill); background: var(--icon-peach); }
.pause-foot { display: flex; align-items: center; justify-content: space-between; }
.pause-foot .pause-clear { min-height: 44px; font-weight: var(--weight-bold); color: var(--text); }
.pause-foot .primary { min-height: 52px; padding: 0 var(--space-8); border-radius: var(--radius-pill); }
/* Ordinateur (ReglagesOrdinateurPause, §71) : fenêtre centrée de 760 px, rayon 28, deux mois de 7 × 44 px côte à côte ;
   la zone des mois défile deux par deux (hauteur d’un mois de six semaines). Pied à droite, « Effacer » puis « Enregistrer ». */
@media (min-width: 821px) {
  .sheet.pause-wide { inset: 0; width: 760px; max-width: calc(100vw - 2 * var(--space-6)); height: fit-content; max-height: calc(100dvh - 2 * var(--space-6)); margin: auto; border-radius: var(--sheet-radius); background: var(--surface); }
  .sheet.pause-wide[open] { animation: none; }
  .pause-wide .sheet-head { min-height: 0; padding: var(--space-5) var(--space-5) 0 var(--space-6); }
  .pause-wide .sheet-body { overflow: hidden; padding: 0; }
  .pause-wide .pause-top { position: static; }
  .pause-wide .pause-sum { margin: var(--space-3) var(--space-6) 0; padding: 0 var(--space-4); }
  .pause-wide .pause-months { display: grid; grid-template-columns: repeat(2, max-content); justify-content: space-between; column-gap: calc(var(--space-8) + var(--space-2)); row-gap: var(--space-6); box-sizing: content-box; height: 342px; padding: var(--space-5) var(--space-8) var(--space-2); overflow-y: auto; overscroll-behavior: contain; scroll-snap-type: y mandatory; scroll-padding-top: var(--space-5); }
  .pause-wide .pause-month { scroll-snap-align: start; }
  .pause-wide .pause-month h3 { margin: 0 0 var(--space-3); line-height: var(--space-6); }
  .pause-wide .pause-week, .pause-wide .pause-grid { grid-template-columns: repeat(7, 44px); }
  .pause-wide .pause-week { margin-bottom: var(--space-2); padding: 0; border: 0; }
  .pause-wide .pc-rdv::after { bottom: var(--space-1); }
  .pause-wide .sheet-actions { padding: var(--space-3) 0 0; border-top: 0; }
  .pause-wide .pause-warn { margin: 0 var(--space-6); }
  .pause-wide .pause-foot { justify-content: flex-end; gap: var(--space-3); margin-top: var(--space-1); padding: var(--space-4) var(--space-5) var(--space-5); border-top: 1px solid var(--line-soft); }
  .pause-wide .pause-foot .pause-clear { min-height: 48px; padding: 0 var(--space-5); font-size: var(--font-body); }
  .pause-wide .pause-foot .primary { min-height: 48px; padding: 0 var(--space-6); }
}
</style>
