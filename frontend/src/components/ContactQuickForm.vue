<script setup lang="ts">
import { ref } from "vue";

import { api, type Contact } from "../api/client";
import { isoDay } from "../contactLabels";
import FormField from "./FormField.vue";

// « J'ai contacté quelqu'un » (prompt du 10 novembre au soir, PR 28 ; maquettes CandidaturesOrdinateurB état `ct` et
// EnvoyeeDetailContacte) : Nom, Rôle (facultatif), Comment. Sur ordinateur, la carte dépliée sous l'historique, avec
// « Annuler » et « Enregistrer » à contour ; sur téléphone (`sheet`), dans la fenêtre du bas, la phrase d'abord et
// « Enregistrer » plein. Le contact est daté d'aujourd'hui ; il entre dans l'historique et la prochaine relance est
// proposée 7 jours après. Le rôle et le moyen restent des choix (ceux de docs/31), pour le journal et les rappels.
const props = defineProps<{ applicationId: number; sheet?: boolean }>();
const emit = defineEmits<{ saved: []; cancel: [] }>();

const ROLE_CHOICES: { value: Contact["role"]; label: string }[] = [
  { value: "recruiter", label: "Recrutement" },
  { value: "manager", label: "Futur responsable" },
  { value: "team", label: "Membre de l’équipe" },
  { value: "alumni", label: "Ancien de ton école" },
];
const CHANNEL_CHOICES: { value: Contact["channel"]; label: string }[] = [
  { value: "linkedin_message", label: "LinkedIn" },
  { value: "email", label: "E-mail" },
  { value: "phone", label: "Téléphone" },
  { value: "other", label: "Autre" },
];

const name = ref("");
const role = ref<Contact["role"] | "">("");
const channel = ref<Contact["channel"]>("linkedin_message");
const nameError = ref("");
const message = ref("");
const busy = ref(false);
const form = ref<HTMLFormElement | null>(null);

async function save(): Promise<void> {
  if (busy.value) return;
  nameError.value = name.value.trim() ? "" : "Indique le nom de la personne.";
  if (nameError.value) {
    form.value?.querySelector<HTMLElement>("[data-test=contact-name]")?.focus();
    return;
  }
  busy.value = true;
  message.value = "";
  try {
    const { data } = await api.POST("/api/contacts", {
      body: {
        application_id: props.applicationId,
        name: name.value.trim(),
        role: role.value || "other",
        channel: channel.value,
        contacted_on: isoDay(),
      },
    });
    if (!data) {
      message.value = "Enregistrement impossible : réessaie dans un instant.";
      return;
    }
    name.value = "";
    role.value = "";
    emit("saved");
  } catch {
    message.value = "Enregistrement impossible : réessaie dans un instant.";
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <form
    ref="form"
    :class="['contact-quick', { 'contact-quick-sheet': sheet }]"
    aria-label="J’ai contacté quelqu’un"
    novalidate
    data-test="contact-quick"
    @submit.prevent="save"
  >
    <p
      v-if="sheet"
      class="contact-quick-lead"
    >
      jobA1 le note dans l’historique et adapte la prochaine relance.
    </p>
    <div class="contact-quick-who">
      <FormField
        v-slot="{ id, describedby, invalid }"
        label="Nom"
        :error="nameError"
      >
        <input
          :id="id"
          v-model="name"
          type="text"
          maxlength="120"
          autocomplete="off"
          :aria-describedby="describedby"
          :aria-invalid="invalid"
          aria-required="true"
          data-test="contact-name"
        >
      </FormField>
      <FormField
        v-slot="{ id }"
        label="Rôle"
        optional
      >
        <select
          :id="id"
          v-model="role"
          data-test="contact-role"
        >
          <option value="">
            Non précisé
          </option>
          <option
            v-for="choice in ROLE_CHOICES"
            :key="choice.value"
            :value="choice.value"
          >
            {{ choice.label }}
          </option>
        </select>
      </FormField>
    </div>
    <FormField
      v-slot="{ id }"
      label="Comment"
    >
      <select
        :id="id"
        v-model="channel"
        data-test="contact-channel"
      >
        <option
          v-for="choice in CHANNEL_CHOICES"
          :key="choice.value"
          :value="choice.value"
        >
          {{ choice.label }}
        </option>
      </select>
    </FormField>
    <p
      v-if="message"
      class="field-error"
      role="alert"
      data-test="contact-error"
    >
      {{ message }}
    </p>
    <div class="contact-quick-actions">
      <button
        v-if="!sheet"
        type="button"
        class="contact-quick-cancel"
        data-test="contact-cancel"
        @click="emit('cancel')"
      >
        Annuler
      </button>
      <button
        type="submit"
        :class="sheet ? 'primary contact-quick-save' : 'contact-quick-save contact-quick-outline'"
        :aria-disabled="busy ? 'true' : undefined"
        data-test="contact-save"
      >
        Enregistrer
      </button>
    </div>
  </form>
</template>

<style>
/* Ordinateur : la carte blanche dépliée, 12 px sous le bouton, 20 dedans, trait de 1,5 px, rayon 18 ; Nom et Rôle sur une
   ligne, 12 px entre eux, 16 entre les blocs ; « Annuler » en texte et « Enregistrer » à contour, 44 px, à droite.
   Téléphone (fenêtre du bas) : sans carte, les champs l'un sous l'autre, « Enregistrer » plein de 52 px. */
.contact-quick { --cq-pad: 18px; --cq-save-h: 52px; display: flex; flex-direction: column; gap: var(--space-4); margin-top: var(--space-3); padding: var(--space-5); background: var(--surface); border: var(--action-line) solid var(--card-line); border-radius: var(--radius-card); }
.contact-quick .form-field { margin: 0; min-width: 0; }
.contact-quick-who { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: var(--space-3); }
.contact-quick-actions { display: flex; justify-content: flex-end; gap: var(--space-3); }
.contact-quick-actions button { height: var(--target-min); min-height: var(--target-min); padding: 0 var(--cq-pad); border-radius: var(--radius-pill); font-size: calc(var(--font-small) + 1px); font-weight: var(--weight-bold); }
.contact-quick-cancel { border: 0; background: transparent; color: var(--primary-text); }
.contact-quick-outline { border: var(--action-line) solid var(--action); background: var(--surface); color: var(--primary-text); }
.contact-quick-save[aria-disabled="true"] { opacity: 0.6; cursor: default; }
.contact-quick.contact-quick-sheet { margin: 0; padding: 0; border: 0; border-radius: 0; background: none; }
.contact-quick-sheet .contact-quick-who { grid-template-columns: minmax(0, 1fr); gap: var(--space-4); }
.contact-quick-lead { margin: 0; font-size: calc(var(--font-small) + 1px); line-height: var(--cq-lead-lh, 22px); color: var(--text-tertiary); }
.contact-quick-sheet .contact-quick-actions { display: grid; }
.contact-quick-sheet .contact-quick-actions button { width: 100%; height: var(--cq-save-h); min-height: var(--cq-save-h); justify-content: center; font-size: var(--font-body); }
</style>
