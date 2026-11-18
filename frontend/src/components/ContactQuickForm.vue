<script setup lang="ts">
import { ref, useId } from "vue";

import { radioKey } from "../radioKey";

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

// Rôle et Comment en pastilles (Kevin, 18.11, §72 ; planche EnvoyeeDetailContacte) : un choix à la fois, un nouveau clic
// sur la pastille choisie la désélectionne ; « Autre » ouvre un champ « Précise », gardé dans la note du contact.
const ROLE_CHOICES: { value: Contact["role"]; label: string }[] = [
  { value: "recruiter", label: "Recrutement" },
  { value: "manager", label: "Responsable du poste" },
  { value: "team", label: "Équipe" },
  { value: "other", label: "Autre" },
];
const CHANNEL_CHOICES: { value: Contact["channel"]; label: string }[] = [
  { value: "linkedin_message", label: "LinkedIn" },
  { value: "email", label: "E-mail" },
  { value: "phone", label: "Téléphone" },
  { value: "in_person", label: "En personne" },
  { value: "other", label: "Autre" },
];

const name = ref("");
const role = ref<Contact["role"] | "">("");
const channel = ref<Contact["channel"] | "">("linkedin_message");
const roleOther = ref("");
const channelOther = ref("");
const nameError = ref("");
const message = ref("");
const busy = ref(false);
const form = ref<HTMLFormElement | null>(null);

const roleLabel = useId();
const channelLabel = useId();
function pickRole(value: Contact["role"]): void {
  role.value = role.value === value ? "" : value;
}
function pickChannel(value: Contact["channel"]): void {
  channel.value = channel.value === value ? "" : value;
}
// Le groupe a une seule entrée au clavier : la pastille choisie, sinon la première.
function tabStop<T extends string>(current: T | "", value: T, first: T): 0 | -1 {
  return current === value || (!current && value === first) ? 0 : -1;
}
function note(): string | null {
  const parts = [
    role.value === "other" && roleOther.value.trim() ? `Rôle : ${roleOther.value.trim()}` : "",
    channel.value === "other" && channelOther.value.trim() ? `Moyen : ${channelOther.value.trim()}` : "",
  ].filter(Boolean);
  return parts.length ? parts.join(" · ") : null;
}

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
        channel: channel.value || "other",
        contacted_on: isoDay(),
        note: note(),
      },
    });
    if (!data) {
      message.value = "Enregistrement impossible : réessaie dans un instant.";
      return;
    }
    name.value = "";
    role.value = "";
    roleOther.value = "";
    channelOther.value = "";
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
    </div>
    <div class="contact-quick-choices">
      <div
        :id="roleLabel"
        class="contact-quick-label"
      >
        Son rôle<span class="contact-quick-optional"> · facultatif</span>
      </div>
      <div
        class="filter-choices-row"
        role="radiogroup"
        :aria-labelledby="roleLabel"
        data-test="contact-role"
        @keydown="radioKey"
      >
        <button
          v-for="choice in ROLE_CHOICES"
          :key="choice.value"
          type="button"
          class="filter-choice contact-choice"
          role="radio"
          :aria-checked="role === choice.value"
          :tabindex="tabStop(role, choice.value, 'recruiter')"
          :data-test="`contact-role-${choice.value}`"
          @click="pickRole(choice.value)"
        >
          {{ choice.label }}
        </button>
      </div>
      <input
        v-if="role === 'other'"
        v-model="roleOther"
        type="text"
        class="contact-quick-other"
        maxlength="200"
        placeholder="Précise"
        aria-label="Son rôle, autre"
        data-test="contact-role-precise"
      >
    </div>
    <div class="contact-quick-choices">
      <div
        :id="channelLabel"
        class="contact-quick-label"
      >
        Comment
      </div>
      <div
        class="filter-choices-row"
        role="radiogroup"
        :aria-labelledby="channelLabel"
        data-test="contact-channel"
        @keydown="radioKey"
      >
        <button
          v-for="choice in CHANNEL_CHOICES"
          :key="choice.value"
          type="button"
          class="filter-choice contact-choice"
          role="radio"
          :aria-checked="channel === choice.value"
          :tabindex="tabStop(channel, choice.value, 'linkedin_message')"
          :data-test="`contact-channel-${choice.value}`"
          @click="pickChannel(choice.value)"
        >
          {{ choice.label }}
        </button>
      </div>
      <input
        v-if="channel === 'other'"
        v-model="channelOther"
        type="text"
        class="contact-quick-other"
        maxlength="200"
        placeholder="Précise"
        aria-label="Comment, autre"
        data-test="contact-channel-precise"
      >
    </div>
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
.contact-quick-who { display: grid; grid-template-columns: minmax(0, 1fr); gap: var(--space-3); }
/* Rôle et Comment (planche EnvoyeeDetailContacte, §72) : titre 14/700, 4 px au-dessus et 8 px en dessous ; pastilles de
   44 px, 14 px de côté, 15/600, trait de 1,5 px (2 px bleu pour la choisie), 8 px entre elles ; « Précise » 52 px à 10 px. */
.contact-quick-choices { display: grid; }
.contact-quick-label { margin: var(--space-1) 0 var(--space-2); font-size: var(--font-small); font-weight: var(--weight-bold); color: var(--text); }
.contact-quick-optional { font-weight: var(--weight-medium); color: var(--text-secondary); }
.contact-quick .contact-choice { min-height: var(--target-min); padding: 0 var(--cq-chip-pad, 14px); border: 0; box-shadow: inset 0 0 0 var(--action-line) var(--card-line); font-size: var(--cq-chip-font, 15px); font-weight: var(--weight-semibold); }
.contact-quick .contact-choice[aria-checked="true"] { box-shadow: inset 0 0 0 2px var(--primary-graphic); }
.contact-quick .contact-quick-other { display: block; width: 100%; height: var(--cq-save-h); margin-top: var(--cq-other-gap, 10px); padding: 0 var(--cq-other-pad, 14px); border: 2px solid var(--primary-graphic); border-radius: var(--radius-field, 12px); background: var(--surface); font-size: var(--font-body); color: var(--text); }
.contact-quick-actions { display: flex; justify-content: flex-end; gap: var(--space-3); }
.contact-quick-actions button { height: var(--target-min); min-height: var(--target-min); padding: 0 var(--cq-pad); border-radius: var(--radius-pill); font-size: calc(var(--font-small) + 1px); font-weight: var(--weight-bold); }
.contact-quick-cancel { border: 0; background: transparent; color: var(--primary-text); }
.contact-quick-outline { border: var(--action-line) solid var(--action); background: var(--surface); color: var(--primary-text); }
.contact-quick-save[aria-disabled="true"] { opacity: 0.6; cursor: default; }
.contact-quick.contact-quick-sheet { margin: 0; padding: 0; border: 0; border-radius: 0; background: none; }
.contact-quick-sheet .contact-quick-who { grid-template-columns: minmax(0, 1fr); gap: var(--space-4); }
.contact-quick-lead { margin: 0; font-size: calc(var(--font-small) + 1px); line-height: var(--cq-lead-lh, 22px); color: var(--text-tertiary); }
.contact-quick-sheet .contact-quick-actions { display: grid; justify-content: stretch; }
.contact-quick-sheet .contact-quick-actions button { width: 100%; height: var(--cq-save-h); min-height: var(--cq-save-h); justify-content: center; font-size: var(--font-body); }
</style>
