<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";

import { api, type Contact, type ContactIn, type ContactsPage } from "../api/client";
import { CHANNELS, contactName, isoDay, ROLES, toFollowUp } from "../contactLabels";
import { dateInSentence } from "../dates";
import AppIcon from "./AppIcon.vue";
import BusyButton from "./BusyButton.vue";
import CopyButton from "./CopyButton.vue";
import MoreMenu, { type MoreMenuItem } from "./MoreMenu.vue";
import HoverNote from "./HoverNote.vue";
import { offerUndo } from "../composables/useUndo";
import { usePlan } from "../composables/usePlan";

const { aiNote } = usePlan();

// Contacts dans l'entreprise (docs/31) : recherches LinkedIn déjà remplies, ouvertes dans
// un nouvel onglet, et suivi des prises de contact. Rien n'est lu sur LinkedIn. Affiché dans
// le panneau latéral (docs/32 §2.2) .
const props = withDefaults(defineProps<{ offerId?: number | null; applicationId?: number | null }>(), {
  offerId: null,
  applicationId: null,
});
const emit = defineEmits<{ changed: []; count: [count: number] }>();

const page = ref<ContactsPage | null>(null);
const failed = ref(false);
// Ajout ou retrait refusé, ou API injoignable : dit dans le panneau plutôt que rien ne bouge.
const actionError = ref("");
const adding = ref(false);
const busy = ref(false);
const answering = ref<number | null>(null);
const note = ref("");
const draft = reactive({ name: "", role: "recruiter" as Contact["role"], channel: "linkedin_invite" as Contact["channel"], contacted_on: isoDay() });
// Premier message rédigé par l'IA (docs/31 §3) : jamais de nom envoyé.
type MessageChannel = "linkedin_invite" | "linkedin_message" | "email";
const MESSAGE_CHANNELS: Record<MessageChannel, string> = {
  linkedin_invite: "Invitation LinkedIn",
  linkedin_message: "Message LinkedIn",
  email: "E-mail",
};
const writing = ref(false);
const writer = reactive({ role: "recruiter" as Contact["role"], channel: "linkedin_invite" as MessageChannel });
const written = ref("");
const limit = ref<number | null>(null);
const writeError = ref("");

async function write(): Promise<void> {
  if (writing.value) return;
  writing.value = true;
  writeError.value = "";
  try {
    const { data, error } = await api.POST("/api/contacts/message", {
      body: { offer_id: props.offerId, application_id: props.applicationId, ...writer },
    });
    if (!data) {
      const detail = (error as { detail?: unknown } | undefined)?.detail;
      writeError.value = typeof detail === "string" ? `Rédaction impossible : ${detail}.` : "Rédaction impossible.";
      return;
    }
    written.value = data.text;
    limit.value = data.limit ?? null;
    // « J'ai contacté quelqu'un » reprend le rôle et le canal du message.
    draft.role = writer.role;
    draft.channel = writer.channel;
  } finally {
    writing.value = false;
  }
}

// « le 12 octobre » : la date de phrase (dates.ts), avec son « le ».
function day(value: string): string {
  return dateInSentence(`${value}T12:00:00`);
}

async function load(): Promise<void> {
  failed.value = false;
  try {
    const result = props.applicationId
      ? await api.GET("/api/applications/{application_id}/contacts", {
        params: { path: { application_id: props.applicationId } },
      })
      : await api.GET("/api/offers/{offer_id}/contacts", { params: { path: { offer_id: props.offerId ?? 0 } } });
    page.value = result.data ?? null;
    failed.value = !result.data;
    if (result.data) emit("count", result.data.contacts.length);
  } catch {
    // API injoignable (réseau) : même message qu'une réponse en erreur.
    page.value = null;
    failed.value = true;
  }
}

function body(contact: Contact, changes: Partial<ContactIn>): ContactIn {
  const { offer_id, application_id, name, role, channel, contacted_on, answered_on, note: text } = contact;
  return { offer_id, application_id, name, role, channel, contacted_on, answered_on, note: text, ...changes };
}

async function add(): Promise<void> {
  if (busy.value) return;
  busy.value = true;
  actionError.value = "";
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
    if (!data) {
      actionError.value = "Enregistrement impossible : réessaie dans un instant.";
      return;
    }
    adding.value = false;
    draft.name = "";
    draft.contacted_on = isoDay();
    await load();
    emit("changed");
  } catch {
    actionError.value = "Enregistrement impossible : réessaie dans un instant.";
  } finally {
    busy.value = false;
  }
}

// « A répondu » visible tant qu'il n'a pas répondu ; le reste dans « ⋯ » (docs/74).
function contactItems(contact: Contact): MoreMenuItem[] {
  return [
    ...(contact.answered_on
      ? [{ label: "Modifier la note", test: "contact-answered", icon: "pencil" as const, run: () => startAnswer(contact) }]
      : []),
    { label: "Retirer", test: "contact-remove", icon: "trash", danger: true, run: () => void remove(contact) },
  ];
}

function startAnswer(contact: Contact): void {
  answering.value = contact.id;
  note.value = contact.note ?? "";
}

