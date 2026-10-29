<script setup lang="ts">
import { nextTick, ref } from "vue";

import type { ApplicationStatus, ApplicationUpdate } from "../api/client";
import { applicationStatusLabel, methodLabel } from "../format";
import { email, useChecks, type Check } from "../validators";
import FormField from "./FormField.vue";

export type ApplicationFormValue = ApplicationUpdate & { offer_id?: number | null };

const props = defineProps<{
  title: string;
  initial: ApplicationFormValue;
  // Le statut de suivi n'a de sens qu'une fois la candidature enregistrée.
  withStatus: boolean;
  error?: string;
}>();
const emit = defineEmits<{ submit: [value: ApplicationFormValue]; close: [] }>();

const form = ref<ApplicationFormValue>({
  ...props.initial,
  company_address: props.initial.company_address ?? "",
  contact_name: props.initial.contact_name ?? "",
  contact_phone: props.initial.contact_phone ?? "",
  contact_email: props.initial.contact_email ?? "",
  location: props.initial.location ?? "",
  rate_text: props.initial.rate_text ?? "",
  application_url: props.initial.application_url ?? "",
  status_reason: props.initial.status_reason ?? "",
});
// Règles §4 (Champ de formulaire, Formulaire) : l'erreur sous le champ, en le quittant puis à l'envoi,
// et dit quoi faire ; à l'envoi, le curseur va au premier champ en erreur.
const filled =
  (message: string): Check =>
  (value) =>
    value.trim() ? null : message;
const { errors, check, clearIfFixed, validate } = useChecks(
  {
    sent_at: filled("Indique la date d'envoi."),
    company: filled("Indique l'entreprise."),
    job_title: filled("Indique le poste."),
    contact_email: email,
  },
  (field) => String(form.value[field] ?? ""),
  "application",
);
const STATUSES = Object.entries(applicationStatusLabel) as [ApplicationStatus, string][];

const formEl = ref<HTMLFormElement | null>(null);
async function submit(): Promise<void> {
  if (validate()) {
    emit("submit", form.value);
    return;
  }
  await nextTick();
  formEl.value?.querySelector<HTMLElement>("[aria-invalid='true']")?.focus();
}
</script>

