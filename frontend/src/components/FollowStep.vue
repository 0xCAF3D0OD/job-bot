<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { api, type Application } from "../api/client";
import { applicationBody } from "../applicationBody";
import { dateInSentence } from "../dates";
import AppIcon from "./AppIcon.vue";

// ④ Suivre, après « Marquer comme envoyée » (docs/124 §G) : ce que jobA1 fera ensuite, en trois
// lignes séparées par un filet, une action au plus chacune. La relance (le jour choisi, sinon
// 10 jours après l'envoi), la preuve ORP (complète, ou le champ qui manque, sur place), le
// contact (le nom, ou « Ajouter un contact » qui mène aux contacts à côté).
const props = defineProps<{ offerId: number }>();
const emit = defineEmits<{ addContact: [] }>();

const REMIND_AFTER_DAYS = 10;
const MIN_DAYS = 5;
const MAX_DAYS = 30;

const application = ref<Application | null>(null);
const missing = ref<string[]>([]);
const editing = ref<"date" | "address" | null>(null);
const draft = ref("");
const error = ref("");

function shift(day: string, days: number): string {
  const d = new Date(`${day}T12:00:00`);
  d.setDate(d.getDate() + days);
  return d.toISOString().slice(0, 10);
}

async function load(): Promise<void> {
  const { data } = await api.GET("/api/applications", { params: { query: { offer: props.offerId } } });
  application.value = data?.[0] ?? null;
  if (!application.value) return;
  const orp = await api.GET("/api/orp", { params: { query: { month: application.value.orp_month } } });
  missing.value = orp.data?.rows.find((r) => r.application_id === application.value?.id)?.missing ?? [];
}
onMounted(load);

const remindOn = computed(() => {
  const a = application.value;
  return a ? (a.follow_up_on ?? shift(a.sent_at, REMIND_AFTER_DAYS)) : "";
});
// « Le 30 octobre » en tête de phrase : la date de phrase (dates.ts) avec sa majuscule.
const remindText = computed(() => dateInSentence(`${remindOn.value}T12:00:00`).replace(/^le/, "Le"));
const contact = computed(() => application.value?.contact_name || application.value?.contacts.find((c) => c.name)?.name || "");

function start(what: "date" | "address"): void {
  error.value = "";
  draft.value = what === "date" ? remindOn.value : (application.value?.company_address ?? "");
  editing.value = what;
}

async function save(): Promise<void> {
  const a = application.value;
  if (!a) return;
  error.value = "";
  if (editing.value === "date") {
    const { data } = await api.PATCH("/api/applications/{application_id}/follow-up-date", {
      params: { path: { application_id: a.id } },
      body: { follow_up_on: draft.value || null },
    });
    if (!data) {
      error.value = `Choisis un jour entre ${MIN_DAYS} et ${MAX_DAYS} jours après l'envoi.`;
      return;
    }
    application.value = { ...a, follow_up_on: data.follow_up_on };
  } else if (editing.value === "address") {
    const { data } = await api.PUT("/api/applications/{application_id}", {
      params: { path: { application_id: a.id } },
      body: {
        ...applicationBody({ ...a, company_address: draft.value }),
        status: a.status,
        status_reason: a.status_reason ?? null,
        status_at: a.status_at ?? null,
        interview_at: a.interview_at ?? null,
      },
    });
    if (!data) {
      error.value = "L'adresse n'a pas pu être enregistrée. Réessaie.";
      return;
    }
    await load();
  }
  editing.value = null;
}
</script>

<template>
  <section
    v-if="application"
    class="follow-step"
    data-test="follow-step"
  >
    <p class="follow-lead">
      Bien joué. jobA1 s'occupe du reste.
    </p>
    <ul class="follow-rows">
      <li data-test="follow-remind">
        <span class="follow-name">Relance</span>
        <span
          v-if="editing === 'date'"
          class="follow-edit"
        >
          <input
            v-model="draft"
            type="date"
            :min="shift(application.sent_at, MIN_DAYS)"
            :max="shift(application.sent_at, MAX_DAYS)"
            aria-label="Jour de la relance"
            data-test="follow-date"
          >
          <button
            type="button"
            class="primary small"
            data-test="follow-save"
            @click="save"
          >Enregistrer</button>
          <button
            type="button"
            class="link"
            @click="editing = null"
          >Annuler</button>
        </span>
        <template v-else>
          <span
            v-if="application.status === 'en_attente'"
            class="follow-value"
          >{{ remindText }}, si l'employeur n'a pas répondu.</span>
          <span
            v-else
            class="follow-value muted"
          >Plus de relance prévue.</span>
          <button
            v-if="application.status === 'en_attente'"
            type="button"
            class="link"
            data-test="follow-change-date"
            @click="start('date')"
          >
            Changer la date
          </button>
        </template>
      </li>
      <li data-test="follow-orp">
        <span class="follow-name">Preuve ORP</span>
        <span
          v-if="editing === 'address'"
          class="follow-edit"
        >
          <input
            v-model="draft"
            type="text"
            aria-label="Adresse de l'entreprise"
            placeholder="Rue, NPA et localité"
            data-test="follow-address"
          >
          <button
            type="button"
            class="primary small"
            data-test="follow-save"
            @click="save"
          >Enregistrer</button>
          <button
            type="button"
            class="link"
            @click="editing = null"
          >Annuler</button>
        </span>
        <template v-else-if="missing.length">
          <span class="follow-value">Il manque {{ missing.join(", ") }}.</span>
          <button
            type="button"
            class="link"
            data-test="follow-complete"
            @click="start('address')"
          >
            Compléter
          </button>
        </template>
        <span
          v-else
          class="follow-value with-icon follow-ok"
        ><AppIcon name="check" />Complète</span>
      </li>
      <li data-test="follow-contact">
        <span class="follow-name">Contact</span>
        <span
          v-if="contact"
          class="follow-value"
        >{{ contact }}</span>
        <button
          v-else
          type="button"
          class="link"
          data-test="follow-add-contact"
          @click="emit('addContact')"
        >
          Ajouter un contact
        </button>
      </li>
    </ul>
    <p
      v-if="error"
      class="notice error"
    >
      {{ error }}
    </p>
  </section>
</template>
