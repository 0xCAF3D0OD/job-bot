<script setup lang="ts">
import { computed, ref, watch } from "vue";

import { api } from "../api/client";
import type { components } from "../api/schema";
import { usePhone } from "../composables/usePhone";
import { dateText } from "../rendezVous";
import BottomSheet from "./BottomSheet.vue";

// Ce qui a été convenu au rendez-vous ORP (docs/83 §1 ; maquettes RendezVous et RendezVousOrdinateur, état
// `noter`, 7.11.2026) : une feuille du bas sur téléphone, un dialogue au centre sur ordinateur. Les recherches
// demandées en compteur, les mesures, le prochain rendez-vous (jobA1 le crée dans « À venir ») et une remarque.
// En l'enregistrant, le serveur met à jour l'objectif du mois et crée le rendez-vous suivant (0.67.2).
// Les formations accordées et les assignations d'avant sont gardées telles quelles : le dialogue ne les montre plus.
type Page = components["schemas"]["MeetingPage"];
type Meeting = components["schemas"]["MeetingOut"];

const props = defineProps<{ meeting: Meeting | null; target: number | null }>();
const emit = defineEmits<{ saved: [page: Page]; close: [] }>();
const { phone } = usePhone();

const count = ref(10);
const measures = ref("");
const nextDay = ref("");
const nextTime = ref("");
const note = ref("");
const message = ref("");
const busy = ref(false);

function pad(n: number): string {
  return String(n).padStart(2, "0");
}

// Les champs repartent de ce qui est noté, à chaque ouverture.
watch(
  () => props.meeting,
  (meeting) => {
    if (!meeting) return;
    count.value = meeting.agreed_target ?? props.target ?? 10;
    measures.value = meeting.measures
      .filter((m) => m.training_id == null)
      .map((m) => m.text)
      .join(", ");
    const next = meeting.next_starts_at ? new Date(meeting.next_starts_at) : null;
    nextDay.value = next ? `${next.getFullYear()}-${pad(next.getMonth() + 1)}-${pad(next.getDate())}` : "";
    nextTime.value = next ? `${pad(next.getHours())}:${pad(next.getMinutes())}` : "";
    note.value = meeting.note ?? "";
    message.value = "";
  },
  { immediate: true },
);

const subtitle = computed(() => (props.meeting ? `Rendez-vous ORP du ${dateText(props.meeting.starts_at).toLowerCase()}` : ""));
// À côté du compteur : ce qui était demandé jusqu'ici.
const before = computed(() => {
  if (!props.target) return "";
  return count.value === props.target ? "Comme le mois dernier" : `${props.target} le mois dernier`;
});

function step(delta: number): void {
  count.value = Math.min(100, Math.max(1, count.value + delta));
}

