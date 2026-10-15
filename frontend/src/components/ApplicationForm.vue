<script setup lang="ts">
import { ref } from "vue";

import type { ApplicationStatus, ApplicationUpdate } from "../api/client";
import { applicationStatusLabel, methodLabel } from "../format";
import AppIcon from "./AppIcon.vue";
import HelpTip from "./HelpTip.vue";
import { email, useChecks } from "../validators";

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
const { errors, check, clearIfFixed, validate } = useChecks(
  { contact_email: email },
  (field) => form.value[field] ?? "",
  "application",
);
const STATUSES = Object.entries(applicationStatusLabel) as [ApplicationStatus, string][];
</script>

<template>
  <div
    class="overlay"
    @click.self="emit('close')"
  >
    <form
      class="form-card editor application-form"
      data-test="application-form"
      @submit.prevent="validate() && emit('submit', form)"
    >
      <h3>
        {{ title }}
        <HelpTip
          text="Ces informations alimentent le formulaire ORP « preuves des recherches d'emploi »."
          label="Aide : candidature"
        />
      </h3>
      <div class="form-grid">
        <label>Date d'envoi
          <input
            v-model="form.sent_at"
            type="date"
            required
            data-test="sent-at"
          >
        </label>
        <label>Mode
          <select
            v-model="form.method"
            data-test="method"
          >
            <option
              v-for="(label, value) in methodLabel"
              :key="value"
              :value="value"
            >{{ label }}</option>
          </select>
        </label>
        <label class="wide">Entreprise
          <input
            v-model="form.company"
            type="text"
            required
            data-test="company"
          >
        </label>
        <label class="wide">Poste
          <input
            v-model="form.job_title"
            type="text"
            required
          >
        </label>
        <label class="wide">Adresse de l'entreprise
          <input
            v-model="form.company_address"
            type="text"
            placeholder="Rue, NPA localité"
          >
        </label>
        <label>Personne de contact
          <input
            v-model="form.contact_name"
            type="text"
          >
        </label>
        <label>Téléphone du contact
          <input
            v-model="form.contact_phone"
            type="text"
          >
        </label>
        <label>Courriel du contact
          <input
            id="application-contact_email"
            v-model="form.contact_email"
            type="text"
            inputmode="email"
            maxlength="200"
            data-test="contact-email"
            :aria-invalid="Boolean(errors.contact_email)"
            :aria-describedby="errors.contact_email ? 'application-contact_email-error' : undefined"
            @blur="check('contact_email')"
            @input="clearIfFixed('contact_email')"
          >
          <span
            v-if="errors.contact_email"
            id="application-contact_email-error"
            class="field-error"
          >{{ errors.contact_email }}</span>
        </label>
        <label>Lieu
          <input
            v-model="form.location"
            type="text"
          >
        </label>
        <label>Taux
          <input
            v-model="form.rate_text"
            type="text"
            placeholder="plein temps, temps partiel (80 %)…"
          >
        </label>
        <label class="wide">Lien de la candidature
          <input
            v-model="form.application_url"
            type="text"
            placeholder="formulaire de l'employeur, annonce ou adresse e-mail utilisée"
            data-test="application-url"
          >
        </label>
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
        <label>Statut
          <select
            v-model="form.status"
            data-test="status"
          >
            <option
              v-for="[value, label] in STATUSES"
              :key="value"
              :value="value"
            >{{ label }}</option>
          </select>
        </label>
        <label>Motif (refus…)
          <input
            v-model="form.status_reason"
            type="text"
          >
        </label>
      </div>
      <p
        v-if="error"
        class="notice error"
      >
        {{ error }}
      </p>
      <div class="form-actions">
        <button
          type="submit"
          class="primary"
          data-test="save-application"
        >
          Enregistrer <AppIcon name="chevron" />
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
