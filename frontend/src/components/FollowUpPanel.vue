<script setup lang="ts">
import { computed, ref } from "vue";

import { api, type Application } from "../api/client";
import { dateInList } from "../dates";
import AppIcon from "./AppIcon.vue";
import CopyLabel from "./CopyLabel.vue";
import HoverNote from "./HoverNote.vue";
import { usePlan } from "../composables/usePlan";

const { aiNote } = usePlan();

// Relancer une candidature (docs/38) : un court message (IA ou modèle simple), à copier ou à
// ouvrir dans ta messagerie ; rien n'est envoyé par la plateforme. Puis « Marquer comme relancée ».
const props = defineProps<{ application: Application }>();
const emit = defineEmits<{ done: [] }>();

const subject = ref("");
const text = ref("");
const reason = ref<string | null>(null);
const writing = ref(false);
const saving = ref(false);
const copied = ref(false);
const error = ref("");

// Ouvre la messagerie avec destinataire, objet et texte (rien n'est envoyé d'office).
const mailto = computed(() => {
  const to = props.application.contact_email;
  if (!to || !text.value) return null;
  const query = new URLSearchParams({ subject: subject.value, body: text.value }).toString().replace(/\+/g, "%20");
  return `mailto:${encodeURIComponent(to)}?${query}`;
});

async function write(): Promise<void> {
  writing.value = true;
  error.value = "";
  try {
    const { data } = await api.POST("/api/applications/{application_id}/follow-up/draft", {
      params: { path: { application_id: props.application.id } },
    });
    if (!data) {
      error.value = "Rédaction impossible pour l'instant.";
      return;
    }
    subject.value = data.subject;
    text.value = data.text;
    reason.value = data.ai ? null : data.reason;
  } finally {
    writing.value = false;
  }
}

async function copy(): Promise<void> {
  try {
    await navigator.clipboard.writeText(`${subject.value}\n\n${text.value}`);
    copied.value = true;
    setTimeout(() => (copied.value = false), 1500);
  } catch {
    copied.value = false;
  }
}

async function markDone(): Promise<void> {
  saving.value = true;
  try {
    const { data } = await api.POST("/api/applications/{application_id}/follow-up", {
      params: { path: { application_id: props.application.id } },
    });
    if (!data) {
      error.value = "Enregistrement impossible.";
      return;
    }
    emit("done");
  } finally {
    saving.value = false;
  }
}
</script>

<template>
  <div
    class="follow-up-panel"
    data-test="follow-up"
  >
    <p class="muted meta-line">
      <span>{{ application.job_title }}</span>
      <span><AppIcon name="send" /><span class="visually-hidden">envoyée le </span>{{ dateInList(`${application.sent_at}T12:00:00`) }}</span>
    </p>
    <button
      v-if="!text"
      type="button"
      class="secondary small"
      :disabled="writing"
      data-test="follow-up-write"
      @click="write"
    >
      <HoverNote :text="writing ? '' : aiNote('Environ 0,002 $.')">
        <span class="with-icon"><AppIcon name="ai" />{{ writing ? "Rédaction…" : "Rédiger la relance" }}</span>
      </HoverNote>
    </button>
    <template v-else>
      <p
        v-if="reason"
        class="hint"
        data-test="follow-up-template"
      >
        Modèle simple, sans IA ({{ reason }}).
      </p>
      <label class="follow-up-field">Objet
        <input
          v-model="subject"
          data-test="follow-up-subject"
        >
      </label>
      <label class="follow-up-field">Message
        <textarea
          v-model="text"
          rows="9"
          data-test="follow-up-text"
        />
      </label>
      <div class="follow-up-actions">
        <a
          v-if="mailto"
          class="button-link"
          :href="mailto"
          data-test="follow-up-mail"
        ><span class="with-icon"><AppIcon name="mail" />Ouvrir dans ma messagerie</span></a>
        <button
          type="button"
          class="link"
          data-test="follow-up-copy"
          @click="copy"
        >
          <CopyLabel :done="copied" />
        </button>
      </div>
    </template>
    <p
      v-if="error"
      class="notice error"
      role="alert"
    >
      {{ error }}
    </p>
    <button
      type="button"
      class="primary small"
      :disabled="saving"
      data-test="follow-up-done"
      @click="markDone"
    >
      Marquer comme relancée
    </button>
  </div>
</template>