async function saveAnswer(contact: Contact): Promise<void> {
  if (busy.value) return;
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

// Retiré tout de suite, « Annuler » pendant 6 s (docs/108 §1).
async function remove(contact: Contact): Promise<void> {
  actionError.value = "";
  const before = page.value;
  if (before) page.value = { ...before, contacts: before.contacts.filter((c) => c.id !== contact.id) };
  await offerUndo({
    message: `${contact.name} retiré des contacts`,
    commit: async (keepalive) => {
      const { error } = await api.DELETE("/api/contacts/{contact_id}", { params: { path: { contact_id: contact.id } }, keepalive });
      if (error !== undefined) {
        actionError.value = "Retrait impossible : réessaie dans un instant.";
        return false;
      }
      await load();
      emit("changed");
    },
    restore: () => {
      page.value = before;
    },
  });
}

onMounted(() => void load());
</script>

<template>
  <div
    class="contacts-section"
    data-test="contacts"
  >
    <p
      v-if="failed"
      class="notice error"
      role="alert"
      data-test="contacts-error"
    >
      Impossible de charger les contacts.
    </p>
    <template v-else-if="page">
      <section class="contacts-block">
        <h3>Trouver quelqu'un</h3>
        <ul class="contacts-searches">
          <li
            v-for="search in page.searches"
            :key="search.kind"
          >
            <a
              class="link"
              :href="search.url"
              target="_blank"
              rel="noopener noreferrer"
              data-test="contact-search"
            ><span class="with-icon">{{ search.label }}<AppIcon name="external" /><span class="visually-hidden"> (nouvel onglet)</span></span></a>
          </li>
          <li v-if="page.website">
            <a
              class="link"
              :href="page.website"
              target="_blank"
              rel="noopener noreferrer"
              data-test="contact-website"
            ><span class="with-icon">Site de l'employeur<AppIcon name="external" /><span class="visually-hidden"> (nouvel onglet)</span></span></a>
          </li>
        </ul>
      </section>

      <section
        class="contacts-block contact-writer"
        data-test="contact-writer"
      >
        <h3>Premier message</h3>
        <form
          class="contact-writer-form"
          @submit.prevent="write"
        >
          <label>
            Écrire à
            <select v-model="writer.role">
              <option
                v-for="(text, value) in ROLES"
                :key="value"
                :value="value"
              >{{ text }}</option>
            </select>
          </label>
          <label>
            Canal
            <select v-model="writer.channel">
              <option
                v-for="(text, value) in MESSAGE_CHANNELS"
                :key="value"
                :value="value"
              >{{ text }}</option>
            </select>
          </label>
          <div class="contact-writer-actions">
            <BusyButton
              type="submit"
              class="secondary small"
              :busy="writing"
              busy-label="Rédaction…"
              data-test="contact-write"
            >
              <HoverNote :text="writing ? '' : aiNote('Environ 0,002 $.')">
                <span class="with-icon"><AppIcon name="ai" />{{ written ? "Rédiger à nouveau" : "Rédiger un message" }}</span>
              </HoverNote>
            </BusyButton>
          </div>
        </form>
        <p
          v-if="writeError"
          class="notice error"
          role="alert"
        >
          {{ writeError }}
        </p>
        <template v-if="written">
          <textarea
            v-model="written"
            rows="5"
            aria-label="Message à envoyer"
            data-test="contact-message"
          />
          <p class="contact-message-foot">
            <span
              v-if="limit"
              :class="['hint', { 'over-limit': written.length > limit }]"
              data-test="contact-count"
            >{{ written.length }} / {{ limit }} caractères{{ written.length > limit ? " : trop long pour une invitation" : "" }}</span>
            <CopyButton
              :value="written"
              label="Copier le message"
              test-id="contact-copy"
            />
          </p>
        </template>
      </section>

      <section class="contacts-block">
        <h3>Prises de contact</h3>
        <p
          v-if="actionError"
          class="notice error"
          role="alert"
          data-test="contact-error"
        >
          {{ actionError }}
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
                {{ contact.name ? `${ROLES[contact.role]} · ` : "" }}{{ CHANNELS[contact.channel] }} {{ day(contact.contacted_on) }}
              </span>
            </span>
            <span
              v-if="contact.answered_on"
              class="contact-state answered"
            >A répondu {{ day(contact.answered_on) }}{{ contact.note ? ` : ${contact.note}` : "" }}</span>
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
                v-if="!contact.answered_on"
                type="button"
                class="link"
                data-test="contact-answered"
                @click="startAnswer(contact)"
              >
                A répondu
              </button>
              <MoreMenu
                :items="contactItems(contact)"
                :label="`Plus d'actions sur le contact ${contactName(contact)}`"
                test-id="contact-more"
              />
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
                <BusyButton
                  type="submit"
                  class="secondary small"
                  :busy="busy"
                  busy-label="Enregistrement…"
                  data-test="contact-save-answer"
                >
                  Enregistrer
                </BusyButton>
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

        <p
          v-if="!page.contacts.length && !adding"
          class="muted contacts-empty"
        >
          Aucun contact pour l'instant.
        </p>
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
          class="contact-writer-form"
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
          <div class="contact-writer-actions">
            <BusyButton
              type="submit"
              class="secondary small"
              :busy="busy"
              busy-label="Enregistrement…"
              data-test="contact-save"
            >
              Enregistrer
            </BusyButton>
            <button
              type="button"
              class="link"
              @click="adding = false"
            >
              Annuler
            </button>
          </div>
        </form>
      </section>
    </template>
  </div>
</template>
