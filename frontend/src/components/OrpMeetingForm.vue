<script setup lang="ts">
import { nextTick, ref } from "vue";

import { api } from "../api/client";
import type { components } from "../api/schema";
import FormField from "./FormField.vue";

// Le prochain rendez-vous ORP (maquette RendezVous, état `vide`, 7.11.2026) : la date et l'heure côte à côte,
// le lieu ou le lien, facultatif. En modification, le conseiller en plus (docs/83).
type Page = components["schemas"]["MeetingPage"];
type Meeting = components["schemas"]["MeetingOut"];

const props = defineProps<{ meeting?: Meeting | null }>();
const emit = defineEmits<{ saved: [page: Page]; cancel: [] }>();

function pad(n: number): string {
  return String(n).padStart(2, "0");
}
const start = props.meeting ? new Date(props.meeting.starts_at) : null;
const day = ref(start ? `${start.getFullYear()}-${pad(start.getMonth() + 1)}-${pad(start.getDate())}` : "");
const time = ref(start ? `${pad(start.getHours())}:${pad(start.getMinutes())}` : "");
const place = ref(props.meeting?.place ?? "");
const advisor = ref(props.meeting?.advisor ?? "");
const dayError = ref("");
const timeError = ref("");
const message = ref("");

// Règles §4 (Formulaire) : l'erreur sous le champ, en le quittant puis à l'envoi ; à l'envoi, le curseur y va.
function checkDay(): void {
  dayError.value = day.value ? "" : "Indique la date du rendez-vous.";
}
function checkTime(): void {
  timeError.value = time.value ? "" : "Indique l'heure.";
}

async function save(event: Event): Promise<void> {
  const form = event.currentTarget as HTMLElement | null;
  checkDay();
  checkTime();
  if (dayError.value || timeError.value) {
    await nextTick();
    form?.querySelector<HTMLElement>("[aria-invalid='true']")?.focus();
    return;
  }
  const { data, error } = await api.PUT("/api/orp-meeting", {
    body: { starts_at: new Date(`${day.value}T${time.value}`).toISOString(), place: place.value, advisor: advisor.value },
  });
  if (data) emit("saved", data);
  else message.value = (error as { detail?: string } | undefined)?.detail ?? "Impossible d'enregistrer pour l'instant.";
}
</script>

<template>
  <form
    class="rdv-form"
    aria-labelledby="rdv-form-title"
    data-test="meeting-form"
    novalidate
    @submit.prevent="save"
  >
    <h3 id="rdv-form-title">
      {{ meeting ? "Le prochain rendez-vous" : "Prochain rendez-vous ORP" }}
    </h3>
    <div class="rdv-form-when">
      <FormField
        v-slot="{ id, describedby, invalid }"
        label="Date"
        :error="dayError"
      >
        <input
          :id="id"
          v-model="day"
          type="date"
          required
          :aria-describedby="describedby"
          :aria-invalid="invalid"
          data-test="meeting-date"
          @blur="checkDay"
          @input="dayError && checkDay()"
        >
      </FormField>
      <FormField
        v-slot="{ id, describedby, invalid }"
        label="Heure"
        :error="timeError"
      >
        <input
          :id="id"
          v-model="time"
          type="time"
          required
          :aria-describedby="describedby"
          :aria-invalid="invalid"
          data-test="meeting-time"
          @blur="checkTime"
          @input="timeError && checkTime()"
        >
      </FormField>
    </div>
    <FormField
      v-slot="{ id, describedby, invalid }"
      label="Lieu ou lien"
      optional
    >
      <input
        :id="id"
        v-model="place"
        type="text"
        maxlength="200"
        placeholder="ORP Renens, rue de Lausanne 35"
        :aria-describedby="describedby"
        :aria-invalid="invalid"
        data-test="meeting-place"
      >
    </FormField>
    <FormField
      v-if="meeting"
      v-slot="{ id, describedby, invalid }"
      label="Conseiller"
      optional
    >
      <input
        :id="id"
        v-model="advisor"
        type="text"
        maxlength="120"
        :aria-describedby="describedby"
        :aria-invalid="invalid"
      >
    </FormField>
    <p
      v-if="message"
      role="status"
      class="notice error"
    >
      {{ message }}
    </p>
    <button
      type="submit"
      class="primary"
      data-test="meeting-save"
    >
      {{ meeting ? "Enregistrer le rendez-vous" : "Ajouter le rendez-vous" }}
    </button>
    <button
      v-if="meeting"
      type="button"
      class="secondary"
      @click="emit('cancel')"
    >
      Annuler
    </button>
  </form>
</template>

<style>
/* Maquette : une carte blanche, 16 de marge, écart 14 ; date et heure en 1,4 fr et 1 fr ; champs de 48 px aux
   bords de 1,5 px ; le bouton de 52 px, en pilule. */
.rdv-form {
  --form-14: 14px; --form-17: 17px; --form-52: 52px;
  display: flex; flex-direction: column; gap: var(--form-14); padding: var(--space-4); background: var(--surface);
  border: 1px solid var(--line); border-radius: var(--radius-card);
}
.rdv-form h3 { margin: 0; font-size: var(--form-17); font-weight: var(--weight-bold); }
.rdv-form-when { display: grid; grid-template-columns: 1.4fr 1fr; gap: var(--space-2); }
.rdv-form .form-field { margin: 0; min-width: 0; }
.rdv-form input { box-sizing: border-box; width: 100%; min-width: 0; height: var(--btn-secondary); border: 1.5px solid var(--field-border); border-radius: var(--radius-sm); font-size: var(--font-body); }
.rdv-form button { min-height: var(--form-52); border-radius: var(--radius-pill); font-size: var(--font-body); font-weight: var(--weight-bold); }
</style>
