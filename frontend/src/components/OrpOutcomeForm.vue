<script setup lang="ts">
import { ref } from "vue";

import { api } from "../api/client";
import type { components } from "../api/schema";

// Ce qui a été convenu au rendez-vous ORP (docs/83 §1, 0.67.2). En l'enregistrant, jobA1 met
// à jour l'objectif du mois, les formations accordées et le rendez-vous suivant.
type Page = components["schemas"]["MeetingPage"];
type Meeting = components["schemas"]["MeetingOut"];

const props = defineProps<{ meeting: Meeting; target: number | null; trainings: Page["trainings"] }>();
const emit = defineEmits<{ saved: [page: Page]; cancel: [] }>();

function localInput(iso: string | null | undefined): string {
  if (!iso) return "";
  const at = new Date(iso);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${at.getFullYear()}-${pad(at.getMonth() + 1)}-${pad(at.getDate())}T${pad(at.getHours())}:${pad(at.getMinutes())}`;
}

const linked = props.meeting.measures.filter((m) => m.training_id != null).map((m) => m.training_id as number);
const target = ref<number | null>(props.meeting.agreed_target ?? props.target);
const granted = ref<number[]>(linked);
const others = ref(
  props.meeting.measures
    .filter((m) => m.training_id == null)
    .map((m) => m.text)
    .join("\n"),
);
const assignments = ref(props.meeting.assignments ?? "");
const note = ref(props.meeting.note ?? "");
const next = ref(localInput(props.meeting.next_starts_at));
const message = ref("");

async function save(): Promise<void> {
  const measures = [
    ...props.trainings.filter((t) => granted.value.includes(t.id)).map((t) => ({ text: t.title, training_id: t.id })),
    ...others.value
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean)
      .map((text) => ({ text, training_id: null })),
  ];
  const { data, error } = await api.PUT("/api/orp-meeting/{meeting_id}/convenu", {
    params: { path: { meeting_id: props.meeting.id } },
    body: {
      target: target.value || null,
      measures,
      assignments: assignments.value,
      note: note.value,
      next_starts_at: next.value ? new Date(next.value).toISOString() : null,
    },
  });
  if (data) emit("saved", data);
  else message.value = (error as { detail?: string } | undefined)?.detail ?? "Impossible d'enregistrer pour l'instant.";
}
</script>

<template>
  <form
    class="orp-outcome"
    data-test="outcome-form"
    @submit.prevent="save"
  >
    <label>
      Objectif mensuel de candidatures
      <input
        v-model.number="target"
        type="number"
        min="1"
        max="100"
        data-test="outcome-target"
      >
    </label>
    <fieldset v-if="trainings.length">
      <legend>Formations accordées</legend>
      <label
        v-for="training in trainings"
        :key="training.id"
        class="orp-outcome-check"
      >
        <input
          v-model="granted"
          type="checkbox"
          :value="training.id"
          :data-test="`outcome-training-${training.id}`"
        >
        {{ training.title }}
      </label>
    </fieldset>
    <label>
      Autres mesures (une par ligne)
      <textarea
        v-model="others"
        rows="2"
        maxlength="1000"
        placeholder="Stage, cours, programme d'emploi temporaire"
      />
    </label>
    <label>
      Assignations reçues
      <textarea
        v-model="assignments"
        rows="2"
        maxlength="2000"
      />
    </label>
    <label>
      Prochain rendez-vous
      <input
        v-model="next"
        type="datetime-local"
        data-test="outcome-next"
      >
    </label>
    <label>
      Note
      <textarea
        v-model="note"
        rows="2"
        maxlength="4000"
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
    <div class="form-actions">
      <button
        type="submit"
        data-test="outcome-save"
      >
        Enregistrer
      </button>
      <button
        type="button"
        class="secondary"
        @click="emit('cancel')"
      >
        Annuler
      </button>
    </div>
  </form>
</template>
