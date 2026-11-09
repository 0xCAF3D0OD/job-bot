<script setup lang="ts">
import { nextTick, ref } from "vue";

import { api } from "../api/client";
import type { components } from "../api/schema";
import DateTimeField from "./DateTimeField.vue";
import DateTimePanel from "./DateTimePanel.vue";
import FormField from "./FormField.vue";
import { usePhone } from "../composables/usePhone";

// Le prochain rendez-vous ORP (maquette RendezVous, état `vide`, 7.11.2026) : la date et l'heure côte à côte,
// le lieu ou le lien, facultatif. En modification, le conseiller en plus (docs/83). Maquette du 8 novembre (D26) : les
// pilules date et heure (DateTimeField) ; un clic ouvre le sélecteur (DateTimePanel), qui prend la place du formulaire.
type Page = components["schemas"]["MeetingPage"];
type Meeting = components["schemas"]["MeetingOut"];

// `inline` : dans le panneau de détail de l'ordinateur (lot 11.5), sans carte autour, le titre de 26 px et sa phrase ;
// `canCancel` : « Annuler » aussi pour un nouveau rendez-vous.
const props = defineProps<{ meeting?: Meeting | null; inline?: boolean; canCancel?: boolean }>();
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
const picking = ref<"" | "date" | "time">("");
const { phone } = usePhone();
const form = ref<HTMLFormElement | null>(null);
function picked(value: { date: string; time: string }): void {
  day.value = value.date;
  time.value = value.time;
  picking.value = "";
  checkDay();
  checkTime();
  void nextTick(() => form.value?.querySelector<HTMLElement>("[data-test=dt-date]")?.focus());
}
function cancelPick(): void {
  const which = picking.value;
  picking.value = "";
  void nextTick(() => form.value?.querySelector<HTMLElement>(`[data-test=dt-${which || "date"}]`)?.focus());
}

// Règles §4 (Formulaire) : l'erreur sous le champ, en le quittant puis à l'envoi ; à l'envoi, le curseur y va.
function checkDay(): void {
  dayError.value = day.value ? "" : "Indique la date du rendez-vous.";
}
function checkTime(): void {
  timeError.value = time.value ? "" : "Indique l'heure.";
}

async function save(): Promise<void> {
  checkDay();
  checkTime();
  if (dayError.value || timeError.value) {
    await nextTick();
    form.value?.querySelector<HTMLElement>(dayError.value ? "[data-test=dt-date]" : "[data-test=dt-time]")?.focus();
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
  <DateTimePanel
    v-if="picking"
    :date="day"
    :time="time"
    title="Prochain rendez-vous ORP"
    :full="phone"
    @confirm="picked"
    @cancel="cancelPick"
  />
  <form
    v-else
    ref="form"
    :class="['rdv-form', { 'rdv-form-inline': inline }]"
    aria-labelledby="rdv-form-title"
    data-test="meeting-form"
    novalidate
    @submit.prevent="save"
  >
    <div v-if="inline">
      <h2 id="rdv-form-title">
        {{ meeting ? "Le prochain rendez-vous" : "Prochain rendez-vous ORP" }}
      </h2>
      <p class="rdv-form-sentence">
        jobA1 prépare ta feuille la veille et te le rappelle le matin.
      </p>
    </div>
    <h3
      v-else
      id="rdv-form-title"
    >
      {{ meeting ? "Le prochain rendez-vous" : "Prochain rendez-vous ORP" }}
    </h3>
    <div class="rdv-form-when">
      <DateTimeField
        :date="day"
        :time="time"
        :open="picking"
        :compact="phone"
        :aria-invalid="dayError || timeError ? 'true' : undefined"
        @open="picking = $event"
      />
      <p
        v-if="dayError || timeError"
        class="field-error"
        role="alert"
        data-test="meeting-when-error"
      >
        {{ dayError || timeError }}
      </p>
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
        placeholder="Ex. : ORP Renens, rue de Lausanne 35"
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
    <div :class="{ 'rdv-form-actions': inline }">
      <button
        type="submit"
        class="primary action-1"
        data-test="meeting-save"
      >
        {{ meeting ? "Enregistrer le rendez-vous" : "Ajouter le rendez-vous" }}
      </button>
      <button
        v-if="meeting || canCancel"
        type="button"
        :class="inline ? 'rdv-form-cancel' : 'secondary'"
        data-test="meeting-cancel"
        @click="emit('cancel')"
      >
        Annuler
      </button>
    </div>
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
.rdv-form-when { display: grid; grid-template-columns: minmax(0, 1fr); gap: var(--space-2); }
.rdv-form .form-field { margin: 0; min-width: 0; }
.rdv-form input { width: 100%; min-width: 0; }
.rdv-form button { min-height: var(--form-52); border-radius: var(--radius-pill); font-size: var(--font-body); font-weight: var(--weight-bold); }
.rdv-form > div:last-child:not(.rdv-form-actions) { display: contents; }
/* Ordinateur, dans le panneau de détail (lot 11.5, CandidaturesOrdinateurB `ajrv`) : pas de carte autour du formulaire,
   560 px au plus, le titre de 26 px et sa phrase, 20 px entre les blocs ; « Annuler » en bouton texte. */
.rdv-form.rdv-form-inline { --form-26: 26px; --form-32: 32px; --form-20: 20px; --form-6: 6px; gap: var(--form-20); max-width: 560px; padding: 0; border: 0; border-radius: 0; background: none; animation: ja-slide-l 200ms cubic-bezier(.05,.7,.1,1); }
.rdv-form-inline h2 { margin: 0; font-size: var(--form-26); line-height: var(--form-32); font-weight: var(--weight-heavy); }
.rdv-form-sentence { margin: var(--form-6) 0 0; font-size: var(--font-label); color: var(--text-secondary); }
.rdv-form-actions { display: flex; flex-wrap: wrap; gap: var(--space-2); }
.rdv-form-actions .primary { padding: 0 var(--space-6); }
.rdv-form-actions .rdv-form-cancel { padding: 0 var(--space-4); border: 0; background: transparent; color: var(--primary-text); }
</style>