<template>
  <div
    class="overlay"
    @click.self="emit('close')"
  >
    <form
      ref="formEl"
      class="form-card editor application-form"
      data-test="application-form"
      novalidate
      @submit.prevent="submit"
    >
      <h3>
        {{ title }}
      </h3>
      <div class="form-grid">
        <FormField
          v-slot="{ id, describedby, invalid }"
          label="Date d'envoi"
          :width="10"
          :error="errors.sent_at"
        >
          <input
            :id="id"
            v-model="form.sent_at"
            type="date"
            required
            :aria-describedby="describedby"
            :aria-invalid="invalid"
            data-test="sent-at"
            @blur="check('sent_at')"
            @input="clearIfFixed('sent_at')"
          >
        </FormField>
        <FormField
          v-slot="{ id, describedby, invalid }"
          label="Mode"
        >
          <select
            :id="id"
            v-model="form.method"
            :aria-describedby="describedby"
            :aria-invalid="invalid"
            data-test="method"
          >
            <option
              v-for="(label, value) in methodLabel"
              :key="value"
              :value="value"
            >
              {{ label }}
            </option>
          </select>
        </FormField>
        <FormField
          v-slot="{ id, describedby, invalid }"
          class="wide"
          label="Entreprise"
          :width="20"
          :error="errors.company"
        >
          <input
            :id="id"
            v-model="form.company"
            type="text"
            required
            :aria-describedby="describedby"
            :aria-invalid="invalid"
            data-test="company"
            @blur="check('company')"
            @input="clearIfFixed('company')"
          >
        </FormField>
        <FormField
          v-slot="{ id, describedby, invalid }"
          class="wide"
          label="Poste"
          :error="errors.job_title"
        >
          <input
            :id="id"
            v-model="form.job_title"
            type="text"
            required
            :aria-describedby="describedby"
            :aria-invalid="invalid"
            data-test="job-title"
            @blur="check('job_title')"
            @input="clearIfFixed('job_title')"
          >
        </FormField>
        <FormField
          v-slot="{ id, describedby, invalid }"
          class="wide"
          label="Adresse de l'entreprise"
          optional
        >
          <input
            :id="id"
            v-model="form.company_address"
            type="text"
            placeholder="Rue, NPA localité"
            :aria-describedby="describedby"
            :aria-invalid="invalid"
          >
        </FormField>
        <FormField
          v-slot="{ id, describedby, invalid }"
          label="Personne de contact"
          optional
          :width="20"
        >
          <input
            :id="id"
            v-model="form.contact_name"
            type="text"
            :aria-describedby="describedby"
            :aria-invalid="invalid"
          >
        </FormField>
        <FormField
          v-slot="{ id, describedby, invalid }"
          label="Téléphone du contact"
          optional
          :width="20"
        >
          <input
            :id="id"
            v-model="form.contact_phone"
            type="text"
            inputmode="tel"
            :aria-describedby="describedby"
            :aria-invalid="invalid"
          >
        </FormField>
        <FormField
          v-slot="{ id, describedby, invalid }"
          label="Courriel du contact"
          optional
          :error="errors.contact_email"
        >
          <input
            :id="id"
            v-model="form.contact_email"
            type="text"
            inputmode="email"
            maxlength="200"
            :aria-describedby="describedby"
            :aria-invalid="invalid"
            data-test="contact-email"
            @blur="check('contact_email')"
            @input="clearIfFixed('contact_email')"
          >
        </FormField>
        <FormField
          v-slot="{ id, describedby, invalid }"
          label="Lieu"
          optional
          :width="30"
        >
          <input
            :id="id"
            v-model="form.location"
            type="text"
            :aria-describedby="describedby"
            :aria-invalid="invalid"
          >
        </FormField>
        <FormField
          v-slot="{ id, describedby, invalid }"
          label="Taux"
          optional
        >
          <input
            :id="id"
            v-model="form.rate_text"
            type="text"
            placeholder="plein temps, temps partiel (80 %)…"
            :aria-describedby="describedby"
            :aria-invalid="invalid"
          >
        </FormField>
        <FormField
          v-slot="{ id, describedby, invalid }"
          class="wide"
          label="Lien de la candidature"
          optional
          hint="Le formulaire de l'employeur, l'annonce ou l'adresse e-mail utilisée."
        >
          <input
            :id="id"
            v-model="form.application_url"
            type="text"
            :aria-describedby="describedby"
            :aria-invalid="invalid"
            data-test="application-url"
          >
        </FormField>
      </div>
      <label class="check">
        <input
          v-model="form.assigned_by_orp"
          type="checkbox"
        >
        Assignée par l'ORP
      </label>
      <div
        v-if="withStatus"
        class="form-grid"
      >
        <FormField
          v-slot="{ id, describedby, invalid }"
          label="Statut"
        >
          <select
            :id="id"
            v-model="form.status"
            :aria-describedby="describedby"
            :aria-invalid="invalid"
            data-test="status"
          >
            <option
              v-for="[value, label] in STATUSES"
              :key="value"
              :value="value"
            >
              {{ label }}
            </option>
          </select>
        </FormField>
        <FormField
          v-slot="{ id, describedby, invalid }"
          label="Motif (refus…)"
          optional
        >
          <input
            :id="id"
            v-model="form.status_reason"
            type="text"
            :aria-describedby="describedby"
            :aria-invalid="invalid"
          >
        </FormField>
      </div>
      <p
        v-if="error"
        class="notice error"
        role="alert"
      >
        {{ error }}
      </p>
      <div class="form-actions">
        <button
          type="submit"
          class="primary"
          data-test="save-application"
        >
          Enregistrer la candidature
        </button>
        <button
          type="button"
          class="secondary"
          @click="emit('close')"
        >
          Annuler
        </button>
      </div>
    </form>
  </div>
</template>