async function save(): Promise<void> {
  const meeting = props.meeting;
  if (!meeting || busy.value) return;
  const kept = meeting.measures.filter((m) => m.training_id != null).map((m) => ({ text: m.text, training_id: m.training_id ?? null }));
  const text = measures.value.trim();
  const next = nextDay.value ? new Date(`${nextDay.value}T${nextTime.value || "09:00"}`) : null;
  busy.value = true;
  try {
    const { data, error } = await api.PUT("/api/orp-meeting/{meeting_id}/convenu", {
      params: { path: { meeting_id: meeting.id } },
      body: {
        target: count.value,
        measures: [...kept, ...(text ? [{ text, training_id: null }] : [])],
        assignments: meeting.assignments ?? "",
        note: note.value,
        next_starts_at: next ? next.toISOString() : null,
      },
    });
    if (data) emit("saved", data);
    else message.value = (error as { detail?: string } | undefined)?.detail ?? "Impossible d'enregistrer pour l'instant.";
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <BottomSheet
    :open="!!meeting"
    title="Ce qui a été convenu"
    :subtitle="subtitle"
    class="outcome-sheet"
    data-test="outcome-sheet"
    @close="emit('close')"
  >
    <form
      id="orp-outcome"
      class="outcome-form"
      data-test="outcome-form"
      @submit.prevent="save"
    >
      <div
        class="outcome-field"
        role="group"
        aria-labelledby="outcome-count-label"
      >
        <span id="outcome-count-label">Recherches demandées par mois</span>
        <div class="outcome-counter">
          <button
            type="button"
            aria-label="Une de moins"
            data-test="outcome-less"
            @click="step(-1)"
          >
            −
          </button>
          <span
            aria-live="polite"
            data-test="outcome-target"
          >{{ count }}</span>
          <button
            type="button"
            aria-label="Une de plus"
            data-test="outcome-more"
            @click="step(1)"
          >
            +
          </button>
          <small v-if="before">{{ before }}</small>
        </div>
      </div>
      <label class="outcome-field">
        <span>Mesures décidées <em>(facultatif)</em></span>
        <input
          v-model="measures"
          type="text"
          maxlength="1000"
          placeholder="Cours, stage, programme…"
          data-test="outcome-measures"
        >
      </label>
      <div class="outcome-next">
        <label class="outcome-field">
          <span>Prochain rendez-vous</span>
          <input
            v-model="nextDay"
            type="date"
            data-test="outcome-next"
          >
        </label>
        <label class="outcome-field">
          <span>Heure</span>
          <input
            v-model="nextTime"
            type="time"
            data-test="outcome-next-time"
          >
        </label>
        <small>jobA1 le met dans tes Rendez-vous.</small>
      </div>
      <label class="outcome-field">
        <span>Autre chose à retenir <em>(facultatif)</em></span>
        <textarea
          v-model="note"
          rows="3"
          maxlength="4000"
          placeholder="Ce que ton conseiller t’a demandé"
          data-test="outcome-note"
        />
      </label>
      <p
        v-if="message"
        role="status"
        class="notice error"
      >
        {{ message }}
      </p>
    </form>
    <template #actions>
      <button
        v-if="!phone"
        type="button"
        class="secondary"
        @click="emit('close')"
      >
        Annuler
      </button>
      <button
        type="submit"
        form="orp-outcome"
        class="primary"
        :disabled="busy"
        data-test="outcome-save"
      >
        Enregistrer
      </button>
    </template>
  </BottomSheet>
</template>

<style>
/* Valeurs de la maquette : 560 px au centre sur ordinateur ; champs de 48 px aux bords de 1,5 px, coins de 12 ;
   le compteur en ronds de 44 px, le nombre en 24 très gras. */
.outcome-sheet { --out-6: 6px; --out-14: 14px; --out-18: 18px; --out-21: 21px; --out-22: 22px; --out-24: 24px; background: var(--surface); }
/* Le titre de la maquette : 21 px sur téléphone, 22 px sur ordinateur, en gras appuyé. */
.outcome-sheet .sheet-title { font-size: var(--out-21); font-weight: var(--weight-heavy); }
@media (min-width: 1024px) { .outcome-sheet .sheet-title { font-size: var(--out-22); } }
@media (min-width: 821px) { .sheet.outcome-sheet { width: min(560px, calc(100vw - 2 * var(--space-4))); } }
.outcome-form { display: flex; flex-direction: column; gap: var(--out-18); }
.outcome-field { display: flex; flex-direction: column; gap: var(--out-6); min-width: 0; }
.outcome-field > span, #outcome-count-label { font-size: var(--font-small); font-weight: var(--weight-bold); }
.outcome-field em { font-style: normal; font-weight: var(--weight-regular); color: var(--text-secondary); }
.outcome-field :is(input, textarea) {
  box-sizing: border-box; width: 100%; min-width: 0; padding: var(--space-3) var(--out-14); border: 1.5px solid var(--field-border);
  border-radius: var(--radius-sm); background: var(--surface); color: var(--text); font: inherit; font-size: var(--font-body);
}
.outcome-field input { height: var(--btn-secondary); padding-block: 0; }
.outcome-field textarea { resize: none; }
.outcome-counter { display: flex; align-items: center; gap: var(--out-14); }
.outcome-counter button {
  display: inline-flex; align-items: center; justify-content: center; width: var(--target-min); height: var(--target-min); min-height: 0; padding: 0; border: 1.5px solid var(--line); border-radius: 50%;
  background: var(--surface); color: var(--text); font-size: var(--out-22); font-weight: var(--weight-semibold);
}
.outcome-counter > span { min-width: 2.25rem; text-align: center; font-size: var(--out-24); font-weight: var(--weight-heavy); }
.outcome-counter small, .outcome-next small { font-size: var(--font-small); color: var(--text-secondary); }
.outcome-next { display: grid; grid-template-columns: 1fr 1fr; gap: var(--out-6) var(--space-3); }
.outcome-next small { grid-column: 1 / -1; }
.outcome-sheet .sheet-actions { justify-content: flex-end; margin: 0 calc(var(--space-4) * -1); padding: var(--space-3) var(--space-4) 0; border-top: 1px solid var(--line); }
.outcome-sheet .sheet-actions > button { min-height: var(--btn-secondary); padding: 0 var(--space-6); border-radius: var(--radius-pill); font-weight: var(--weight-bold); }
</style>
