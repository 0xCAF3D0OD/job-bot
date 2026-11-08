<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, useId } from "vue";

import AppIcon from "./AppIcon.vue";
import { pickerOpen } from "../composables/useDismissLayer";
import {
  addDays,
  addMonths,
  clockLabel,
  dayLabel,
  dayToDate,
  longDate,
  monthTitle,
  parseTypedDay,
  parseTypedTime,
  shortDate,
  todayDay,
  typedDay,
} from "../dates";

// Le sélecteur de date et heure (maquette du 8 novembre, docs/143, D26 ; LISEZMOI « Date et heure ») : il prend la
// place du formulaire dans son conteneur (pas de popover) ; sur téléphone (`full`), il occupe l'écran avec « Valider »
// collé en bas. Raccourcis, grille de 6 semaines (lundi en premier), jours passés désactivés, saisie jj.mm.aaaa ;
// créneaux de 30 min de 8 h à 16 h et saisie hh:mm. Clavier : flèches pour les jours, Page haut et Page bas pour les
// mois, Entrée valide, Échap annule.
// Lot 10 : les bornes `min` et `max` (jj ISO) pour les dates passées (date d'envoi, contact, formation) ; sans `min`,
// les jours passés restent désactivés. Les raccourcis hors des bornes ne s'affichent pas (aucun raccourci ajouté).
const props = withDefaults(
  defineProps<{ date: string; time: string; title: string; full?: boolean; today?: string; withTime?: boolean; min?: string | null; max?: string }>(),
  { full: false, today: "", withTime: true, min: undefined, max: "" },
);
const emit = defineEmits<{ confirm: [value: { date: string; time: string }]; cancel: [] }>();

const now = computed(() => props.today || todayDay());
const low = computed(() => (props.min === undefined ? now.value : props.min ?? ""));
const out = (day: string) => (!!low.value && day < low.value) || (!!props.max && day > props.max);
function clamp(day: string): string {
  if (low.value && day < low.value) return low.value;
  if (props.max && day > props.max) return props.max;
  return day;
}
const picked = ref(props.date || "");
const time = ref(props.time || "");
const focusDay = ref(clamp(props.date || now.value));
const view = ref(firstOfMonth(focusDay.value));
const typedDate = ref(picked.value ? typedDay(picked.value) : "");
const typedTime = ref(time.value);
const dateError = ref("");
const timeError = ref("");
const titleId = useId();
const grid = ref<HTMLElement | null>(null);

const WEEKDAYS = [
  ["L", "lundi"],
  ["M", "mardi"],
  ["M", "mercredi"],
  ["J", "jeudi"],
  ["V", "vendredi"],
  ["S", "samedi"],
  ["D", "dimanche"],
] as const;
const SLOTS = Array.from({ length: 17 }, (_, i) => `${String(8 + Math.floor(i / 2)).padStart(2, "0")}:${i % 2 ? "30" : "00"}`);

function firstOfMonth(day: string): string {
  return `${day.slice(0, 7)}-01`;
}

// Le lundi de la semaine du 1er, puis 42 jours.
const days = computed(() => {
  const first = dayToDate(view.value);
  const offset = (first.getUTCDay() + 6) % 7;
  const start = addDays(view.value, -offset);
  return Array.from({ length: 42 }, (_, i) => {
    const day = addDays(start, i);
    return {
      day,
      number: Number(day.slice(8)),
      outside: day.slice(0, 7) !== view.value.slice(0, 7),
      past: out(day),
      today: day === now.value,
      picked: day === picked.value,
      weekend: [0, 6].includes(dayToDate(day).getUTCDay()),
    };
  });
});

const shortcuts = computed(() => {
  const today = now.value;
  const weekday = dayToDate(today).getUTCDay();
  const toMonday = ((8 - weekday) % 7) || 7;
  return [
    { label: "Demain", day: addDays(today, 1) },
    { label: "Lundi prochain", day: addDays(today, toMonday) },
    { label: "Dans 2 semaines", day: addDays(today, 14) },
    { label: "Dans 1 mois", day: addMonths(today, 1) },
  ].filter((shortcut) => !out(shortcut.day));
});

const summaryDate = computed(() => (picked.value ? (props.full ? shortDate(picked.value) : longDate(picked.value)) : ""));
const summary = computed(() => {
  if (!picked.value) return "Choisis un jour";
  return time.value && props.withTime ? `${longDate(picked.value)}, ${clockLabel(time.value)}` : longDate(picked.value);
});
const canConfirm = computed(() => !!picked.value && (!props.withTime || !!time.value));

