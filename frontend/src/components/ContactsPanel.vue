<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";

import { api, type Contact, type ContactIn, type ContactsPage } from "../api/client";
import { CHANNELS, contactName, isoDay, ROLES, toFollowUp } from "../contactLabels";

// Contacts dans l'entreprise (docs/31) : recherches LinkedIn déjà remplies, ouvertes dans
// un nouvel onglet, et suivi des prises de contact. Rien n'est lu sur LinkedIn.
const props = withDefaults(
  defineProps<{ offerId?: number | null; applicationId?: number | null; company: string; bare?: boolean }>(),
  { offerId: null, applicationId: null, bare: false },
);
const emit = defineEmits<{ changed: [] }>();

const page = ref<ContactsPage | null>(null);
const failed = ref(false);
const adding = ref(false);
const busy = ref(false);
const answering = ref<number | null>(null);
const note = ref("");
const draft = reactive({ name: "", role: "recruiter" as Contact["role"], channel: "linkedin_invite" as Contact["channel"], contacted_on: isoDay() });
const shortDate = new Intl.DateTimeFormat("fr-CH", { day: "numeric", month: "short" });

function day(value: string): string {
  return shortDate.format(new Date(`${value}T12:00:00`));
}

async function load(): Promise<void> {
  failed.value = false;
  const result = props.applicationId
    ? await api.GET("/api/applications/{application_id}/contacts", {
      params: { path: { application_id: props.applicationId } },
    })
    : await api.GET("/api/offers/{offer_id}/contacts", { params: { path: { offer_id: props.offerId ?? 0 } } });
  page.value = result.data ?? null;
  failed.value = !result.data;
}

function onToggle(event: Event): void {
  if ((event.target as HTMLDetailsElement).open && !page.value) void load();
}

function body(contact: Contact, changes: Partial<ContactIn>): ContactIn {
  const { offer_id, application_id, name, role, channel, contacted_on, answered_on, note: text } = contact;
  return { offer_id, application_id, name, role, channel, contacted_on, answered_on, note: text, ...changes };
}

async function add(): Promise<void> {
  busy.value = true;
  try {
    const { data } = await api.POST("/api/contacts", {
      body: {
        offer_id: props.offerId,
        application_id: props.applicationId,
        name: draft.name || null,
        role: draft.role,
        channel: draft.channel,
        contacted_on: draft.contacted_on || isoDay(),
      },
    });
    if (!data) return;
    adding.value = false;
    draft.name = "";
    draft.contacted_on = isoDay();
    await load();
    emit("changed");
  } finally {
    busy.value = false;
  }
}

function startAnswer(contact: Contact): void {
  answering.value = contact.id;
  note.value = contact.note ?? "";
}

async function saveAnswer(contact: Contact): Promise<void> {
  busy.value = true;
  try {
    await api.PUT("/api/contacts/{contact_id}", {
      params: { path: { contact_id: contact.id } },
      body: body(contact, { answered_on: contact.answered_on ?? isoDay(), note: note.value || null }),
    });
    answering.value = null;
    await load();
    emit("changed");
  } finally {
    busy.value = false;
  }
}

async function remove(contact: Contact): Promise<void> {
  await api.DELETE("/api/contacts/{contact_id}", { params: { path: { contact_id: contact.id } } });
  await load();
  emit("changed");
}

onMounted(() => {
  if (props.bare) void load();
});
</script>