function choose(day: string): void {
  if (out(day)) return;
  picked.value = day;
  focusDay.value = day;
  typedDate.value = typedDay(day);
  dateError.value = "";
  if (day.slice(0, 7) !== view.value.slice(0, 7)) view.value = firstOfMonth(day);
}

function chooseTime(slot: string): void {
  time.value = slot;
  typedTime.value = slot;
  timeError.value = "";
}

function onTypedDate(): void {
  if (!typedDate.value.trim()) return;
  const day = parseTypedDay(typedDate.value);
  if (!day) dateError.value = "Écris la date comme ceci : 10.11.2026.";
  else if (low.value && day < low.value) dateError.value = low.value === now.value ? "Ce jour est déjà passé." : `Choisis un jour à partir du ${longDate(low.value)}.`;
  else if (props.max && day > props.max) dateError.value = props.max === now.value ? "Ce jour n'est pas encore arrivé." : `Choisis un jour jusqu'au ${longDate(props.max)}.`;
  else choose(day);
}

function onTypedTime(): void {
  if (!typedTime.value.trim()) return;
  const value = parseTypedTime(typedTime.value);
  if (!value) timeError.value = "Écris l'heure comme ceci : 09:30.";
  else chooseTime(value);
}

function month(delta: number): void {
  view.value = addMonths(view.value, delta);
  focusDay.value = clamp(addMonths(focusDay.value, delta));
}

async function moveFocus(day: string): Promise<void> {
  focusDay.value = clamp(day);
  if (focusDay.value.slice(0, 7) !== view.value.slice(0, 7)) view.value = firstOfMonth(focusDay.value);
  await nextTick();
  grid.value?.querySelector<HTMLButtonElement>(`[data-day="${focusDay.value}"]`)?.focus();
}

function onGridKeydown(event: KeyboardEvent): void {
  const steps: Record<string, number> = { ArrowLeft: -1, ArrowRight: 1, ArrowUp: -7, ArrowDown: 7 };
  if (event.key in steps) {
    event.preventDefault();
    void moveFocus(addDays(focusDay.value, steps[event.key]!));
  } else if (event.key === "PageUp" || event.key === "PageDown") {
    event.preventDefault();
    void moveFocus(addMonths(focusDay.value, event.key === "PageUp" ? -1 : 1));
  }
}

function confirm(): void {
  if (!canConfirm.value) return;
  emit("confirm", { date: picked.value, time: props.withTime ? time.value : "" });
}

function onKeydown(event: KeyboardEvent): void {
  if (event.key === "Escape") {
    event.preventDefault();
    event.stopPropagation();
    emit("cancel");
  } else if (event.key === "Enter" && (event.target as HTMLElement).closest?.(".dt-grid")) {
    // Entrée sur un jour : le choisit et valide si l'heure est déjà là.
    event.preventDefault();
    choose(focusDay.value);
    if (canConfirm.value) confirm();
  }
}

onMounted(() => {
  pickerOpen.value += 1;
  void moveFocus(focusDay.value);
});
onUnmounted(() => {
  pickerOpen.value -= 1;
});
</script>

<template>
  <section
    :class="['dt-panel', { 'dt-panel-full': full }]"
    :aria-labelledby="titleId"
    data-test="date-time-panel"
    @keydown="onKeydown"
  >
    <header class="dt-panel-head">
      <button
        type="button"
        class="dt-back"
        data-test="dt-back"
        @click="emit('cancel')"
      >
        <AppIcon name="chevron-left" />{{ full ? "Retour" : "Retour au formulaire" }}
      </button>
      <h3
        :id="titleId"
        class="dt-panel-title"
      >
        {{ title }}
      </h3>
    </header>
    <div class="dt-panel-body">
      <div class="dt-calendar">
        <div
          v-if="shortcuts.length"
          class="dt-shortcuts"
          role="group"
          aria-label="Raccourcis"
        >
          <button
            v-for="shortcut in shortcuts"
            :key="shortcut.label"
            type="button"
            class="dt-shortcut"
            :aria-pressed="picked === shortcut.day"
            :data-test="`dt-shortcut-${shortcut.label}`"
            @click="choose(shortcut.day)"
          >
            {{ shortcut.label }}
          </button>
        </div>
        <div class="dt-calendar-card">
          <div class="dt-month">
            <button
              type="button"
              class="dt-month-step"
              aria-label="Mois précédent"
              :disabled="!!low && view <= `${low.slice(0, 7)}-01`"
              data-test="dt-prev"
              @click="month(-1)"
            >
              <AppIcon name="chevron-left" />
            </button>
            <strong aria-live="polite">{{ monthTitle(view) }}</strong>
            <button
              type="button"
              class="dt-month-step"
              aria-label="Mois suivant"
              :disabled="!!max && view >= `${max.slice(0, 7)}-01`"
              data-test="dt-next"
              @click="month(1)"
            >
              <AppIcon name="chevron" />
            </button>
          </div>
          <div
            ref="grid"
            class="dt-grid"
            role="group"
            :aria-label="monthTitle(view)"
            @keydown="onGridKeydown"
          >
            <abbr
              v-for="(weekday, index) in WEEKDAYS"
              :key="index"
              class="dt-weekday"
              :title="weekday[1]"
            >{{ weekday[0] }}</abbr>
            <button
              v-for="cell in days"
              :key="cell.day"
              type="button"
              :class="['dt-day', { 'dt-day-outside': cell.outside, 'dt-day-today': cell.today, 'dt-day-picked': cell.picked, 'dt-day-weekend': cell.weekend }]"
              :disabled="cell.past"
              :tabindex="cell.day === focusDay ? 0 : -1"
              :aria-label="`${dayLabel(cell.day)}${cell.today ? ', aujourd’hui' : ''}`"
              :aria-pressed="cell.picked"
              :aria-current="cell.today ? 'date' : undefined"
              :data-day="cell.day"
              @click="choose(cell.day)"
            >
              {{ cell.number }}
            </button>
          </div>
          <div class="dt-typed">
            <label :for="`${titleId}-d`">Ou écris-la :</label>
            <input
              :id="`${titleId}-d`"
              v-model="typedDate"
              class="dt-typed-input"
              inputmode="numeric"
              aria-label="Date au format jj.mm.aaaa"
              :aria-invalid="dateError ? 'true' : undefined"
              :aria-describedby="dateError ? `${titleId}-de` : undefined"
              data-test="dt-typed-date"
              @change="onTypedDate"
              @keydown.enter.prevent="onTypedDate"
            >
          </div>
          <p
            v-if="dateError"
            :id="`${titleId}-de`"
            class="field-error"
            role="alert"
          >
            {{ dateError }}
          </p>
        </div>
      </div>
      <div
        v-if="withTime"
        class="dt-time"
      >
        <span
          :id="`${titleId}-h`"
          class="dt-time-title"
        >Heure</span>
        <div
          class="dt-slots"
          role="group"
          :aria-labelledby="`${titleId}-h`"
        >
          <button
            v-for="slot in SLOTS"
            :key="slot"
            type="button"
            class="dt-slot"
            :aria-pressed="time === slot"
            :data-test="`dt-slot-${slot}`"
            @click="chooseTime(slot)"
          >
            {{ slot }}
          </button>
        </div>
        <div class="dt-typed">
          <label :for="`${titleId}-t`">Autre heure :</label>
          <input
            :id="`${titleId}-t`"
            v-model="typedTime"
            class="dt-typed-input"
            inputmode="numeric"
            aria-label="Heure au format hh:mm"
            :aria-invalid="timeError ? 'true' : undefined"
            :aria-describedby="timeError ? `${titleId}-te` : undefined"
            data-test="dt-typed-time"
            @change="onTypedTime"
            @keydown.enter.prevent="onTypedTime"
          >
        </div>
        <p
          v-if="timeError"
          :id="`${titleId}-te`"
          class="field-error"
          role="alert"
        >
          {{ timeError }}
        </p>
      </div>
      <footer class="dt-confirm">
        <span class="dt-confirm-label">{{ title }}</span>
        <strong
          v-if="!full"
          aria-live="polite"
          data-test="dt-summary"
        >{{ summary }}</strong>
        <span
          v-else
          class="dt-confirm-value"
          aria-live="polite"
          data-test="dt-summary"
        >
          <span>{{ summaryDate || "Choisis un jour" }}</span>
          <strong v-if="withTime && time">{{ clockLabel(time) }}</strong>
        </span>
        <button
          type="button"
          class="primary dt-confirm-button"
          :disabled="!canConfirm"
          data-test="dt-confirm"
          @click="confirm"
        >
          Valider
        </button>
      </footer>
    </div>
  </section>
</template>