<template>
  <component
    :is="bare ? 'div' : 'details'"
    :class="['contacts-section', { 'company-section': !bare }]"
    data-test="contacts"
    @toggle="onToggle"
  >
    <summary v-if="!bare">
      Contacts chez {{ company }}
    </summary>
    <p
      v-if="failed"
      class="notice error"
    >
      Impossible de charger les contacts.
    </p>
    <template v-else-if="page">
      <p class="hint">
        Trouver quelqu'un : recherches LinkedIn déjà remplies, ouvertes dans un nouvel onglet.
      </p>
      <p class="contacts-searches">
        <a
          v-for="search in page.searches"
          :key="search.kind"
          class="link"
          :href="search.url"
          target="_blank"
          rel="noopener noreferrer"
          data-test="contact-search"
        >{{ search.label }}</a>
        <a
          v-if="page.website"
          class="link"
          :href="page.website"
          target="_blank"
          rel="noopener noreferrer"
          data-test="contact-website"
        >Site de l'employeur</a>
      </p>

      <ul
        v-if="page.contacts.length"
        class="contacts-list"
      >
        <li
          v-for="contact in page.contacts"
          :key="contact.id"
          data-test="contact"
        >
          <span>
            <strong>{{ contact.name || ROLES[contact.role] }}</strong>
            <span class="muted">
              {{ contact.name ? `${ROLES[contact.role]} · ` : "" }}{{ CHANNELS[contact.channel] }} le {{ day(contact.contacted_on) }}
            </span>
          </span>
          <span
            v-if="contact.answered_on"
            class="contact-state answered"
          >A répondu le {{ day(contact.answered_on) }}{{ contact.note ? ` : ${contact.note}` : "" }}</span>
          <span
            v-else-if="toFollowUp(contact)"
            class="contact-state due"
            data-test="contact-due"
          >Sans réponse : relancer {{ contactName(contact) }} ?</span>
          <span
            v-else
            class="contact-state muted"
          >En attente de réponse</span>
          <span class="contact-actions">
            <button
              type="button"
              class="link"
              data-test="contact-answered"
              @click="startAnswer(contact)"
            >
              {{ contact.answered_on ? "Modifier la note" : "A répondu" }}
            </button>
            <button
              type="button"
              class="link danger"
              @click="remove(contact)"
            >
              Retirer
            </button>
          </span>
          <form
            v-if="answering === contact.id"
            class="contact-form"
            @submit.prevent="saveAnswer(contact)"
          >
            <label>
              Note (facultative)
              <input
                v-model="note"
                maxlength="1000"
                placeholder="Ce qui a été dit, la suite"
                data-test="contact-note"
              >
            </label>
            <div>
              <button
                type="submit"
                class="secondary small"
                :disabled="busy"
                data-test="contact-save-answer"
              >
                Enregistrer
              </button>
              <button
                type="button"
                class="link"
                @click="answering = null"
              >
                Annuler
              </button>
            </div>
          </form>
        </li>
      </ul>

      <button
        v-if="!adding"
        type="button"
        class="link"
        data-test="contact-add"
        @click="adding = true"
      >
        J'ai contacté quelqu'un
      </button>
      <form
        v-else
        class="contact-form"
        data-test="contact-form"
        @submit.prevent="add"
      >
        <label>
          Nom (facultatif)
          <input
            v-model="draft.name"
            maxlength="120"
            autocomplete="off"
            data-test="contact-name"
          >
        </label>
        <label>
          Rôle
          <select v-model="draft.role">
            <option
              v-for="(text, value) in ROLES"
              :key="value"
              :value="value"
            >{{ text }}</option>
          </select>
        </label>
        <label>
          Canal
          <select v-model="draft.channel">
            <option
              v-for="(text, value) in CHANNELS"
              :key="value"
              :value="value"
            >{{ text }}</option>
          </select>
        </label>
        <label>
          Date
          <input
            v-model="draft.contacted_on"
            type="date"
            :max="isoDay()"
          >
        </label>
        <div>
          <button
            type="submit"
            class="secondary small"
            :disabled="busy"
            data-test="contact-save"
          >
            Enregistrer
          </button>
          <button
            type="button"
            class="link"
            @click="adding = false"
          >
            Annuler
          </button>
        </div>
      </form>
      <p class="hint">
        Une prise de contact ne compte pas pour l'ORP ; un rappel arrive dans la cloche après 7 jours sans réponse.
      </p>
    </template>
  </component>
</template>
